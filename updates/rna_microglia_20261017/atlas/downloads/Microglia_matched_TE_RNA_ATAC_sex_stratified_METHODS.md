# Sex-stratified Microglia TE RNA and ATAC Circos

Four target-only TE-copy sets are reused exactly from the IRescue RNA and ATAC
mouse boxplots: WT_6mo 9,361, WT_21mo 9,725, 5xFAD_3mo 7,240 and
APOE4_TREM2_3mo 6,438 loci. Each target is compared with WT_3mo using the
identical copy set. The set identifies RepeatMasker TE copies overlapping a
target-group called ATAC peak and without an overlapping WT_3mo called peak.
It does not establish absence of WT_3mo ATAC signal.

The left column shows female mice; the right shows male mice. Each sex/group
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
Female chrY signal is shown only as the source reports it; do not interpret
female chrY alignment as a biological sex-specific TE effect.

Sources: four `IRescue_WT_3mo_vs_<target>.TE_RNA_counts.tsv` copy matrices;
`animal_TE_body_ATAC.tsv.gz` per-copy, per-mouse bigWig table;
`animal_bigwig_headers.json`; and
`normalization_and_mouse_metadata.tsv` (gene depths and sex). All source
tables are in the local `work` folder under
`IRescue_Microglia_locus_20261028`, `MAnorm_targetTE_RNA_20261028`, and
`IRescue_Microglia_DE_20261028`.

Validation: every IRescue copy ID matched the saved ATAC copy ID; 32,764
copy-by-target membership records were checked. Reaggregating all windows
reproduced the existing RNA boxplot mouse values with maximum absolute
difference < 1e-12, and the existing ATAC boxplot mouse values with maximum
absolute difference < 5e-15. This figure is descriptive; same-data
peak-selection bias, sparse bins and small sex-stratified sample sizes limit
inference. The supplied Python source and complete window TSV allow replotting.
