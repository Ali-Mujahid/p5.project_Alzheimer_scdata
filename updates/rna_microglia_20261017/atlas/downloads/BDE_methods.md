# Microglial transposable elements in ageing and 5xFAD mice

Panels C–E use the same 267,038 distinct mm10 TE copies. C1 contains 66,522 WT 21 mo RNA-specific copies and C2 contains 38,620 5xFAD RNA-specific copies. C3 (72,749) and C4 (54,337) are additional copies with higher RNA and ATAC in WT 21 mo only or 5xFAD only, respectively. C5 (34,810) qualifies in both. Specificity is an observed detection pattern in the sampled mice. Discoveries within preselected RNA/ATAC clusters are descriptive.

## B. TE RNA changes

Each dot represents one TE copy. The horizontal axis is the edgeR log2 fold change against WT 3 mo. Mice supply the replicates (4 WT 3 mo, 3 WT 21 mo, 4 5xFAD). WT_21mo_female_1 was excluded as in panel C. The robust quasi-likelihood model uses unrounded IRescue RNA allocations per mouse with gene-derived TMM effective depths. Autosomes and chrX use sex and condition. ChrY uses two males per group. The original count tables distinguish biological zero from missing female chrY values.

Choose raw P or genome-wide Benjamini–Hochberg adjusted P. The chosen value determines both the y-axis and color. The cutoff is strict (<). BH was applied once per contrast to all testable loci, before restricting the display to a cluster or a WT 3 mo detection set. All-zero copies in a contrast have no estimate. A raw P threshold provides exploratory features when testing hundreds of thousands of loci.

Exact mode draws every tested fold change and P value at the measured coordinates, to the precision of the SVG display. Coincident opaque symbols share the same ink. Spread mode moves overlapping points by up to three SVG units horizontally using a repeatable offset. The signs, vertical positions, selection and source statistics remain intact. Density mode counts all points in fixed display bins and encodes counts on a logarithmic scale, separately for the three color classes. Dot size applies to exact mode. Narrowing the axes reports the number of off-screen points. The same two contrasts appear in every SVG. Raw per-mouse allocations, raw P, BH-adjusted P and log fold change are downloadable at full source precision. The 11 genome-wide parts have identical columns and disjoint rows. Together they contain every TE with RNA detected in at least one included mouse, including target-only copies. Each cluster is also available in one file.

### Differential locus downloads

The two contrast buttons export all directional TE hits for the chosen scope and strict P or BH threshold. The third button exports unique loci passing in both comparisons. An Up-only or Down-only filter on the shared list requires that direction in both. The axis-limited option applies the original fold change and P-value coordinates to the selected contrast, or to both for the shared list. Exact dots, spread dots and density use the same loci. TSV and CSV include mm10 coordinates, subfamily, the original mouse measurements, effect sizes, both P values and selection settings. BED6 has chromosome, start, end, locus ID, score 0, strand. An empty list produces a header-only TSV or CSV. Static packages contain both significance measures at 0.05 for every volcano set.

## C. Matched RNA and ATAC

Both heatmaps average the same ordered TE copies within display bins. RNA units are expected IRescue TE allocations per million gene UMIs. ATAC units are coverage over the TE body relative to genome-wide coverage for the same mouse. Columns show condition means. RNA and ATAC come from separate nuclei. The original per-copy measurements and display bins are linked in panel C.

## D. Zhu adult mouse microglial chromatin

All five columns use Zhu et al. (GSE152020) and the same 267,038 mm10 TE copies as Figure C. We matched the deposited H3K27ac count-matrix barcodes to the authors’ annotated microglia (membership 20) and pooled 192 nuclei from the frontal cortex (135) and hippocampus (57). Six tissue/replicate combinations contributed 307,727 tags. The filtered matrix provides counts in 5-kb bins. We kept each replicate column, source bin, and total in the downloads.

By default the H3K27ac column requires both the adult microglial **active enhancer** ChromHMM segmentation at the TE midpoint (dense state 3) and at least one observed microglial H3K27ac tag in the bin containing that midpoint. This is evidence about chromatin surrounding the TE. It cannot localize the tag within the TE copy. Of 267,038 loci, 256,701 have a deposited midpoint bin. The other 10,337 are unmeasured for the mark and excluded from the two mark-based percentage denominators. A measured bin with zero tags is a valid zero. The per-copy table identifies the source state, bin bounds, tag count, number of positive libraries, and joint classification.

Use the panel selector to show either measurement separately. **H3K27ac detected** counts any measured midpoint bin with positive tags. **Active enhancer** uses the ChromHMM state irrespective of the count matrix. Promoter, H3K27me3, H3K9me3 and no-signal columns summarize the midpoint states among all called loci. The state crosswalk documents the IDs. These are independent adult reference data and are shared across the project conditions.

[Zhu et al.](https://doi.org/10.1038/s41592-021-01060-3) · [H3K27ac matrix and ChromHMM deposit](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE152020) · [Cell annotation and accession provenance](BDE_sources.json)

## E. Age-related DNA methylation

Panel E uses independent female WT microglial snm3C ALLC pseudobulks at 8 weeks and 18 months. For each 1-kb mm10 tile, mCG is methylated CpG calls divided by all CpG calls. Each endpoint requires at least 20 total calls and three CpG records. A change of at least ten percentage points defines the age-hypo and age-hyper tiles. These pooled, descriptive calls have no biological-replicate P value. They are distinct from the authors' published three-age DMR analysis.

Of 2,407,854 callable tiles, 27,581 are age-hypomethylated and 62,189 age-hypermethylated. A TE counts once for each direction with any positive-length overlap. The 260,751 callable TE copies contribute to the comparison. Uncovered copies receive missing values, including chrY. Observed overlap counts are compared with expected counts drawn from the callable RNA/ATAC-detected TE universe, matched by chromosome, TE class, family, TE length bin, and number of callable tiles overlapped (capped at three). Each cell shows log2(observed / matched expected). This healthy-age reference also annotates copies selected in 5xFAD. It provides no 5xFAD methylation measurement. The downloadable strata, covered tiles and per-copy flags allow the panel to be reconstructed.

Source: [GSE292803](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE292803), [8 weeks](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM8865626), [18 months](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM8865625).
