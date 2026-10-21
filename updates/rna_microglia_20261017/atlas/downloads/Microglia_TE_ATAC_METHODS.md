# Microglia TE-family accessibility and TE-derived UMAP

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
