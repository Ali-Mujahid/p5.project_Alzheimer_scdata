# Microglia TE-overlapping ATAC peaks and nearby RNA genes: five-group screen

Generated 24 October 2026 with local R 4.4.1. This is a descriptive screen of observed ATAC peak counts and observed RNA gene counts, not a set of validated peak-to-gene regulatory links.

## Inputs and scope

- The accepted combined mm10 peak matrix has 335,546 peaks measured across the same 20 animals. The full six-class mm10 RepeatMasker annotation overlaps **176,629** of those peaks by at least one base. All 176,629 are included in the retained local five-group ATAC table, even when their signal is zero or low.
- The RNA input is the accepted raw-gene pseudobulk from **22,251 selected provisional Microglia-like RNA cells**, spanning all 20 animals and 55,487 genes.
- Conditions are WT_3mo, WT_6mo, WT_21mo, 5xFAD_3mo and APOE4_TREM2_3mo. Each condition has four animals (two female, two male). RNA and ATAC nuclei are from the same animals but are not paired cell by cell.
- The earlier 14,896-peak count threshold applied only to a separate 20-animal inferential screen. It does not define the full TE-overlapping peak universe here.

## Values in the downloads

For each animal, raw ATAC peak counts were divided by its reviewed DESeq2 size factor. For each condition, the four normalized animal values were averaged; the five condition means are shown in the ATAC table. RNA raw gene UMIs were divided by each animal's total selected-Microglia gene UMIs and multiplied by one million before the four values in each condition were averaged. The RNA table reports these five group mean CPM values. The peak–gene table and PDF use `log2(group mean + 1)` for each assay.

Every TE-overlapping peak was mapped to all GENCODE M25 gene transcription start sites within 500 kb of the peak center, producing **4,304,442** peak–gene pairs. Pearson correlations use the **five group profiles**: 2,849,895 are defined and 1,454,547 are `NA` because at least one profile is constant. A `NA` correlation does not remove its peak from the complete ATAC table. No P value or FDR was calculated from these five descriptive points.

The local 8,530-row L1/MaLR/SINE file is a **plotting shortlist**, not a discovery set. It requires a protein-coding gene, TE coverage of at least 10% of the peak, signal in at least four groups, mean normalized ATAC ≥2, mean RNA ≥1 CPM, Pearson r >0.8, and a positive group change in both assays for at least one disease group versus WT_3mo. It is selected on the displayed trend, so its correlations must not be interpreted as independent confirmation. All rows remain in the full pair table regardless of this plotting filter.

## Group summary

The numbers below are TE-overlapping peaks with a **nonzero group-mean normalized count**, not condition-specific peak calls. Depth, sampling and detection affect them.

| Group | Nonzero among 176,629 | Median normalized ATAC count across all TE-overlapping peaks |
| --- | ---: | ---: |
| WT_3mo | 153,589 | 0.622 |
| WT_6mo | 154,105 | 0.636 |
| WT_21mo | 158,549 | 0.613 |
| 5xFAD_3mo | 157,746 | 0.737 |
| APOE4_TREM2_3mo | 156,118 | 0.787 |

These small descriptive differences are not differential accessibility tests. A nearby gene, matching trend or TE overlap alone does not establish a functional TE enhancer, autonomous TE expression or causality. The earlier animal-level condition-and-sex-adjusted screen found **no positive link at global FDR 0.10**; this group view does not supersede that result.

## Web downloads

The public atlas provides summary counts, six illustrative profiles and the first 100 ranked descriptive candidates. The complete 176,629-peak, 55,487-gene and 4,304,442-pair tables remain in the local analysis folder `work/TE_cCRE_gene_linkage_20261024/group_all_TE_peaks_20261024_v2`. The compact SVG is a re-rendering of the same six profile values as the local R PDF.
