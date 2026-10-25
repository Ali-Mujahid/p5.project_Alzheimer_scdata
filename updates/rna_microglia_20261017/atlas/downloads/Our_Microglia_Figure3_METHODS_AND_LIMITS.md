# Figure 3 A–G adaptation: our Microglia data

This companion to the [published-data Figure 3 comparison](TrackerSci_Figure3_METHODS_AND_LIMITS.md) uses **our GSE212606 mm10 Microglia selections**, not the paper's GSE212251 newborn-cell cohort. It follows the reference panel sequence A–G but does not imply that the two cohorts, assays or cell-state labels are interchangeable.

## Inputs and execution

- RNA: 22,251 selected Microglia nuclei, raw 55,487-gene UMI matrix aggregated across the same 20 mice.
- ATAC: 9,152 selected Microglia nuclei, 335,546 nonoverlapping mm10 common-union peaks recounted from accepted fragments across the 20 mice. RNA and ATAC nuclei are different; **the mouse is the pairing unit**.
- Source cross-check: the saved RNA aggregate's 20 column sums match the reviewed raw-UMI-depth table exactly (12,756,037 UMIs total). The mouse IDs were taken from the companion high-resolution source, which was checked against the total matrix in its original producer.
- New source-bound LiSC extraction job **7667206 completed 0:0** in 3 seconds with 2 CPUs, 8 GB allocation and peak RSS 278,284 KB. It selected marker and TF genes, strand-aware promoters and three previously ranked TE-overlapping peak examples. The earlier 7667202 attempt stopped before output because it looked for mouse IDs in the total HDF5 rather than its companion file. The corrected source used the companion file, with the failed attempt retained.
- Promoter interval: 2 kb upstream to 500 bp downstream of the Gencode vM25 protein-coding TSS, respecting strand. A common peak counts when its BED interval overlaps this window. RNA is `log2(raw gene UMI / total mouse Microglia UMI × 1e6 + 1)`; ATAC is `log2(sum of promoter-peak raw counts / saved DESeq2 size factor + 1)`. The paired heatmaps use a separate within-gene z score for each assay.

| Panel | Measurement in our data | Interpretation limit |
|---|---|---|
| A | 20 matched mouse rows × 13 genes with promoter ATAC signal; RNA expression and promoter accessibility heatmaps are separate. | Mice, rather than the paper's newborn-cell types, form rows. The promoter window and normalization are stated above. |
| B | All 120,334 previously tested TE-overlapping peak–gene candidates: 4,168 TSS-near peaks at ≤3 kb and 116,166 distal candidates at >3–500 kb. Raw 20-mouse Pearson coefficients are shown with the condition+sex residualized coefficients. | The gray curve is an adjusted sensitivity, **not** a permutation null or formal empirical threshold. Across the full tested family, **zero positive links passed FDR 0.1**. |
| C | Csf1r and Apoe TE-overlapping candidate peaks, up to 18 per gene ranked by nominal P, with TSS and arc height proportional to absolute mouse-level Pearson r. | Genomic proximity plus correlation is exploratory. None of these arcs passed FDR 0.1. No causal enhancer–gene relationship is claimed. |
| D | Source-saved RNA and ATAC high-resolution Microglia UMAPs, colored by **cluster-mean** Csf1r or Apoe RNA expression and ATAC gene-body activity. The third column is the corresponding 20-mouse selected TE-peak versus RNA scatterplot. | The ATAC UMAP colour measures gene-body activity, not the selected TE locus. A verified **per-cell locus-by-peak matrix** is unavailable; the third column deliberately uses mouse-level observed counts instead of inventing a single-cell locus overlay. The 24 RNA and 12 ATAC clusters are provisional and are not one-to-one paired states. |
| E | Seven measured TF genes: observed condition+sex residual RNA–promoter ATAC correlations across mice versus 300 fixed-seed residual permutations per gene. | This tests a **promoter-accessibility proxy**, not TF motif accessibility. The permuted distribution is exploratory; no motif FDR or TF activity call is made. |
| F | Spi1 and Irf8 RNA expression versus their promoter ATAC counts across 20 mice, with nominal Pearson r/P displayed. | Promoter peak counts do not measure motif binding. Nominal P values are unadjusted examples. |
| G | The same mouse-level promoter proxy for Sall1, Mafb, Stat1, Nfkb1 and Runx1. | No transfer-imputed RNA or cell-as-replicate inference is used. |

The paper's motif-specific Figure 3E–G would require a validated Microglia motif-by-peak matrix or per-cell chromVAR-like deviations and a prespecified background, which this study has not yet produced. Its single-cell linked-distal-site UMAP would require a verified Microglia cell-by-locus ATAC matrix. The corresponding panels are visibly labelled as observed proxies or mouse-level alternatives.

## Downloadable quantitative inputs

`microglia_20mouse_gene_promoter_values.tsv` contains the exact 20-mouse gene, promoter and selected TE-peak plotting values. `microglia_gene_promoter_correlations.tsv` lists gene TSS, promoter peak IDs, raw and condition+sex-residual Pearson coefficients. `panel_B_TE_peak_gene_correlation_histogram.tsv`, `panel_C_exploratory_TE_peak_gene_arcs.tsv`, `panel_EFG_TF_promoter_proxy_correlations.tsv` and `panel_E_permuted_mouse_residuals.tsv` supply the other plotted numbers. `figure_manifest.json` records panel counts and selection. The figure uses the saved high-resolution Microglia UMAP JSONs and prior full TE-cCRE candidate result (`120,334` tested pairs); no BAM or fragment source was rescanned.
