# GSE212606 RNA methods: results and live status

28 October 2026. Biological replicate: mouse (20 animals, four per condition). Broad cell labels and Microglia subclusters are provisional.

## 1. scCODA cell proportions — finished

RNA: 2,281,619 cells, 15 broad labels, 20 mice. A model of condition versus WT_3mo with sex included selected three exploratory effects at estimated FDR 0.1: 5xFAD_3mo Granule neuron log2 fold change −0.148; WT_21mo Endothelial cell −0.501; WT_21mo GABAergic neuron +0.540. It did not select a Microglia proportion effect. The fit used 500 warmup and 1,000 posterior draws and has only four mice per condition. `../Cell_composition_20261028/scCODA_broad_composition_effects.pdf`, `../Cell_composition_20261028/sccoda_effects.tsv`, and `../Cell_composition_20261028/sccoda_broad_result_metadata.json` contain the figure and full effects. The separate ATAC initial-cluster sensitivity is in `../Cell_composition_20261028/ATAC_initial_scCODA/`; two selected clusters have QC or lineage concerns, so those numbers are not biological cell-type proportion findings.

## 2. CellChat communication — finished

CellChat 2.2.0.9001 used 29,973 mouse-balanced RNA cells, mouse ligand–receptor database, triMean, 100 bootstraps, and five condition networks. Inferred links by WT_3mo / WT_6mo / WT_21mo / 5xFAD_3mo / APOE4_TREM2_3mo were 5,462 / 5,368 / 3,919 / 5,447 / 5,289. Pathways were 36 / 40 / 29 / 41 / 37. See `cellchat_results/CellChat_top_pathways.pdf`, `cellchat_results/CellChat_Microglia_involving_pathways.pdf`, and the complete link/pathway TSVs in that folder. Network strengths pool cells by condition and do not constitute mouse-replicate differential signaling tests.

## 3. Monocle3 trajectory — finished on representative Microglia subset

LiSC job 7748025 completed 0:0. The fit used 4,517 stratified Microglia cells from all 20 mice and 2,930 reviewed variable genes. All 4,517 cells have finite inferred pseudotime rooted on a fixed-seed subset of WT_3mo provisional homeostatic cells. The graph test found 153 genes with q<0.05; Monocle3 grouped those into five modules (49, 40, 25, 20, 19 genes). `monocle_results/Microglia_Monocle3_readable_summary.pdf` gives the legible UMAP and animal medians; the same folder has Monocle's graph and condition PDFs, cell pseudotime, gene-association and module tables, and the fitted CDS. This cross-sectional ordering does not establish chronological time or disease progression. Full 22,251-cell graph attempts exceeded practical memory; pseudotime is therefore only for the 4,517-cell subset.

## 4. scVelo RNA velocity — in progress

The published count atlas has no spliced/unspliced layers, so the analysis must count those from exact Microglia reads in the 20 animal RNA BAMs. The first-animal pilot verified all 456 expected cells and nonzero spliced/unspliced counts. A pilot dynamical fit had too few shared genes to support a velocity graph; this is not a conclusion about the combined 20-animal data. LiSC tagging array 7747789 is scanning the other 19 BAMs; per-animal velocyto tasks are submitted only after matching barcode, cell and BAM audits. The full 22,251-cell combined matrix, QC, dynamical fit, latent time and plots have not run yet. `RESULTS_STATUS.md` has the current job details and staged scripts.
