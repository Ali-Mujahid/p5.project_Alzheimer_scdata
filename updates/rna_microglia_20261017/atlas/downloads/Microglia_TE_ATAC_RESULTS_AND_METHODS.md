# Microglia TE-ATAC analysis: accepted results,21October2026

## Full-reference family analysis and TE-derived UMAP

The analysis reused the completed mm10 RepeatMasker fragment counts for **9,152 selected Microglia cells, 104 libraries and 20 mice**. It did not rescan BAMs, recount fragments or restrict counts to accessible peaks. All cells retain their original QC and provisional published-calibration labels; this selection is not a new final cell-identity assignment.

**No TE-family bin passed FDR <0.05 or exploratory FDR <0.10 in any of the four comparisons.** This does not establish that biological effects are absent. The TE-derived embedding retained all 9,152 cells, but the prespecified Leiden analysis returned one group, rather than resolving additional Microglia states.

| Comparison, adjusted for sex | Eligible family bins | FDR <0.05 | Exploratory FDR <0.10 | Smallest FDR |
| --- | ---: | ---: | ---: | ---: |
| 5xFAD 3 months versus WT 3 months | 41 | 0 | 0 | 0.574 |
| APOE4/TREM2 3 months versus WT 3 months | 41 | 0 | 0 | 0.531 |
| WT 6 months versus WT 3 months | 41 | 0 | 0 | 0.983 |
| WT 21 months versus WT 3 months | 41 | 0 | 0 | 0.997 |

## Counting and differential analysis

The input contains 1,075 TE subfamilies from the assembly-matched full TE reference, with five represented TE classes within the six-class annotation scope. No absent Retroposon features were invented. Primary counts include a deduplicated admitted ATAC fragment only when it overlaps exactly one distinct TE subfamily. Fragments ambiguous between subfamilies remain excluded from primary counts, including ambiguity within a single family. Separate all-hit descriptive counts are not used in the model.

Summing these exclusive subfamily counts yielded **13,264,975 fragments in 43 family analysis bins**. Forty-one bins represent resolved family labels; two retain unresolved per-subfamily taxonomy labels. All bins remain in the tables. A condition-blind requirement of at least 10 counts in at least four mice admitted 41 bins; `DNA|TcMar-Pogo` and `LINE|L1?` lacked this support.

DESeq2 used raw integer mouse-level counts, design `~ sex + condition`, WT at 3 months as reference, and four independent mice per condition, two female and two male. Size factors were fixed proportional to each mouse's **total admitted unique ATAC fragments**, whose total is 38,409,129. The endpoint is therefore TE-family fragment rate relative to sampled ATAC exposure. It is not within-TE composition, absolute chromatin openness or TE RNA expression. Automatic count replacement was disabled; the actual dispersion trend fit was parametric and all fitted coefficients converged. Wald tests and Benjamini–Hochberg correction were applied within each comparison and family universe. FDR 0.10 remains explicitly exploratory.

Heatmaps show row-standardized log fragment rates. Dot colors summarize equally weighted mouse mean rates; dot area denotes the fraction of animals with nonzero counts. Neither plot uses individual cells as biological replicates.

## TE-derived embedding and its limits

Of 1,075 input subfamilies, 1,073 had positive primary counts. The embedding used Signac method-1 TF–IDF, 30 standardized LSI components, cosine neighbors and UMAP with a fixed seed. The two prespecified views use LSI 2–30 and, as a control, LSI 1–30. Condition, genotype, age, sex, animal and library labels were not used to fit the embeddings or regressed out.

**Depth remains a strong technical association.** LSI1 correlated with log admitted-fragment depth at Pearson r=0.952. Removing it did not remove all depth structure: LSI2 had r=−0.866 with log admitted-fragment depth and r=−0.925 with log primary TE depth; LSI3 also had r=−0.370 with admitted depth. Both fixed layouts, depth overlays and all 30 component diagnostics are retained. Any visual separation must be interpreted descriptively, without assigning biological TE states or genotype effects. Leiden resolution 0.5 returned a single provisional group containing every cell.

## Provenance and verification

The computation completed as job **7517207**, with successful whole-job and batch exit codes. Frozen source manifest: `cdcbfb3e420476a6b8dec64b31bc8833a9d736c48cd667e1404bd00f26ca3a9e`. Execution nonce: `ef5df932507145228b6596c15e7b1b45`.

Independent review passed 118 terminal, source, population, count-conservation, exposure, statistical and embedding checks. All 43 delivered PDF/table/JSON products were verified by SHA-256; input hashes were unchanged. Actual allocated checks included 14 operational guard checks and five generated runtime checks. The allocation used 2 CPUs and 16 GiB; own storage caps were 3 GB and 1,200 names, with the shared 500 GB/40,000-name limit retained. Storage and file-descriptor monitoring are sampled operational bounds. The model RDS, graph NPZs and runtime cache remain archived separately from the public report products.


## Common-peak differential accessibility and TE overlap

The analysis completed successfully and passed independent source, execution, 104-library, matrix and output-integrity checks. The analysis uses the same **9,152 selected initial Microglia-labelled cells, 104 fragment libraries and 20 mice** for a common universe of **335,546 mm10 peaks**. The fixed count filter retained **26,590 peaks** (at least 10 raw fragment counts in at least 4 mice).

DESeq2 compares each condition with WT at 3 months, adjusting for sex. Mice are the independent replicates, with two female and two male mice per condition. Standard median-ratio normalization is used. FDR is controlled separately within each contrast; the FDR 0.10 results are explicitly exploratory.

| Comparison versus WT 3mo | FDR < 0.05 peaks | Exploratory FDR < 0.10 peaks | TE-overlapping FDR < 0.05 peaks | TE-overlapping exploratory FDR < 0.10 peaks |
| --- | ---: | ---: | ---: | ---: |
| 5xFAD 3mo | 2 | 2 | 2 | 2 |
| APOE4_TREM2 3mo | 1 | 1 | 1 | 1 |
| WT 6mo | 0 | 0 | 0 | 0 |
| WT 21mo | 1 | 2 | 0 | 0 |

These are **per-contrast calls**, not a count of globally unique discoveries across comparisons. Effects are unshrunk and should be considered with their uncertainty and the small number of animals per condition.

The full canonical-chromosome mm10 RepeatMasker TE reference contains **3,651,522 distinct loci**. TE sequence overlaps **176,629 of 335,546 peaks (52.64%)** and **14,896 of 26,590 count-eligible peaks (56.02%)**. The endpoint allows six TE classes; the pinned feature taxonomy represents five, with no Retroposon feature invented. Peak annotation retains overlapping subfamilies, classes, families and union-covered bases.

The TE-overlap and width/GC/mean-accessibility-stratified ratios are **descriptive associations**. Mappability is unavailable, so these are not fully adjusted enrichment significance tests. A TE-overlapping accessible peak is not evidence of autonomous TE transcription, and a peak with no retained TE overlap is not necessarily gene-only.

The dispersion trend used DESeq2's automatic local-regression fallback. All coefficient fits converged. **22,005 of 26,590 initial per-peak dispersion estimates (82.76%) reached the diagnostic floor; none of the final dispersions did.** This boundary behavior warrants caution when interpreting the small candidate list. Sparse discoveries do not establish absence of biological changes.


All reported candidates have higher accessibility in the comparison condition. The two 5xFAD candidates are adjacent on chromosome 9: **44,041,759–44,045,767** and **44,047,550–44,050,268** (0-based half-open coordinates; log2 fold changes 6.15 and 7.38). They are two peak calls in one adjacent genomic region, not two independent regions. Their large effects need construct/homology-aware interpretation before any disease-driven TE claim. The APOE4_TREM2 candidate is **chr19:36,925,324–36,927,081**, overlaps SINE annotations, and has log2 fold change 1.15/FDR 0.0277. The WT21mo candidates have no retained TE overlap.


# ATAC TE counting scope

These analyses reuse processed ATAC fragments that were retained as uniquely aligned (`MAPQ >=30`, `NH=1`), filtered against the blacklist and deduplicated by library, cell, chromosome, fragment start and fragment end. Coordinates represent unshifted fragment spans. The original library-qualified cell identities remain distinct when barcodes recur in different libraries.

The full assembly-matched mm10 RepeatMasker TE reference broadens the annotation and counting universe; **it does not recover multimapping reads or other fragments excluded during preprocessing**. Repeat-rich TE families can therefore be underrepresented. Full-reference coverage is not equivalent to all reads from every genomic TE copy being identifiable.

For primary TE-family accessibility, a retained fragment is counted only if it overlaps one distinct TE subfamily; family counts sum those exclusive subfamily counts. Cross-subfamily ambiguous fragments remain outside this primary endpoint, even when their candidate subfamilies share a family. Separate all-hit counts are descriptive and are not a unique-fragment denominator. Ambiguous taxonomy labels remain explicitly unresolved.

For common-peak analysis, fragments are counted against the same nonoverlapping mm10 union of published and study peaks in the same selected cells. A fragment can overlap more than one distinct union interval; peak-assignment totals are therefore not fragment-recovery rates or FRiP. RepeatMasker overlap of a peak is a coordinate annotation. Raw TE-overlap ratios compare the DA set with all FDR-evaluated peaks; width/GC/baseMean-stratified summaries use the complement of the current direction-specific DA selection as their control pool. These ratios are descriptive, with no mappability adjustment or formal enrichment P value.

All findings concern ATAC fragment accessibility or TE-overlapping accessible coordinates. They do not measure TE RNA expression, establish autonomous TE transcription, identify active individual TE copies, or prove that a TE drives a nearby regulatory change. Differential tests use mice as biological replicates; cell-level embeddings are descriptive and retain their reported depth limitations.


## Candidate-locus interpretation

TEs cover 761/4,008 bp (19.0%) of UNION0319992, 117/2,718 bp (4.3%) of UNION0319993 and 117/1,757 bp (6.7%) of UNION0167018. The differential test counts the entire peak; it does not identify the TE segment as the source of the change. The two 5xFAD peaks exactly recur in the previously reviewed Thy1-region windows. Mouse Thy1 regulatory elements are part of the [5xFAD construct](https://www.mmrrc.org/catalog/sds.php?mmrrc_id=34840). A construct-related mapping or copy-number contribution is therefore a candidate explanation, not a demonstrated artifact or proof of endogenous TE activation. These peak-set results reuse the same cells and fragments; agreement with the previous peak sets is a robustness comparison, not independent biological replication.

## Reference definitions and delivery

Use the full RepeatMasker TE annotation for family-level fragment-rate analysis and the common peak union for candidate TE-associated loci. The latter uses full peak-interval overlap, not 1-bp peak-summit overlap. Its overlap percentages cannot be compared directly with a summit-based published figure. All primary q0.05 and exploratory q0.10 values, the null family findings, all 9,152 embedding cells and the depth caveat are retained.

Family job7517207 and common-peak job7517231 both completed with whole-job and batch exit0:0. The atlas includes PDF plots and TSV tables. Complete model objects and unselected full DA tables remain archived with the computation; no raw BAM was downloaded.
