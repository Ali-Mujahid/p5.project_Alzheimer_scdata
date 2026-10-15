#!/usr/bin/env python3
"""Focused initial-provenance, correction-overlap and raw-count tests."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from scipy import sparse

from core import sparse_tfidf
from initial_atac import (GENOME, POLICY, ROLE, PLAN, validate_initial_atac,
                          technical_overlap, lsi_feature_mask, review_summary, embed_initial)
from legacy_analyze import validate_preprocessed_qc
from harmony_adapter import checked_harmony

HERE = Path(__file__).resolve().parent


def observations(n=120):
    animals = np.arange(n) % 20
    conditions = np.array(["3mo", "6mo", "21mo", "5xFAD", "APOE4/TREM2"])[animals // 4]
    libraries = ["PCR" + str(i % 3) for i in range(n)]
    obs = pd.DataFrame({"animal_id": ["A" + str(i) for i in animals], "donor_id": ["A" + str(i) for i in animals], "condition": conditions,
                        "sex": np.where(animals % 4 < 2, "F", "M"),
                        "age_months": np.where(conditions == "6mo", 6, np.where(conditions == "21mo", 21, 3)),
                        "library_id": libraries, "technical_batch": libraries,
                        "fresh_mm10_qc_initial": True, "fresh_mm10_qc_pass": True,
                        "unique_fragments": 1500 + np.arange(n), "tss_enrichment": 2., "frip": 0.,
                        "candidate_source": "all_observed_validated_barcodes",
                        "published_cell_type": np.where(np.arange(n) % 2, "UNASSIGNED", "Astrocyte")},
                       index=pd.Index(["cell" + str(i) for i in range(n)], name="cell_id"))
    return obs


def input_object(n=120):
    evidence = {"assay": "atac", "genome": GENOME, "scope": "complete_study", "basic_qc_applied": True,
                "source_basic_qc_applied": False, "finalized": False, "doublet_filter_applied": False,
                "doublet_selection_inherited": False, "retained_cells": n, "input_cells": n + 100,
                "method": "Fresh all-candidate mm10 unique-fragment/TSS filtering; provisional FRiP diagnostic"}
    return SimpleNamespace(obs=observations(n), n_obs=n, uns={"genome": GENOME,
                           "analysis_role": "primary_mm10_raw_reprocessing", "analysis_scope": "complete_study",
                           "feature_space": "peak", "cell_selection_provenance": POLICY,
                           "cell_selection_final": False,
                           "peak_universe_role": "provisional_common_peaks_for_initial_matrix_and_FRiP",
                           "applied_qc": json.dumps(evidence)})


class InitialATACContracts(unittest.TestCase):
    def test_initial_guard_accepts_unknown_labels_and_zero_provisional_frip(self):
        a = input_object()
        self.assertFalse(validate_initial_atac(a)["doublet_selection_inherited"])
        self.assertEqual(int(a.obs.published_cell_type.eq("UNASSIGNED").sum()), 60)
        self.assertTrue(a.obs.frip.eq(0).all())

    def test_original_filtered_guard_still_refuses_pending_initial_doublets(self):
        with self.assertRaises(ValueError): validate_preprocessed_qc(input_object(), "atac")

    def test_initial_guard_never_relabels_activity_mm39_pilot_or_whitelist(self):
        for key, value in [("feature_space", "activity"), ("genome", "GRCm39/mm39"),
                           ("analysis_scope", "pilot"), ("cell_selection_provenance", "published whitelist"),
                           ("cell_selection_final", True)]:
            with self.subTest(key=key):
                a = input_object();a.uns[key] = value
                with self.assertRaises(ValueError):validate_initial_atac(a)

    def test_input_provenance_reconciles_counts_and_doublet_status(self):
        for key, value in [("doublet_filter_applied", True), ("doublet_selection_inherited", True),
                           ("finalized", True), ("retained_cells", 119), ("input_cells", 10),
                           ("source_basic_qc_applied", True), ("basic_qc_applied", False)]:
            with self.subTest(key=key):
                a = input_object();evidence = json.loads(a.uns["applied_qc"]);evidence[key] = value
                a.uns["applied_qc"] = json.dumps(evidence)
                with self.assertRaises(ValueError):validate_initial_atac(a)

    def test_flags_and_measured_source_thresholds_cannot_be_substituted(self):
        for field, value in [("fresh_mm10_qc_initial", False), ("fresh_mm10_qc_pass", False),
                             ("unique_fragments", 1499), ("unique_fragments", 1500.001),
                             ("tss_enrichment", 1.999), ("tss_enrichment", np.nan),
                             ("frip", 1.001), ("candidate_source", "published_whitelist")]:
            with self.subTest(field=field, value=value):
                a=input_object();a.obs[field]=a.obs[field].astype(object);a.obs.loc[a.obs.index[0],field]=value
                with self.assertRaises(ValueError):validate_initial_atac(a)

    def test_complete_scope_requires_all20_animals(self):
        a = input_object();a.obs = a.obs[a.obs.animal_id.ne("A19")].copy();a.n_obs = len(a.obs)
        evidence = json.loads(a.uns["applied_qc"]);evidence["retained_cells"] = a.n_obs;a.uns["applied_qc"] = json.dumps(evidence)
        with self.assertRaisesRegex(ValueError,"all20"):validate_initial_atac(a)

    def test_batch_overlap_is_reported_before_identifiable_correction(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            path = Path(directory)
            report = technical_overlap(observations(),path,"technical_batch","PCR pool processing")
            self.assertEqual(report["n_animals"],20);self.assertEqual(report["n_libraries"],3)
            self.assertTrue((path/"library_by_animal_id.tsv").exists())
            self.assertTrue((path/"correction_batch_by_condition.tsv").exists())

    def test_biological_or_condition_confounded_correction_is_refused(self):
        obs = observations()
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            with self.assertRaises(ValueError):technical_overlap(obs,Path(directory),"condition","unjustified")
            obs["bad_batch"] = obs.condition
            with self.assertRaises(ValueError):technical_overlap(obs,Path(directory),"bad_batch","condition confounded")
            with self.assertRaises(ValueError):technical_overlap(obs,Path(directory),"technical_batch","")

    def test_animal_confounded_correction_is_refused_even_with_condition_overlap(self):
        obs = observations();ids = obs.animal_id.str[1:].astype(int)
        obs["bad_batch"] = np.where(ids % 4 < 2,"batch1","batch2")
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            with self.assertRaisesRegex(ValueError,"confounded with animal"):
                technical_overlap(obs,Path(directory),"bad_batch","each animal occurs in one batch")

    def test_disconnected_design_is_refused_despite_local_overlap(self):
        obs=observations();animal_number=obs.animal_id.str[1:].astype(int)
        obs["bad_batch"]=[("left" if animal%2 else "right")+str((i//20)%2) for i,animal in enumerate(animal_number)]
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            with self.assertRaisesRegex(ValueError,"disconnected"):
                technical_overlap(obs,Path(directory),"bad_batch","two disconnected biological blocks")

    def test_direct_harmony_layout_bridge_preserves_baseline_and_rejects_mismatch(self):
        baseline=np.arange(120*3,dtype=np.float32).reshape(120,3);original=baseline.copy();obs=observations()
        corrected,proof=checked_harmony(baseline,obs,"technical_batch",version="2.0.0",run_harmony=lambda x,*args,**kwargs:SimpleNamespace(Z_corr=x+1),ncores=2)
        np.testing.assert_array_equal(baseline,original);np.testing.assert_array_equal(corrected,original+1)
        self.assertEqual(proof["stored_layout"],"cells_by_pcs")
        corrected,_=checked_harmony(baseline,obs,"technical_batch",version="0.0.10",run_harmony=lambda x,*args,**kwargs:SimpleNamespace(Z_corr=(x+1).T))
        np.testing.assert_array_equal(corrected,original+1)
        with self.assertRaisesRegex(ValueError,"layout"):
            checked_harmony(baseline,obs,"technical_batch",version="2.0.0",run_harmony=lambda x,*args,**kwargs:SimpleNamespace(Z_corr=x.T))
        with self.assertRaisesRegex(ValueError,"Unreviewed"):
            checked_harmony(baseline,obs,"technical_batch",version="unexpected",run_harmony=lambda x,*args,**kwargs:None)

    def test_uncorrected_path_reports_overlap_without_changing_cells(self):
        obs=observations();before=obs.copy(deep=True)
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            report=technical_overlap(obs,Path(directory))
            self.assertFalse(report["correction_requested"])
        pd.testing.assert_frame_equal(obs,before)

    def test_tfidf_preserves_integer_counts_and_zero_peak_cells(self):
        x=sparse.csr_matrix([[3,0,1],[0,0,0],[2,4,0]],dtype=np.int32);before=x.copy()
        result=sparse_tfidf(x)
        np.testing.assert_array_equal(x.toarray(),before.toarray())
        self.assertEqual(result.shape,x.shape);self.assertEqual(result[1].nnz,0)
        self.assertTrue(np.isfinite(result.data).all())

    def test_feature_selection_excludes_ubiquitous_peaks_not_cells(self):
        x=sparse.csr_matrix([[1,1,1,0,0,0],[1,0,1,1,0,0],[1,0,0,0,1,0],[1,1,0,0,0,1],[1,0,1,0,0,1]])
        keep=lsi_feature_mask(x,1,2)
        self.assertEqual(keep.tolist(),[False,True,True,True,True,True]);self.assertEqual(x.shape[0],5)
        with self.assertRaises(ValueError):lsi_feature_mask(x,4,2)

    def test_review_summary_has_no_fabricated_doublet_call_or_cutoff(self):
        obs=observations();obs["initial_cluster"]=np.where(np.arange(len(obs))%2,"0","1")
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            review_summary(obs,Path(directory));summary=pd.read_csv(Path(directory)/"initial_cluster_review_summary.tsv",sep="\t")
            self.assertTrue(summary.doublet_or_subcluster_decision.eq("pending_review").all())
            self.assertFalse(summary.final_cell_selection.any())
        self.assertFalse(PLAN["numeric_doublet_cutoff_specified_by_article"])
        self.assertFalse(PLAN["automatic_doublet_calls_or_removal_by_this_entry"])

    def test_categorical_calibration_labels_need_no_new_category(self):
        obs=observations();obs["initial_cluster"]="0"
        obs["published_cell_type"]=pd.Categorical(["Astrocyte"]*60+["UNKNOWN"]*59+[None])
        with tempfile.TemporaryDirectory() as directory:
            review_summary(obs,Path(directory))
            table=pd.read_csv(Path(directory)/"initial_cluster_review_summary.tsv",sep="\t")
            self.assertEqual(int(table.n_unassigned_calibration_labels.iloc[0]),60)

    def test_actual_embedding_and_serialization_when_cluster_runtime_available(self):
        try:
            import anndata as ad
            import scanpy
            import sklearn
            import igraph
            import leidenalg
            import harmonypy
        except ImportError:
            self.skipTest("Full Scanpy/AnnData/SVD/Leiden runtime absent locally; actual cluster QA must execute this test")
        rng=np.random.default_rng(44);counts=rng.binomial(2,.2,size=(120,80)).astype(np.int32);counts[1,:]=0;x=sparse.csr_matrix(counts)
        src=input_object();a=ad.AnnData(x,obs=src.obs.copy(),var=pd.DataFrame(index=["peak"+str(i) for i in range(80)]));a.uns.update(src.uns)
        a.obs["qc_total_counts"]=np.asarray(a.X.sum(axis=1)).ravel();a.obs["qc_detected_features"]=np.diff(a.X.indptr)
        a.obs["frip"]=.2;a.obs.loc[a.obs.index[1],"frip"]=0.
        before=a.X.copy();ids=a.obs_names.tolist()
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            baseline=None
            for name,batch in [("uncorrected",None),("harmony","technical_batch")]:
                target=Path(directory)/name;target.mkdir()
                working=a.copy()
                validate_initial_atac(working)
                args=SimpleNamespace(output=target,input="synthetic_raw_peak_counts.h5ad",batch_key=batch,batch_provenance="PCR pool processing" if batch else None,
                                     min_feature_cells=2,n_components=3,n_neighbors=5,resolution=.6,seed=1729,threads=1)
                embed_initial(working,args);out=ad.read_h5ad(target/"atac_initial_atlas.h5ad")
                np.testing.assert_array_equal(out.X.toarray(),before.toarray());self.assertEqual(out.obs_names.tolist(),ids)
                self.assertEqual(int(out.obs.published_cell_type.eq("UNASSIGNED").sum()),60)
                self.assertEqual(out.obsm["X_umap_initial"].shape,(120,2));self.assertIn("initial_cluster",out.obs)
                self.assertNotIn("cluster",out.obs);self.assertNotIn("X_umap",out.obsm)
                self.assertEqual(out.uns["embedding_role"],ROLE);self.assertFalse(out.uns["final_doublet_selection"])
                self.assertTrue(out.obs.loc["cell1","zero_informative_peak_counts"])
                validate_initial_atac(out)
                self.assertEqual(out.uns["initial_neighbors"]["connectivities_key"],"initial_connectivities")
                self.assertTrue((target/"initial_embedding_complete.json").exists())
                if baseline is None:baseline=out.obsm["X_lsi"].copy()
                else:
                    np.testing.assert_allclose(out.obsm["X_lsi"],baseline,atol=1e-6)
                    self.assertEqual(out.obsm["X_lsi_harmony"].shape,(120,3))
                    self.assertIn("initial_cluster_uncorrected",out.obs)
                    self.assertEqual(out.obsm["X_umap_initial_uncorrected"].shape,(120,2))
                    self.assertIn("uncorrected_initial_connectivities",out.obsp)
                    self.assertIn("runtime_layout_provenance",json.loads(out.uns["batch_correction"]))


if __name__ == "__main__":unittest.main(verbosity=2)
