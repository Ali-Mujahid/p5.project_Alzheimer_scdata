#!/usr/bin/env python3
"""Auditable post-count QC, sparse atlas clustering, and animal pseudobulk.

This is a modern scalable adaptation, not a literal reproduction of TrackerSci's
SnapATAC/densityPeak implementation. X remains raw counts in saved objects.
"""
import argparse
import gc
import importlib.metadata
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy import io, sparse
from core import require_counts, validate_obs, validate_technical_batch, qc_metrics, sparse_tfidf, aggregate_counts

def open_counts(path, memory_gb):
    import anndata as ad
    import h5py
    a = ad.read_h5ad(path, backed="r")
    try:
        with h5py.File(path,"r") as h:
            if "X/data" not in h: raise ValueError("Only sparse raw count h5ad inputs are supported")
            raw_gb = sum(h[f"X/{p}"].size * h[f"X/{p}"].dtype.itemsize for p in ["data", "indices", "indptr"]) / 1e9
        # Conservative allowance for copies/normalization/LSI and dense low-D arrays.
        estimate = 6 * raw_gb + 4 * a.n_obs * 80 / 1e9 + 4
    finally:
        a.file.close()
    if estimate > memory_gb:
        raise MemoryError(f"Estimated {estimate:.1f} GB for this stage exceeds --memory-gb {memory_gb}; use a larger allocation or an explicit biological subset.")
    a = ad.read_h5ad(path)
    a.X = require_counts(a.X)
    validate_obs(a.obs)
    if not a.var_names.is_unique: raise ValueError("Feature IDs must be unique; sum duplicate biological features explicitly")
    return a

def add_qc(a, assay):
    mt = None
    if assay == "rna":
        if "gene_symbol" not in a.var: raise ValueError("RNA var.gene_symbol required for mitochondrial fraction")
        mt = a.var.gene_symbol.fillna("").str.lower().str.startswith("mt-").to_numpy()
        if not mt.any(): raise ValueError("No mitochondrial gene symbols found; check genome/annotation instead of reporting a false zero")
    for field, values in qc_metrics(a.X, mt).items(): a.obs[f"qc_{field}"] = values

def qc_report(a, out, assay):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fields = [c for c in a.obs if c.startswith("qc_")]
    fields += [c for c in ["unique_fragments", "tss_enrichment", "frip", "blacklist_fraction", "original_total_reads", "original_peak_ratio", "original_UMI_count", "original_Gene_count"] if c in a.obs]
    meta_fields = [c for c in ["animal_id", "condition", "sex", "library_id", "technical_batch"] if c in a.obs]
    a.obs[meta_fields + fields].to_csv(out / "qc_cells.tsv.gz", sep="\t", index_label="cell_id")
    for by in ["library_id", "animal_id", "condition"]:
        summary = a.obs.groupby(by, observed=True)[fields].quantile([0, .01, .05, .5, .95, .99, 1])
        summary.to_csv(out / f"qc_quantiles_by_{by}.tsv", sep="\t")
    fig, axes = plt.subplots(1, min(len(fields), 4), figsize=(5*min(len(fields),4),4), squeeze=False)
    for ax, field in zip(axes.ravel(), fields[:4]):
        values = pd.to_numeric(a.obs[field], errors="raise").to_numpy()
        values = np.log10(1+values) if "counts" in field or "features" in field else values
        ax.hist(values[np.isfinite(values)], bins=100, rasterized=True)
        ax.set_xlabel(("log10(1+x) " if "counts" in field or "features" in field else "") + field)
        ax.set_ylabel("Nuclei")
    fig.tight_layout(); fig.savefig(out / "qc_overview.pdf"); plt.close(fig)

def apply_qc(a, policy_path, assay):
    cfg = json.loads(Path(policy_path).read_text())
    if cfg.get("finalized_after_observed_qc") is not True or not cfg.get("review_note", "").strip():
        raise ValueError("QC policy must be finalized after observed library/animal distributions and record review_note")
    p = cfg[assay]
    keep = np.ones(a.n_obs, dtype=bool)
    checks = {"min_detected_features": ("qc_detected_features", ">="), "min_total_counts": ("qc_total_counts", ">="),
              "max_total_counts": ("qc_total_counts", "<="), "max_pct_mt": ("qc_pct_mt", "<="),
              "min_unique_fragments": ("unique_fragments", ">="), "min_tss_enrichment": ("tss_enrichment", ">="),
              "min_frip": ("frip", ">="), "max_blacklist_fraction": ("blacklist_fraction", "<=")}
    for name, (column, op) in checks.items():
        if p.get(name) is None: continue
        if column not in a.obs: raise ValueError(f"QC policy needs obs.{column}; do not substitute published total_reads for unique fragments")
        v = pd.to_numeric(a.obs[column], errors="raise").to_numpy()
        flag = np.isfinite(v) & ((v >= p[name]) if op == ">=" else (v <= p[name]))
        a.obs[f"pass_{name}"] = flag; keep &= flag
    if p.get("exclude_doublets"):
        col = p.get("doublet_call_column", "doublet_call")
        if col not in a.obs: raise ValueError("QC requests doublet filtering but chemistry-calibrated calls are missing")
        flag = a.obs[col].eq(p.get("doublet_singlet_value", "singlet")).to_numpy()
        a.obs["pass_doublet"] = flag; keep &= flag
    a.obs["pass_final_qc"] = keep
    return keep, cfg

def validate_preprocessed_qc(a,assay):
    """Accept declared source-rule initial QC, never pretend it was observed-finalized."""
    if a.uns.get("genome")!="GRCm38/mm10" or a.uns.get("analysis_role")!="primary_mm10_raw_reprocessing" or a.uns.get("analysis_scope")!="complete_study":
        raise ValueError("--preprocessed-filtered requires complete-study fresh primary mm10 reprocessing")
    evidence=a.uns.get("applied_qc")
    if isinstance(evidence,str):evidence=json.loads(evidence)
    if not isinstance(evidence,dict):raise ValueError("Structured applied_qc provenance is required")
    if evidence.get("assay")!=assay or evidence.get("genome")!="GRCm38/mm10" or evidence.get("scope")!="complete_study":
        raise ValueError("Applied-QC assay/assembly/scope does not match this object")
    if evidence.get("source_basic_qc_applied") is not True or evidence.get("retained_cells")!=a.n_obs or not isinstance(evidence.get("input_cells"),int) or evidence["input_cells"]<a.n_obs:
        raise ValueError("Applied-QC counts or source basic filtering are invalid")
    if not str(evidence.get("method","")).strip():raise ValueError("QC method provenance is missing")
    if a.obs.animal_id.nunique()!=20:raise ValueError("Complete-study first embedding requires all 20 verified animal identities")
    if assay=="rna":
        if evidence.get("doublet_filter_applied") is not True or "pass_source_basic_qc" not in a.obs or not a.obs.pass_source_basic_qc.eq(True).all():
            raise ValueError("Fresh RNA basic QC/doublet filtering evidence is incomplete")
        if "predicted_doublet" not in a.obs or not a.obs.predicted_doublet.eq(False).all():raise ValueError("RNA object contains unresolved/positive doublet calls")
    else:
        if evidence.get("doublet_selection_inherited") is not True:raise ValueError("ATAC retained-source doublet-selection scope must be explicitly inherited")
        for field in ["fresh_mm10_qc_pass","unique_fragments","tss_enrichment","frip"]:
            if field not in a.obs:raise ValueError(f"Fresh ATAC QC needs obs.{field}")
        if not a.obs.fresh_mm10_qc_pass.eq(True).all():raise ValueError("ATAC object contains cells failing fresh mm10 QC")
    return evidence

def embed(a, args):
    import anndata as ad
    import scanpy as sc
    from sklearn.decomposition import TruncatedSVD
    if args.batch_key:
        if not args.batch_provenance:
            raise ValueError("--batch-provenance must explain the technical process being corrected")
        validate_technical_batch(a.obs, args.batch_key)
    detected = np.asarray((a.X > 0).sum(axis=0)).ravel()
    keep_features = detected >= args.min_feature_cells
    if args.assay == "atac": keep_features &= detected / a.n_obs < .99
    if keep_features.sum() <= args.n_components: raise ValueError("Too few informative features for embedding")
    if args.assay == "rna":
        e = ad.AnnData(a.X[:, keep_features].astype(np.float32), obs=a.obs.copy(), var=a.var.loc[keep_features].copy())
        sc.pp.normalize_total(e, target_sum=1e4)
        sc.pp.log1p(e)
        # Seurat flavor expects log expression, avoids an optional LOESS runtime.
        sc.pp.highly_variable_genes(e, flavor="seurat", n_top_genes=args.n_hvg, batch_key=args.batch_key)
        chosen = e.var_names[e.var.highly_variable]
        e = e[:, chosen].copy()
        sc.pp.scale(e, zero_center=False, max_value=10)
        sc.pp.pca(e, n_comps=args.n_components, zero_center=True, svd_solver="arpack", random_state=args.seed)
        basis = "X_pca"
        a.var["embedding_feature"] = a.var_names.isin(chosen)
    else:
        # Peak/bin counts are not gene expression. Never apply RNA HVG scaling.
        tfidf = sparse_tfidf(a.X[:, keep_features])
        svd = TruncatedSVD(n_components=args.n_components+1, random_state=args.seed)
        lsi = svd.fit_transform(tfidf).astype(np.float32)
        del tfidf; gc.collect()
        depth = np.log1p(a.obs.qc_total_counts.to_numpy())
        correlation = [float(np.corrcoef(depth, lsi[:, i])[0,1]) for i in range(lsi.shape[1])]
        a.uns["lsi_depth_correlation"] = correlation
        a.uns["lsi_first_component_excluded"] = True
        # LSI1 commonly follows coverage; retain its diagnostic and omit from graph.
        e = ad.AnnData(sparse.csr_matrix((a.n_obs, 1), dtype=np.float32), obs=a.obs.copy())
        e.obsm["X_lsi_all"] = lsi
        e.obsm["X_lsi"] = lsi[:, 1:]
        a.obsm["X_lsi_all"] = lsi
        basis = "X_lsi"
        a.var["embedding_feature"] = keep_features
    corrected = basis
    if args.batch_key:
        sc.external.pp.harmony_integrate(e, key=args.batch_key, basis=basis, adjusted_basis=basis+"_harmony", random_state=args.seed)
        corrected = basis + "_harmony"
        a.uns["batch_correction"] = json.dumps({"method":"Harmony", "column":args.batch_key, "provenance":args.batch_provenance})
    else:
        a.uns["batch_correction"] = "None: technical provenance/condition overlap must justify any correction"
    a.obsm[basis] = e.obsm[basis]
    if corrected != basis: a.obsm[corrected] = e.obsm[corrected]
    sc.pp.neighbors(e, n_neighbors=args.n_neighbors, use_rep=corrected, random_state=args.seed)
    sc.tl.umap(e, min_dist=.3, random_state=args.seed)
    sc.tl.leiden(e, resolution=args.resolution, key_added="cluster", random_state=args.seed)
    a.obsm["X_umap"] = e.obsm["X_umap"]
    a.obs["cluster"] = e.obs.cluster
    a.obsp["connectivities"] = e.obsp["connectivities"]
    a.obsp["distances"] = e.obsp["distances"]
    a.uns["neighbors"] = e.uns["neighbors"]
    a.uns["umap"] = e.uns["umap"]
    a.uns["downstream_method"] = "Sparse RNA HVG/PCA or ATAC TF-IDF/LSI, Leiden/UMAP: modern adaptation; original published annotations retained"
    a.uns["run_parameters"] = json.dumps(vars(args), default=str)
    a.uns["software_versions"] = json.dumps({p: importlib.metadata.version(p) for p in ["anndata","scanpy","numpy","scipy","pandas","scikit-learn"]})
    for by in ["condition", "animal_id", "library_id", "published_cell_type"]:
        if by in a.obs: pd.crosstab(a.obs.cluster, a.obs[by]).to_csv(args.output / f"cluster_by_{by}.tsv", sep="\t")
    e.obs["condition"] = a.obs.condition
    sc.settings.figdir = args.output
    sc.pl.umap(e, color=["cluster","condition"], show=False, save="_clusters_conditions.pdf")
    if "published_cell_type" in e.obs:
        sc.pl.umap(e, color="published_cell_type", legend_loc="on data", show=False, save="_published_annotation.pdf")
    a.write_h5ad(args.output / "atlas.h5ad", compression="gzip")
    a.obs.to_csv(args.output / "cell_metadata.tsv.gz", sep="\t", index_label="cell_id")
    if args.assay=="rna":
        from marker_report import marker_report
        marker_report(a,args.output/"marker_validation")

def pseudobulk(a, args):
    if not args.label_column: raise ValueError("--label-column must name reviewed or explicitly published annotations")
    if not args.label_provenance: raise ValueError("--label-provenance must document annotation source and marker review status")
    if args.feature_kind != "gene" and not args.library_size_column:
        raise ValueError("TE/ATAC pseudobulk requires a full-assay denominator in --library-size-column; TE-only/peak-only totals are invalid")
    if args.library_size_column:
        if args.library_size_column not in a.obs: raise ValueError("Full-assay library denominator missing")
        denom = pd.to_numeric(a.obs[args.library_size_column], errors="raise").to_numpy()
    else: denom = np.asarray(a.X.sum(axis=1)).ravel()
    x, obs, excluded = aggregate_counts(a.X, a.obs, args.label_column, denom, args.min_cells)
    if obs.empty: raise ValueError("No sufficiently represented animal/cell-type pseudobulks")
    io.mmwrite(args.output / "counts.mtx", x.T, field="integer")
    obs.to_csv(args.output / "samples.tsv", sep="\t", index=False)
    excluded.to_csv(args.output / "excluded_low_cell_pseudobulks.tsv", sep="\t", index=False)
    a.var.to_csv(args.output / "features.tsv", sep="\t", index_label="feature_id")
    (args.output / "provenance.json").write_text(json.dumps({"feature_kind":args.feature_kind, "label_column":args.label_column,
        "label_provenance":args.label_provenance, "library_size_column":args.library_size_column or "raw_gene_count_sum",
        "experimental_unit":"animal", "count_correction":"none", "batch_removal_used_for_tests":False,
        "genome":a.uns.get("genome","UNRESOLVED"), "analysis_role":a.uns.get("analysis_role","UNRESOLVED")}, indent=2))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=["qc", "cluster", "pseudobulk"])
    p.add_argument("--input", required=True); p.add_argument("--output", required=True, type=Path)
    p.add_argument("--assay", required=True, choices=["rna", "atac"])
    p.add_argument("--memory-gb", required=True, type=float)
    p.add_argument("--genome", choices=["GRCm38/mm10","GRCm39/mm39"])
    p.add_argument("--qc-policy"); p.add_argument("--published-filtered", action="store_true")
    p.add_argument("--preprocessed-filtered",action="store_true")
    p.add_argument("--batch-key"); p.add_argument("--batch-provenance")
    p.add_argument("--n-hvg", type=int, default=3000); p.add_argument("--n-components", type=int, default=50)
    p.add_argument("--min-feature-cells", type=int, default=10); p.add_argument("--n-neighbors", type=int, default=30)
    p.add_argument("--resolution", type=float, default=.6); p.add_argument("--seed", type=int, default=1729)
    p.add_argument("--label-column"); p.add_argument("--label-provenance")
    p.add_argument("--feature-kind", choices=["gene", "peak", "te_rna", "te_atac"], default="gene")
    p.add_argument("--library-size-column"); p.add_argument("--min-cells", type=int, default=30)
    args = p.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    if (args.output / "atlas.h5ad").exists(): raise FileExistsError("Output atlas exists; select a new run directory")
    a = open_counts(args.input, args.memory_gb)
    if args.genome and a.uns.get("genome") != args.genome:
        raise ValueError("Requested assembly differs from count provenance; relabeling a matrix is not realignment/recounting")
    if args.stage == "pseudobulk": pseudobulk(a, args); return
    add_qc(a, args.assay); qc_report(a, args.output, args.assay)
    if args.stage == "qc": return
    if sum([bool(args.qc_policy),args.published_filtered,args.preprocessed_filtered])!=1:
        raise ValueError("Choose exactly one QC path: finalized policy, published atlas, or verified primary preprocessing")
    if args.qc_policy:
        keep, policy = apply_qc(a, args.qc_policy, args.assay)
        a.obs.to_csv(args.output / "qc_flags_before_filter.tsv.gz", sep="\t", index_label="cell_id")
        a = a[keep].copy(); a.uns["qc_policy"] = json.dumps(policy)
    elif args.preprocessed_filtered:
        a.uns["qc_policy"] = json.dumps({"applied_source_initial_QC":validate_preprocessed_qc(a,args.assay),
            "secondary_observed_distribution_review":"pending; source cutoffs are declared initial rules"})
    elif args.published_filtered:
        if "Published filtered EasySci atlas" not in str(a.uns.get("cell_selection_provenance", "")):
            raise ValueError("--published-filtered requires converter-verified published filtered provenance")
        a.uns["qc_policy"] = "Published filtered EasySci atlas retained; observed secondary QC reported without additional automatic filtering"
    else: raise ValueError("QC provenance unresolved")
    if a.n_obs < 100: raise ValueError("Too few QC-passing cells for this atlas workflow")
    embed(a, args)

if __name__ == "__main__":
    try: main()
    except (ValueError, MemoryError, FileExistsError) as e:
        sys.exit(f"INPUT/VALIDITY GATE: {e}")
