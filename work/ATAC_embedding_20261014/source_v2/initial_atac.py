#!/usr/bin/env python3
"""Initial full-study ATAC LSI/clusters/UMAP for marker and doublet diagnostics.

Raw peak counts and all initial-QC cells, including unassigned annotations, remain
in the output. This explicit initial-atlas entry accepts pending fresh doublet
review without relaxing the original filtered/final analysis guard.
"""
import argparse
import gc
import importlib.metadata
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy import sparse

from core import require_counts, sparse_tfidf, validate_obs, validate_technical_batch
from legacy_analyze import open_counts, add_qc, qc_report
from harmony_adapter import integrate, raw_csr_digest

GENOME = "GRCm38/mm10"
POLICY = "all observed mapped barcodes with validated LIG10 and donor-linked N5+N7; published whitelist is calibration only"
ROLE = "initial_ATAC_diagnostic_for_iterative_doublet_and_marker_review"
PLAN = {
    "status": "pending_fresh_ATAC_iterative_review",
    "source_method_review": "outputs/p5_workflow/full_study_20261008_r2/original_article_qc_review.md",
    "article_methods": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10703679/#Sec10",
    "paper_method": "Iterative clustering identifies potential ATAC doublet cells and doublet-derived subclusters",
    "numeric_doublet_cutoff_specified_by_article": False,
    "automatic_doublet_calls_or_removal_by_this_entry": False,
    "published_retained_cell_selection_inherited": False,
    "next_steps": [
        "Review initial clusters by library, animal, condition and coverage/TSS/FRiP/nucleosome metrics; technical concentration or unusual depth is a review cue, not a doublet call",
        "Review independent lineage-marker accessibility using matched gene activity and RNA marker annotations; published calibration labels are reference evidence, not final annotation",
        "Subcluster major lineages and candidate mixed-lineage clusters, retaining ambiguous and newly identified states; record cluster parameters and marker/accessibility evidence at each iteration",
        "Save any chemistry-specific doublet score with its algorithm, fitting partition and assumptions; the source provides no universal numeric threshold",
        "Record reviewed cell/subcluster decisions, reasons and before/after animal-by-library retention; remove cells only under that explicit reviewed policy",
        "Refine common peaks after fresh labels, recount/reevaluate FRiP as required, and rerun the retained-cell graph before final annotation or condition inference"
    ],
    "external_TrackerSci_reference_integration": False,
    "biological_replicate": "animal; RNA and ATAC nuclei are not one-to-one paired"
}


def exact_bool(value, expected):
    return isinstance(value, (bool, np.bool_)) and bool(value) is expected


def validate_initial_atac(a):
    """Validate this narrow initial path, leaving legacy final guard unchanged."""
    validate_obs(a.obs)
    if (a.uns.get("genome") != GENOME or a.uns.get("analysis_role") != "primary_mm10_raw_reprocessing" or
            a.uns.get("analysis_scope") != "complete_study" or a.uns.get("feature_space") != "peak"):
        raise ValueError("Initial ATAC entry requires a complete-study fresh mm10 raw peak matrix")
    if a.uns.get("cell_selection_provenance") != POLICY:
        raise ValueError("Initial ATAC entry requires all-candidate cell selection, not a published whitelist")
    if not exact_bool(a.uns.get("cell_selection_final"), False):
        raise ValueError("Initial matrix must explicitly declare pending final cell selection")
    if a.uns.get("peak_universe_role") != "provisional_common_peaks_for_initial_matrix_and_FRiP":
        raise ValueError("Initial peak/FRiP provenance is missing")
    evidence = a.uns.get("applied_qc")
    if isinstance(evidence, str): evidence = json.loads(evidence)
    if not isinstance(evidence, dict): raise ValueError("Structured initial applied_qc provenance is required")
    if (evidence.get("assay") != "atac" or evidence.get("genome") != GENOME or evidence.get("scope") != "complete_study" or
            not exact_bool(evidence.get("basic_qc_applied"), True) or
            not exact_bool(evidence.get("source_basic_qc_applied"), False) or
            not exact_bool(evidence.get("finalized"), False) or
            not exact_bool(evidence.get("doublet_filter_applied"), False) or
            not exact_bool(evidence.get("doublet_selection_inherited"), False)):
        raise ValueError("Initial ATAC provenance must declare fresh basic QC and pending uninherited doublet review")
    if (evidence.get("retained_cells") != a.n_obs or type(evidence.get("input_cells")) is not int or
            evidence["input_cells"] < a.n_obs or not str(evidence.get("method", "")).strip()):
        raise ValueError("Initial applied_qc counts/method do not reconcile")
    if a.obs.animal_id.nunique() != 20:
        raise ValueError("Full-study initial ATAC graph requires all20 verified animals")
    if "donor_id" not in a.obs or not a.obs.donor_id.astype(str).equals(a.obs.animal_id.astype(str)):
        raise ValueError("Initial ATAC donor/animal identities must agree")
    for field in ("fresh_mm10_qc_initial", "fresh_mm10_qc_pass", "unique_fragments", "tss_enrichment", "frip", "candidate_source"):
        if field not in a.obs: raise ValueError("Initial ATAC QC requires obs." + field)
    for field in ("fresh_mm10_qc_initial", "fresh_mm10_qc_pass"):
        if not a.obs[field].map(lambda x: exact_bool(x, True)).all():
            raise ValueError("Initial matrix contains unresolved/failed initial fragment/TSS flags")
    if not a.obs.candidate_source.eq("all_observed_validated_barcodes").all():
        raise ValueError("Candidate source policy differs")
    fragments = pd.to_numeric(a.obs.unique_fragments, errors="raise").to_numpy()
    tss = pd.to_numeric(a.obs.tss_enrichment, errors="raise").to_numpy()
    frip = pd.to_numeric(a.obs.frip, errors="raise").to_numpy()
    if not np.isfinite(fragments).all() or (fragments < 1500).any() or not np.array_equal(fragments, np.rint(fragments)):
        raise ValueError("Initial ATAC candidates must have >=1500 integer unique fragments")
    if not np.isfinite(tss).all() or (tss < 2).any():
        raise ValueError("Initial ATAC candidates must have finite TSS enrichment >=2")
    if not np.isfinite(frip).all() or ((frip < 0) | (frip > 1)).any():
        raise ValueError("Provisional FRiP must lie in [0,1]; it is diagnostic, not a selection threshold")
    return evidence


def technical_overlap(obs, output, batch_key=None, batch_provenance=None):
    """Always save coverage tables; require identifiability before correction."""
    output.mkdir(parents=True, exist_ok=True)
    report = {"correction_requested": bool(batch_key), "batch_key": batch_key, "batch_provenance": batch_provenance,
              "n_libraries": int(obs.library_id.nunique()), "n_animals": int(obs.animal_id.nunique()),
              "n_conditions": int(obs.condition.nunique())}
    for field in ("animal_id", "condition"):
        table = pd.crosstab(obs.library_id, obs[field])
        table.to_csv(output / ("library_by_" + field + ".tsv"), sep="\t")
        report["libraries_per_" + field] = {str(k): int(v) for k, v in table.gt(0).sum().items()}
        report[field + "_per_library"] = {str(k): int(v) for k, v in table.gt(0).sum(axis=1).items()}
    if batch_key:
        if not batch_provenance or not batch_provenance.strip():
            raise ValueError("Technical correction requires --batch-provenance")
        condition_table = validate_technical_batch(obs, batch_key)
        animal_table = pd.crosstab(obs[batch_key], obs.animal_id)
        condition_table.to_csv(output / "correction_batch_by_condition.tsv", sep="\t")
        animal_table.to_csv(output / "correction_batch_by_animal.tsv", sep="\t")
        if (animal_table.gt(0).sum() < 2).any() or (animal_table.gt(0).sum(axis=1) < 2).any():
            raise ValueError("Technical batch is confounded with animal identity; each animal and each batch must overlap >=2 counterpart groups")
        seen = set()
        frontier = {animal_table.columns[0]}
        while frontier:
            seen.update(frontier)
            batches = animal_table.index[animal_table[list(frontier)].gt(0).any(axis=1)]
            connected = set(animal_table.columns[animal_table.loc[batches].gt(0).any(axis=0)])
            frontier = connected - seen
        if len(seen) != len(animal_table.columns):
            raise ValueError("Technical batch/animal design is disconnected; correction effects cannot be separated across biological blocks")
        report["connected_batch_animal_design"] = True
        report["correction_overlap_check"] = "Passed connected multi-library animal/condition overlap; correction is for diagnostic embedding only"
    else:
        report["correction_overlap_check"] = "No correction requested; uncorrected LSI is retained"
    (output / "technical_overlap.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def lsi_feature_mask(x, min_feature_cells, n_components):
    detected = np.asarray((x > 0).sum(axis=0)).ravel()
    keep = (detected >= min_feature_cells) & (detected / x.shape[0] < .99)
    if min(x.shape[0], int(keep.sum())) <= n_components + 1:
        raise ValueError("Too few cells or informative peak features for the requested LSI components")
    return keep


def review_summary(obs, output):
    rows = []
    for cluster, group in obs.groupby("initial_cluster", observed=True, sort=True):
        row = {"initial_cluster": str(cluster), "n_cells": len(group), "n_animals": group.animal_id.nunique(),
               "n_libraries": group.library_id.nunique(), "n_conditions": group.condition.nunique(),
               "doublet_or_subcluster_decision": "pending_review", "final_cell_selection": False}
        if "published_cell_type" in group:
            unknown = group.published_cell_type.astype("string").fillna("UNASSIGNED").str.lower().isin(["unknown", "ambiguous", "unassigned", "mixed", "nan"])
            row["n_unassigned_calibration_labels"] = int(unknown.sum())
        for field in ("unique_fragments", "tss_enrichment", "frip", "nucleosome_signal", "qc_total_counts", "qc_detected_features"):
            if field in group:
                values = pd.to_numeric(group[field], errors="raise")
                row[field + "_median"] = float(values.median())
                row[field + "_q95"] = float(values.quantile(.95))
        rows.append(row)
    pd.DataFrame(rows).to_csv(output / "initial_cluster_review_summary.tsv", sep="\t", index=False)


def embed_initial(a, args):
    import anndata as ad
    import scanpy as sc
    from sklearn.decomposition import TruncatedSVD

    raw_x = a.X
    raw_digest_before = raw_csr_digest(raw_x)
    original_shape = a.shape
    original_ids = a.obs_names.copy()
    technical_overlap(a.obs, args.output, args.batch_key, args.batch_provenance)
    keep = lsi_feature_mask(a.X, args.min_feature_cells, args.n_components)
    # Same sparse TF-IDF/SVD algorithm as existing analyze.py. Only the working
    # representation is normalized; no raw count/initial-QC cell subset is made.
    tfidf = sparse_tfidf(a.X[:, keep])
    a.obs["zero_informative_peak_counts"] = np.diff(tfidf.indptr) == 0
    svd = TruncatedSVD(n_components=args.n_components + 1, random_state=args.seed)
    lsi = svd.fit_transform(tfidf).astype(np.float32)
    del tfidf
    gc.collect()
    depth = np.log1p(a.obs.qc_total_counts.to_numpy())
    correlations = [float(np.corrcoef(depth, lsi[:, i])[0, 1]) if np.std(depth) and np.std(lsi[:, i]) else None for i in range(lsi.shape[1])]
    a.uns["lsi_depth_correlation"] = json.dumps(correlations)
    a.uns["lsi_first_component_excluded"] = True
    a.uns["lsi_explained_variance_ratio"] = svd.explained_variance_ratio_.astype(float)
    e = ad.AnnData(sparse.csr_matrix((a.n_obs, 1), dtype=np.float32), obs=a.obs.copy())
    e.obsm["X_lsi_all"] = lsi
    e.obsm["X_lsi"] = lsi[:, 1:]
    a.obsm["X_lsi_all"] = lsi
    a.obsm["X_lsi"] = e.obsm["X_lsi"]
    a.var["embedding_feature"] = keep
    basis = "X_lsi"
    if args.batch_key:
        harmony_provenance = integrate(e, args.batch_key, basis=basis, adjusted_basis="X_lsi_harmony", seed=args.seed, ncores=args.threads)
        basis = "X_lsi_harmony"
        a.obsm[basis] = e.obsm[basis]
        a.uns["batch_correction"] = json.dumps({"method": "Harmony", "column": args.batch_key, "provenance": args.batch_provenance,
                                                "use": "Initial diagnostic graph only; raw counts preserved",
                                                "same_LSI_baseline": "Uncorrected X_lsi is retained with exactly the same feature/components used for Harmony",
                                                "runtime_layout_provenance": harmony_provenance})
    else:
        a.uns["batch_correction"] = "None: initial uncorrected LSI diagnostic"
    if args.batch_key:
        sc.pp.neighbors(e, n_neighbors=args.n_neighbors, use_rep="X_lsi", random_state=args.seed)
        sc.tl.umap(e, min_dist=.3, random_state=args.seed)
        sc.tl.leiden(e, resolution=args.resolution, key_added="initial_cluster_uncorrected", random_state=args.seed)
        a.obsm["X_umap_initial_uncorrected"] = e.obsm["X_umap"].copy()
        a.obs["initial_cluster_uncorrected"] = e.obs.initial_cluster_uncorrected
        a.obsp["uncorrected_initial_connectivities"] = e.obsp["connectivities"].copy()
        a.obsp["uncorrected_initial_distances"] = e.obsp["distances"].copy()
        for field in ("condition", "animal_id", "library_id", "published_cell_type"):
            pd.crosstab(a.obs.initial_cluster_uncorrected, a.obs[field]).to_csv(args.output / ("uncorrected_initial_cluster_by_"+field+".tsv"), sep="\t")
        sc.settings.figdir = args.output
        sc.pl.umap(e, color=["initial_cluster_uncorrected", "condition"], show=False, save="_uncorrected_same_LSI_clusters_conditions.pdf")
    sc.pp.neighbors(e, n_neighbors=args.n_neighbors, use_rep=basis, random_state=args.seed)
    sc.tl.umap(e, min_dist=.3, random_state=args.seed)
    sc.tl.leiden(e, resolution=args.resolution, key_added="initial_cluster", random_state=args.seed)
    a.obsm["X_umap_initial"] = e.obsm["X_umap"]
    a.obs["initial_cluster"] = e.obs.initial_cluster
    a.obsp["initial_connectivities"] = e.obsp["connectivities"]
    a.obsp["initial_distances"] = e.obsp["distances"]
    neighbor_info = dict(e.uns["neighbors"])
    neighbor_info["connectivities_key"] = "initial_connectivities"
    neighbor_info["distances_key"] = "initial_distances"
    a.uns["initial_neighbors"] = neighbor_info
    a.uns["initial_umap"] = e.uns["umap"]
    a.uns["embedding_role"] = ROLE
    a.uns["initial_graph_diagnostic"] = True
    a.uns["final_doublet_selection"] = False
    a.uns["cell_selection_final"] = False
    a.uns["doublet_review_plan"] = json.dumps(PLAN)
    a.uns["downstream_method"] = "Initial sparse ATAC TF-IDF/LSI, Leiden/UMAP diagnostic; modern adaptation, not literal SnapATAC2 diffusion-map reproduction"
    a.uns["run_parameters"] = json.dumps(vars(args), default=str)
    a.uns["software_versions"] = json.dumps({name: importlib.metadata.version(name) for name in ("anndata", "scanpy", "numpy", "scipy", "pandas", "scikit-learn")})
    a.obs["doublet_review_status"] = "pending_iterative_ATAC_marker_subcluster_review"
    a.obs["final_doublet_selection"] = False
    a.obs["final_cell_selection"] = False
    if a.X is not raw_x or a.shape != original_shape or not a.obs_names.equals(original_ids):
        raise RuntimeError("Initial embedding changed raw matrix/cell membership")
    for field in ("condition", "animal_id", "library_id", "published_cell_type"):
        if field in a.obs:
            pd.crosstab(a.obs.initial_cluster, a.obs[field]).to_csv(args.output / ("initial_cluster_by_" + field + ".tsv"), sep="\t")
    review_summary(a.obs, args.output)
    (args.output / "doublet_review_plan.json").write_text(json.dumps(PLAN, indent=2) + "\n")
    sc.settings.figdir = args.output
    sc.pl.umap(e, color=["initial_cluster", "condition"], title=["Initial ATAC clusters: review diagnostic", "Condition: initial ATAC diagnostic"],
               show=False, save="_initial_diagnostic_clusters_conditions.pdf")
    sc.pl.umap(e, color=["animal_id", "library_id"], title=["Animal: initial ATAC diagnostic", "Library: initial ATAC diagnostic"],
               show=False, save="_initial_diagnostic_animals_libraries.pdf")
    if "published_cell_type" in e.obs:
        sc.pl.umap(e, color="published_cell_type", title="Published calibration labels: initial diagnostic", show=False,
                   save="_initial_diagnostic_calibration_labels.pdf")
    raw_digest_after = raw_csr_digest(a.X)
    if raw_digest_after != raw_digest_before:
        raise RuntimeError("Raw integer CSR changed during initial ATAC embedding")
    a.uns["raw_counts_producer_before_after_digest"] = raw_digest_before
    (args.output / "raw_preservation.json").write_text(json.dumps({"before":raw_digest_before,"after":raw_digest_after,"equal":True,"scope":"allocated producer in-memory integer CSR; source input H5 unchanged"},indent=2)+"\n")
    a.write_h5ad(args.output / "atac_initial_atlas.h5ad", compression="gzip")
    a.obs.to_csv(args.output / "initial_cell_metadata.tsv.gz", sep="\t", index_label="cell_id")
    (args.output / "initial_embedding_complete.json").write_text(json.dumps({
        "embedding_role": ROLE, "n_initial_cells": a.n_obs, "n_peaks": a.n_vars,
        "n_LSI_features": int(keep.sum()), "n_initial_clusters": int(a.obs.initial_cluster.nunique()),
        "n_animals": int(a.obs.animal_id.nunique()), "n_libraries": int(a.obs.library_id.nunique()),
        "input": args.input, "raw_counts_preserved": True, "all_initial_QC_cells_retained": True,
        "final_annotation_complete": False, "final_doublet_selection": False, "final_cell_selection": False,
        "provisional_peak_universe": True, "refined_peaks_pending": True
    }, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--initial-atlas", action="store_true", help="Explicitly accept pending fresh ATAC doublet/final selection for diagnostics")
    parser.add_argument("--memory-gb", required=True, type=float)
    parser.add_argument("--batch-key")
    parser.add_argument("--batch-provenance")
    parser.add_argument("--n-components", type=int, default=50)
    parser.add_argument("--min-feature-cells", type=int, default=10)
    parser.add_argument("--n-neighbors", type=int, default=30)
    parser.add_argument("--resolution", type=float, default=.6)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--threads", type=int, default=1, help="Allocated Harmony cores for the reviewed direct adapter")
    args = parser.parse_args()
    if not args.initial_atlas: raise ValueError("Use --initial-atlas to acknowledge initial diagnostic/pending doublet provenance")
    if args.n_components < 2 or args.min_feature_cells < 1 or args.n_neighbors < 2 or args.resolution <= 0 or args.threads < 1:
        raise ValueError("Invalid embedding parameters")
    if not np.isfinite(args.memory_gb) or args.memory_gb <= 0 or not np.isfinite(args.resolution):
        raise ValueError("Finite positive memory/resolution parameters are required")
    args.output.mkdir(parents=True, exist_ok=True)
    if (args.output / "atac_initial_atlas.h5ad").exists() or (args.output / "initial_embedding_complete.json").exists():
        raise FileExistsError("Initial atlas output exists; preserve it and select a new directory")
    a = open_counts(args.input, args.memory_gb)
    evidence = validate_initial_atac(a)
    add_qc(a, "atac")
    qc_report(a, args.output, "atac")
    a.uns["initial_QC_path"] = json.dumps({"applied_fresh_initial_QC": evidence, "final_doublet_selection": False,
                                          "observed_distribution_and_marker_review": "pending"})
    if a.n_obs < 100 or args.n_neighbors >= a.n_obs:
        raise ValueError("Too few initial cells or neighbors exceed initial cell count")
    embed_initial(a, args)


if __name__ == "__main__":
    try: main()
    except (ValueError, MemoryError, FileExistsError) as error:
        sys.exit("INITIAL ATAC INPUT/VALIDITY: " + str(error))
