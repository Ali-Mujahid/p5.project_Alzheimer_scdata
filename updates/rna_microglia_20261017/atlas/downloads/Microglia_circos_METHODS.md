# Chromosome Circos views (25 October 2026)

## Scope

The four contrast plot shows provisional Microglia-like cells only. Each target is compared with WT 3 months: WT 6 months, WT 21 months, 5xFAD 3 months, and APOE4/TREM2 3 months. RNA and ATAC source models use mice as replicates. The three circular data rings are 5 Mb binned mean log2 fold changes for genes, all eligible common-universe ATAC peaks, and the eligible subset whose coordinates overlap mm10 RepeatMasker TEs. The source model's FDR<=0.1 counts are retained in the TSV. The binned mean is descriptive, not an additional significance test.

The TE class and family views show mm10 RepeatMasker genomic copy locations. They do not measure TE RNA expression or TE accessibility. The top eight family names are selected by genome-wide copy count among LINE, LTR, and SINE families. Copy density is binned at 5 Mb.

The older versus younger figure compares WT 21-month with WT 3-month mice. Its outer green ring shows the locations of annotated ETnERV2-int copies. The separate IRescue RNA subfamily analysis estimated ETnERV2-int log2FC +0.7026, within-contrast FDR 0.0204, four-primary-contrast pooled FDR 0.0816. The RNA assignment is at subfamily level; none of the positions in the ring is individually established as transcribed. Neither of the two WT age ATAC peaks at exploratory FDR<=0.1 overlapped a TE, so no specific differentially accessible TE locus is claimed.

## Inputs

- Mouse-level Microglia RNA gene edgeR results: `Microglia_gene_DE_20261025_v3/job-7664383/DEG/all_microglia__*.all_tested.tsv.gz`.
- Mouse-level common-universe ATAC DESeq2 peak results: `ATAC_common_union_TE_DESeq2_20261021_v1/job-7517231/science/DESeq2/*.all_peaks.tsv`; 26,590 eligible peaks per contrast.
- Exact combined-peak TE annotation: `ATAC_common_union_TE_DESeq2_20261021_v1/job-7517231/science/TE_annotation/combined_peak_TE_annotation.tsv`.
- GENCODE vM25 mm10 gene loci, mm10 canonical chromosome sizes, full RepeatMasker copy annotations, and `te-atac/TEs.sorted.bed` on LiSC.
- Reviewed RNA TE subfamily result: `RNA_TE_Differential_and_multimodal_20261021/RNA_DE/recovery_v2/selected_results_verified/subfamily/WT_21mo_vs_WT_3mo.FDR005.tsv` in the local work area.

Aggregation jobs 7664458, 7664461, and 7664464 ran on LiSC compute. The exact scripts and small TSV outputs are retained in `work/Microglia_circos_20261025/`. Gene annotation joined 55,364 source gene IDs; 36 contrast-row IDs across four models could not be mapped and were omitted from the positional RNA rings. The original differential result tables remain unchanged.
