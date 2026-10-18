# Published Microglia accessible ATAC peaks and TE annotation

Actual accepted VSC job **8769240** analyzed **9,511 published ATAC Microglia cells across all 20 animals**. This is a different assay/cell selection from the 22,251 provisional RNA Microglia-like cells; the populations are not interchangeable.

Of 339,951 published mm39 peak regions, 339,735 passed conservative reciprocal conversion to mm10; 216 remain mapping exclusions rather than zero accessibility. The prespecified recurrent Microglia-accessible set contains **62,956** whole features after blacklist exclusion. A feature must be detected in at least max(3, ceil(1% of an animal's Microglia cells)) cells in each of at least two animals.

**35,694 / 62,956 (56.70%)** of these accessible peak features overlap at least one primary TE annotation.

This is accessible-region TE annotation. Neither a region count nor its full deposited accessibility count is a molecule-conserving TE-fragment count. A region may overlap multiple classes/families, so category fractions need not sum to 100%.

## Matched exploratory analysis

Matched **53,607** query peaks to disjoint nonquery published accessible peaks from **62,950** query peaks with complete measured covariates (85.16% retained). This represents 85.15% of the full callable primary query set.

Matching used exact chromosome/gene context and prespecified bins of GC, length, GenMap K76E2 mappability, TSS distance and measured non-Microglia peak-detection prevalence. Numerical matching balance required absolute standardized mean differences <=0.2.

Maximum measured absolute SMD: **0.3785**. Test status: **matching_failed_no_P_values**. P values and BH values were not reported because matching balance/support failed.

Exact paired binomial/McNemar tests describe exploratory peak-feature annotation associations conditional on the retained matched subset. They assume within-pair genomic feature exchangeability; local genomic correlation may inflate significance. They do not use animals as biological replicates and do not establish genotype or age effects.

## Twenty-mouse summaries

The point table includes all 20 mice. Each condition has four mice (two females/two males), and condition summaries weight each measured mouse equally. An animal with no detected callable peaks has NA for its overlap fraction, not zero. The per-mouse feature sets can differ. No condition differential test was performed.

## Practical limits

- Published ATAC processing retained primary, properly paired alignments with MAPQ >30. This favors uniquely mappable sequence and can underrepresent repetitive TE regions; GenMap is a single-read mappability proxy, not complete correction of that selection.
- Reciprocal conversion validates peak-region correspondence; it does not certify one-to-one orthology or identifiability of individual TE copies.
- GC and mappability were measured on full peaks; every blacklist-overlapping or ambiguous-reference-base feature was excluded from matched testing.
- These results are neither RNA TE expression nor autonomous TE activity. BAM-based physical-fragment/UMI TE quantification remains a separate endpoint.

## Deliverables

- `published_Microglia_ATAC_TE_report.pdf`: class overlaps, all 20 mouse points, and exploratory matched effects.
- `twenty_mouse_TE_accessible_region_points.tsv`: per-mouse denominators and TE-region fractions.
- `equal_mouse_TE_accessible_region_summary.tsv`: equal-mouse means, SD and ranges.
- Source analysis tables retain all TE tests, matching exclusions, pair IDs, measured covariates and receipt hashes.
