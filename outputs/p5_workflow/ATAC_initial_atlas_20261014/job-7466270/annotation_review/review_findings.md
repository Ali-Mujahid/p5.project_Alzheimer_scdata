# Initial ATAC cluster annotation review — job 7466270

## Takeaway

The saved ATAC marker activity supports provisional oligodendrocyte-associated (cluster 3), astrocyte-associated (4), microglia-associated (6), and several neuronal candidates. These are manual diagnostic candidates, not final per-cell identities. All 11 initial clusters contain all 20 animals and 104 PCR libraries, with no new exclusion applied. Cluster 8 is strongly concentrated in the four 5xFAD 3-month animals, requiring animal-level and QC sensitivity review before biological interpretation. Cluster 9 combines vascular/stromal activity with comparatively low FRiP and elevated nucleosome signal, while cluster 7 needs depth-aware comparison with the other granule-neuron-associated candidate. Raw counts, atlas labels, and source products remain unchanged.

## Evidence and limits

Candidates use coherent groups of individual raw gene-body activity markers summarized with equal animal weights. Published calibration labels are shown separately as supporting context and are not copied into final identities. The associated dotplots compare descriptive activity; within-gene scaled color cannot compare absolute strength between different genes. Cluster-average marginal detection cannot establish whether incompatible markers occur together in the same nucleus. RNA cluster numbers do not map directly to ATAC cluster numbers, and final RNA identities remain under review.

## Priority diagnostics

- Cluster 8: 9,557/11,606 nuclei (82.345%) are from 5xFAD 3-month animals, distributed across all four mice (2,905, 2,600, 2,320, 1,732). Its largest animal contributes 25.0%, but its largest PCR library only 1.34%. Median FRiP is 7.84% and TSS 3.72. This establishes condition concentration, not a genotype effect or an artefact; animal-level proportions, technical depth, coverage and marker breadth need review.
- Cluster 9: 8,671 nuclei; 90.19% lack published calibration labels. Median FRiP is 4.84%, TSS 3.21 and nucleosome signal 3.0, with 12,436 median unique fragments. Abcc9/Rgs5/Kcnj8 and Col1a2/Col3a1/Dcn activity motivates a vascular/stromal mixed candidate. Other panel signals occur too. Low FRiP could also reflect incomplete provisional peak coverage of rare states. No failure, doublet threshold or automatic removal is declared.
- Cluster 7: 11,611 nuclei; median unique fragments 12,295 and detected peaks 2,462, versus 3,000/680 for cluster 1. Both have Gabra6/Cbln3 neuronal activity. Higher activity breadth and counts alone cannot distinguish a real state, depth structure or doublets.
- Cluster 6: coherent P2ry12/Tmem119/Csf1r/Cx3cr1/Hexb activity supports a microglia-associated candidate, while Pecam1/Flt1 activity remains a breadth-review cue. ATAC activity is not RNA expression and does not alone establish vascular identity or mixed-cell status.

## Next analyses

Inspect existing corrected/uncorrected UMAPs and per-cell marker breadth for the priority clusters, assess animal/library-specific QC and depth distributions, and compare candidate identities with independently reviewed RNA markers. Any later doublet or retention decision needs a justified sensitivity analysis. Refined common peaks should follow reviewed identities and retention. No new heavy job is submitted by this review and no producer stage is rerun.

## Saved outputs and provenance

`provisional_cluster_annotation.tsv` records all 11 candidates, coverage, QC and pending review decisions. `candidate_marker_evidence.tsv` records actual per-gene descriptive activity and detection. Condition count and fraction tables expose both denominators. Inputs are the downloaded producer summary/coverage/marker tables, pinned by the existing download manifest and `review_provenance.actual.json`. No full matrix scan, new graph or gene/peak count was generated.
