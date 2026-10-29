# Sex-stratified Microglia TE RNA and ATAC Circos

Four target-only TE-copy sets are reused exactly from the IRescue RNA and ATAC
mouse boxplots: WT_6mo 9,361, WT_21mo 9,725, 5xFAD_3mo 7,240 and
APOE4_TREM2_3mo 6,438 loci. Each target is compared with WT_3mo using the
identical copy set. The set identifies RepeatMasker TE copies overlapping a
target-group called ATAC peak and without an overlapping WT_3mo called peak.
It does not establish absence of WT_3mo ATAC signal.

The left column shows female mice (chr1-19 and chrX only); the right shows male
mice (chr1-19, chrX and chrY). This corrects an earlier version that plotted
chrY reference TE copies and small source-assigned RNA/ATAC signal in female
panels. Those female chrY source values are retained in a separate audit table,
not interpreted as a Y chromosome in those mice. Their cause (for example,
ambiguous alignment to homologous sequence) has not been established from BAMs.
Each sex/group
normally contributes two mice. WT_21mo_female_1 is excluded only in the
WT_21mo contrast to match the displayed seven-mouse RNA and ATAC boxplots;
that target-female panel contains one mouse. The exclusion is a requested
sensitivity analysis, not a demonstrated QC failure. Sex differences are
descriptive and are not tested.

Every TE copy is placed in one 1 Mb mm10 window by its midpoint. The grey
track counts copies from the corresponding target-defined set in each window.
The red and blue tracks are equal-mouse mean TE-body ATAC signals for target
and WT_3mo. For each mouse, the saved bigWig signal integral is divided by
the full TE length and then by that mouse's bigWig `sumData/nBasesCovered`.
The mean across loci in a window is then calculated. Existing bigWig
normalization commands were not independently established. Uncovered bases
within represented chromosomes contribute zero.

The orange and green tracks are equal-mouse mean IRescue expected TE UMI
allocations for target and WT_3mo. Each mouse's allocations are summed across
the copies in that 1 Mb window and divided by its matched same-nucleus raw
gene UMI total, times one million. These are fractional expected allocations,
not observed uniquely localized transcripts. ATAC and RNA tracks have
separate scales. All tracks use log1p display transformation and a common
assay-wide 99th-percentile height cap; the downloadable TSV retains unscaled
values. Empty windows have zero selected TE copies and no TE-body ATAC mean.
Female chrY rows are absent from the corrected window table and plot. The
female sets therefore contain 9,211 (WT_6mo), 9,716 (WT_21mo), 7,122 (5xFAD)
and 6,428 (APOE4/TREM2) selected autosomal/X TE copies. Male panels retain
the full target-defined sets. No claim is made about biological sex effects.

Sources: four `IRescue_WT_3mo_vs_<target>.TE_RNA_counts.tsv` copy matrices;
`animal_TE_body_ATAC.tsv.gz` per-copy, per-mouse bigWig table;
`animal_bigwig_headers.json`; and
`normalization_and_mouse_metadata.tsv` (gene depths and sex). All source
tables are in the local `work` folder under
`IRescue_Microglia_locus_20261028`, `MAnorm_targetTE_RNA_20261028`, and
`IRescue_Microglia_DE_20261028`.

Validation: every IRescue copy ID matched the saved ATAC copy ID; 32,764
copy-by-target membership records were checked. Before female chrY exclusion,
the source reaggregation reproduced the historical RNA boxplot mouse values
with maximum absolute difference < 1e-12 and ATAC boxplot mouse values with
maximum difference < 5e-15. The corrected female mouse boxplot values are
distributed separately and used by the interactive atlas boxplots. Across the
15 female animal-by-target records in those comparisons, chrY contributed at
most 0.0358% of selected RNA expected allocations; exclusion changed the
per-copy ATAC mean by at most 1.622%. These values do not identify why the
female source assigned signal to chrY. The eight exploratory two-sided
mouse-level rank-sum p-values for the four RNA and four ATAC target comparisons
were unchanged by this exclusion. In the linked IRescue gene-TMM TE-copy DE
tables, all 287 chrY rows across the four comparisons were untested and none
appeared in FDR 0.05 or 0.10 lists; the separate seven-mouse WT21 sensitivity
table likewise tested no chrY row. This is a targeted audit of these outputs,
not an audit of every atlas analysis. The full original IRescue and ATAC
matrices, historical static figures and differential analyses remain as saved;
they have not been silently rewritten or re-tested. This figure is descriptive; same-data
peak-selection bias, sparse bins and small sex-stratified sample sizes limit
inference. The Python source, corrected window TSV and female chrY audit TSV
allow this specific figure and its correction to be inspected.
