# Microglial transposable elements in ageing and 5xFAD mice

Panels C–E use the same 267,038 distinct mm10 TE copies. C1 contains 66,522 WT 21 mo RNA-specific copies and C2 contains 38,620 5xFAD RNA-specific copies. C3 (72,749) and C4 (54,337) are additional copies with higher RNA and ATAC in WT 21 mo only or 5xFAD only, respectively. C5 (34,810) qualifies in both. Specificity is an observed detection pattern in the sampled mice. Discoveries within preselected RNA/ATAC clusters are descriptive.

## B. TE RNA changes

Each dot represents one TE copy. The horizontal axis is the edgeR log2 fold change against WT 3 mo. Mice supply the replicates (4 WT 3 mo, 3 WT 21 mo, 4 5xFAD). WT_21mo_female_1 was excluded as in panel C. The robust quasi-likelihood model uses unrounded IRescue RNA allocations per mouse with gene-derived TMM effective depths. Autosomes and chrX use sex and condition. ChrY uses two males per group. The original count tables distinguish biological zero from missing female chrY values.

Choose raw P or genome-wide Benjamini–Hochberg adjusted P. The chosen value determines both the y-axis and color. The cutoff is strict (<). BH was applied once per contrast to all testable loci, before restricting the display to a cluster or a WT 3 mo detection set. All-zero copies in a contrast have no estimate. A raw P threshold provides exploratory features when testing hundreds of thousands of loci.

Exact mode draws every tested fold change and P value at the measured coordinates, to the precision of the SVG display. Coincident opaque symbols share the same ink. Density mode counts all points in fixed display bins and encodes counts on a logarithmic scale, separately for the three color classes. Dot size applies to exact mode. Narrowing the axes reports the number of off-screen points. The same two contrasts appear in every SVG. Raw per-mouse allocations, raw P, BH-adjusted P and log fold change are downloadable at full source precision. The 11 genome-wide parts have identical columns and disjoint rows. Together they contain every TE with RNA detected in at least one included mouse, including target-only copies. Each cluster is also available in one file.

## C. Matched RNA and ATAC

Both heatmaps average the same ordered TE copies within display bins. RNA units are expected IRescue TE allocations per million gene UMIs. ATAC units are coverage over the TE body relative to genome-wide coverage for the same mouse. Columns show condition means. RNA and ATAC come from separate nuclei. The original per-copy measurements and display bins are linked in panel C.

## D. Reference regulatory evidence

The denominator in each cell is every Figure C copy in that cluster. Four columns use the Zhu adult mouse microglial ChromHMM segmentation, cluster 20. We assign the TE midpoint, pooling the two promoter states and the two no-signal states. The supplied crosswalk documents the dense-state IDs and the figure and mark evidence for H3K27me3 and H3K9me3. The complete Zhu state table includes Zhu's own enhancer states.

The independent distal H3K27ac column uses the project's GSE218426 allNormTags ChIP workbook. Its header identifies 500-bp measurement windows at merged IL-33/vehicle ATAC IDR sites. We required an absolute Distance to TSS of at least 3,000 bp, positive normalized H3K27ac tags in at least one of eight libraries, and at least one base of overlap with the TE body. Each copy counts once per column. Of 104,977 valid reference windows, 72,394 met the distal and positive-tag criteria. This operational definition supplies distal acetylation evidence. The mice, treatment, and age of the external reference differ from the ageing/5xFAD project. The Zhu and ChIP columns may overlap, so rows need not sum to 100%.

We retained the project's mm10 start and end interpretation for these 500-bp windows and verified it reproduced all 44,163 prior ATAC-region overlap flags. The per-copy table also gives overlap counts for the broader IDR union and an alternate TE-midpoint overlap with distal supported windows. The reference peak table gives coordinates, TSS distance, study peak ID, tag sum, number of positive libraries, and the distal flag.

Sources: [ChIP workbook](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE218nnn/GSE218426/suppl/GSE218426_H3K27ac_ChIPseq_allNormTags.xlsx) · [microglial IL-33 study](https://doi.org/10.1084/jem.20220605) · [Zhu et al.](https://doi.org/10.1038/s41592-021-01060-3) · [ChromHMM deposit](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE152020)

## E. Age-related DNA methylation

Panel E uses independent female WT microglial snm3C ALLC pseudobulks at 8 weeks and 18 months. For each 1-kb mm10 tile, mCG is methylated CpG calls divided by all CpG calls. Each endpoint requires at least 20 total calls and three CpG records. A change of at least ten percentage points defines the age-hypo and age-hyper tiles. These pooled, descriptive calls have no biological-replicate P value. They are distinct from the authors' published three-age DMR analysis.

Of 2,407,854 callable tiles, 27,581 are age-hypomethylated and 62,189 age-hypermethylated. A TE counts once for each direction with any positive-length overlap. The 260,751 callable TE copies contribute to the comparison. Uncovered copies receive missing values, including chrY. Observed overlap counts are compared with expected counts drawn from the callable RNA/ATAC-detected TE universe, matched by chromosome, TE class, family, TE length bin, and number of callable tiles overlapped (capped at three). Each cell shows log2(observed / matched expected). This healthy-age reference also annotates copies selected in 5xFAD. It provides no 5xFAD methylation measurement. The downloadable strata, covered tiles and per-copy flags allow the panel to be reconstructed.

Source: [GSE292803](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE292803), [8 weeks](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM8865626), [18 months](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM8865625).
