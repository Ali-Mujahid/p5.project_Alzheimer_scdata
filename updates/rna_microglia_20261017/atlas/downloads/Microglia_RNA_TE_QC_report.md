# Microglia RNA TE QC and Figure 1

The recovered RNA merge and the new LiSC QC completed successfully and passed independent review. The analysis includes all 22,251 selected provisional Microglia-like cells, 192 libraries and 20 mice. All cells have usable mapped-UMI alignment exposure and positive exported TE allocation; no selected cells were dropped.

**Interpretation limit:** the first TE principal component is strongly associated with TE depth (Pearson r=0.920949; Spearman rho=0.908953) and the number of detected TE subfamilies (r=0.957610). The two TE-composition groups (13,041 and 9,210 cells) are descriptive, depth-associated groups. They are not validated biological Microglia states. Condition agreement with these groups is weak (adjusted mutual information=0.002644); this is not a test of a condition effect.

## Count and sample QC

- 1,075 retained TE subfamilies; 1,061 have positive allocation.
- Total exported expected allocation: 4,948,337.721. Pre-export algorithm UMI clusters: 4,948,365. The net export precision difference is 27.279 units. These are expected IRescue allocations, not certified physical molecules.
- Median exported allocation per cell: 191; median detected subfamilies: 97.
- Canonical-cell, mouse and mouse-by-original-state mass conservation passed independently in compute. Selected summary totals, metadata, coordinates and depth correlations were separately reviewed.
- All 22,251 original metadata records and provisional QC/confidence fields are preserved. Zero exported allocation and no usable exposure each affect zero cells in this result.
- The exact selected cell IDs, original states, animal, library, condition, sex, genotype, age and original global row joined the accepted saved gene coordinates.

| Condition | Mice | Female/male | Selected cells |
| --- | ---: | --- | ---: |
| WT_3mo | 4 | 2 / 2 | 4,978 |
| WT_6mo | 4 | 2 / 2 | 4,384 |
| WT_21mo | 4 | 2 / 2 | 4,487 |
| 5xFAD_3mo | 4 | 2 / 2 | 2,950 |
| APOE4_TREM2_3mo | 4 | 2 / 2 | 5,452 |

## Figure panels

A: the actual five-condition, 20-mouse RNA cohort. B: saved gene RNA UMAP for the exact selected cells, coloured by the original provisional gene states. C: separate gene and TE RNA layouts coloured by condition; positions are not aligned or integrated. D: actual per-cell TE allocation, detected-subfamily and mapped valid-UMI alignment-record QC distributions. E: provisional TE groups and state/condition/depth overlays, with the depth association noted above. F: mouse-level TE-family composition heatmap. G: equal-mouse family-composition dotplot; dot area represents the fraction of four mice with signal.

This adapts the supplied figure's scientific panel style to the actual data. The EPO treatment, joint RNA–ATAC embedding, transfer prediction scores, gene-expression marker panels and genome coverage tracks from the example are not produced here.

## Methods and scope

Fractional IRescue expected EM allocations remain unchanged. Exact three-decimal arithmetic is audited as lossless milli-units; it does not make the counts observed integers. TE composition uses each cell's total exported TE allocation, scaled to 10,000 and log1p transformed. The embedding uses nonconstant subfamilies, 30 PCs, 30 neighbours, UMAP min_dist 0.3 and provisional Leiden resolution 0.5, seed 20261021. No biological covariates were removed or parameters searched to improve the visual separation. The saved gene UMAP retains its original 52,016-cell fit; the displayed subset was joined by exact observation ID without refitting.

Mouse family proportions use total exported TE allocation, with equal-weight means of four mice per condition. This is relative TE composition, not whole-transcriptome-normalized RNA expression or evidence of autonomous TE transcription. Raw source family-label conflicts are preserved as unsplit bins. Mice remain the biological replicates. No differential TE-expression P values, physical-molecule certification, final singlet certification or joint RNA–ATAC inference are claimed.

## Provenance

VSC recovered merge: 8782686, COMPLETED 0:0. LiSC QC: 7522290, COMPLETED 0:0. Current source, actual allocated guard/runtime checks, original input continuity, exact mass/axes, complete outputs, process retirement and storage checks passed. All 25 QC/coordinate/PDF products were copied once and verified against the allocated producer SHA/size manifest. No raw merged count matrix, BAM or original gene-expression matrix was parsed locally for this review.
