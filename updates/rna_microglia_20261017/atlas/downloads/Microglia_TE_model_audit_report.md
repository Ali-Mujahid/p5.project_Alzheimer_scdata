# Microglia TE accessibility and RNA: matched-animal model audit

## What the new measurements establish

The individual ATAC tracks confirm higher signal at the target-defined TE sets. The RNA models do not show a comparably large set-wide transcriptional increase. This is a comparison of the same TE intervals across the same 20 animals in two separate assays; it is not paired-cell multiome data. High DNA accessibility and high RNA transcription are distinct hypotheses.

The ATAC quantity below is mean bigWig signal across the full TE bodies, including zero-valued uncovered bases, divided by that track's genome-wide covered-base mean to control multiplicative scaling. The RNA quantity is the sum of assigned TE UMIs in the set divided by the gene-derived TMM effective depth from the same selected RNA cells. Each ratio is the target's four-mouse median divided by the control's four-mouse median.

| Target-specific TE set | ATAC median ratio | RNA median ratio |
|---|---:|---:|
| WT_6mo | 1.517 | 1.037 |
| WT_21mo | 1.540 | 0.985 |
| 5xFAD_3mo | 1.463 | 1.012 |
| APOE4_TREM2_3mo | 1.513 | 1.002 |

In the saved pooled WT_6mo profile, the central 200 bp signal is 8.056 in WT_6mo and 5.180 in WT_3mo. Outer-flank signals are 5.289 and 5.273, respectively. The WT_6mo centre/flank ratio is 1.523, compared with 0.982 for control. Thus the pooled ATAC pattern is confirmed, including similar background, but the height of pooled curves alone is not a mouse-replicate significance test.

## Input and set audit

- All 41,965 unique TE intervals in the exported RNA union were evaluated in each of the 20 individual ATAC bigWigs. No chromosome/coordinate interval was absent from an animal track. Genome assembly checks and unchanged source file identity/size/mtime checks passed in the compute job.
- ATAC source and RNA matrices were joined by exact mm10 chromosome, start and end; strand is retained on the RNA feature identifier. The previous RNA join had already established one-to-one coordinate/strand matching. Source TE names may differ in specificity between annotations.
- The screenshot uses 9,716 WT_21mo and 7,237 5xFAD K4-stable loci, while the unfiltered RNA sets used 9,725 and 7,240. WT_6mo uses the same 9,361 and APOE the same 6,438 loci. The 12 excluded loci have no assigned RNA counts in the 20-mouse matrix: full and stable RNA set totals are identical, so this mismatch does not explain the RNA result. Both versions were retained and tested as sensitivity analyses.
- The pooled and individual ATAC bigWigs have nearly equal genome-wide covered-base means (approximately 1.57–1.58). Their exact original normalization commands are not independently reconstructed by this audit; header values do not prove normalization provenance. Within-track background division addresses multiplicative scale only. These are processed coverage measurements, not newly counted raw ATAC fragments.
- Gene counts from the saved 55,487-gene × 20-mouse matrix exactly reproduce the accepted raw RNA depths. All mouse identifiers and selected-cell counts match the 22,251-cell Stellarscope cohort. TMM offsets were estimated separately from these gene counts and from all 1,075 TE subfamily counts.

## Count models and RNA effect sizes

Both edgeR quasi-likelihood and DESeq2 use integer Stellarscope-assigned counts, a `~ sex + condition` design, all 20 mice (four per condition), and identical fixed effective-library exposures. No display z-scores enter a differential-expression model. The two exposure choices are gene-derived TMM and TE-derived TMM. Gene-derived offsets retain a relative TE-versus-gene question, while TE-derived offsets estimate changes within the TE transcript pool. Neither establishes absolute transcript amounts without a suitable external calibration.

The table gives gene-TMM, sex-adjusted DESeq2 set-total estimates with 95% Wald intervals. Unlike a simple median ratio, a regression estimate accounts for sex, exposure and variance, so the two summaries need not be identical.

| Target | Model RNA fold change | 95% Wald interval | BH FDR across 4 primary contrasts |
|---|---:|---:|---:|
| WT_6mo | 1.000 | 0.913–1.096 | 0.997 |
| WT_21mo | 0.934 | 0.848–1.028 | 0.653 |
| 5xFAD_3mo | 1.013 | 0.920–1.115 | 0.997 |
| APOE4_TREM2_3mo | 1.012 | 0.922–1.110 | 0.997 |

The edgeR estimates closely agree. Neither model identifies a significant target-set increase under either exposure choice. The WT_6mo regression estimate is approximately 1.00, with a 95% interval of 0.91–1.10, even though its simple median ratio is 1.037. Individual-mouse variation and depth weighting explain why a modest median shift is not a model-supported increase.

For locus-level testing, an explicit count-support criterion—at least five assigned counts in at least four of the 20 mice—retains 1,089 of the 41,965 unique loci. All loci remain in the aggregate set analyses. Locus FDR is calculated across the retained unique union for each contrast; it is not recalculated separately inside the small target sets.

| Target set | RNA-supported loci / total | edgeR up/down at FDR .1 | DESeq2 up/down at FDR .1 | Effect Spearman correlation |
|---|---:|---:|---:|---:|
| WT_6mo | 246 / 9361 | 0 / 0 | 0 / 0 | 0.992 |
| WT_21mo | 215 / 9725 | 0 / 1 | 0 / 0 | 0.992 |
| 5xFAD_3mo | 182 / 7240 | 0 / 0 | 0 / 0 | 0.993 |
| APOE4_TREM2_3mo | 178 / 6438 | 0 / 0 | 0 / 0 | 0.996 |

All DESeq2 locus fits converged. The filter does not establish that excluded loci are biologically silent: short-read RNA support and locus identifiability are limited. Counts remain model-assigned rather than proof of autonomous TE transcription.

## Which model performed better?

A separate leave-one-mouse-out experiment compares Poisson and negative-binomial model classes on each target-defined set, using the same gene-derived exposure and sex/condition predictors. Held-out negative log likelihood is lower for the negative-binomial model in every set. Poisson Pearson overdispersion is approximately 9–14, making Poisson uncertainty unsuitable here.

| Target set | Poisson held-out mean NLL | Negative-binomial mean NLL |
|---|---:|---:|
| WT_6mo | 15.45 | 7.66 |
| WT_21mo | 17.08 | 7.40 |
| 5xFAD_3mo | 12.31 | 7.18 |
| APOE4_TREM2_3mo | 12.15 | 6.77 |

This validates the negative-binomial model class relative to Poisson; it does not establish that edgeR is superior to DESeq2. Their effect estimates are almost identical here. Robust edgeR quasi-likelihood is a reasonable primary count model with DESeq2 as sensitivity analysis, rather than selecting the model yielding the desired direction. Normalization choice remains a biological-estimand and calibration issue. The package methods are described in the [edgeR guide](https://bioconductor.org/packages/release/bioc/vignettes/edgeR/inst/doc/edgeRUsersGuide.pdf) and [DESeq2 vignette](https://bioconductor.org/packages/release/bioc/vignettes/DESeq2/inst/doc/DESeq2.html).

## Does accessibility predict RNA within corresponding animals?

An exploratory joint model adds the fixed-set mean ATAC signal to the sex/condition-adjusted negative-binomial RNA model, with gene-derived RNA exposure. None of the target-set ATAC coefficients passes the reported FDR threshold. Adding ATAC worsens held-out prediction for all four sets:

| Target | NLL without ATAC | NLL with ATAC |
|---|---:|---:|
| WT_6mo | 7.66 | 7.87 |
| WT_21mo | 7.40 | 7.62 |
| 5xFAD_3mo | 7.18 | 7.32 |
| APOE4_TREM2_3mo | 6.77 | 6.97 |

Across 1,089 RNA-supported loci, exploratory partial Pearson correlations of log-normalized RNA and relative ATAC signal after removing sex and condition yield no associations at FDR .1. This is a low-power, sparse-RNA analysis on separate cells; it does not prove biological independence or absence of regulatory activity. Condition and ATAC are correlated because the TE sets were chosen using ATAC, which also limits interpretation of a conditional ATAC coefficient.

## Better design for the biological question

1. Define a common, fixed mm10 TE/cCRE universe. Use independent peak discovery or discovery/validation splitting to test accessibility. The present target-only sets were selected from these same animals, so their ATAC enrichment is partly expected by selection and should not be treated as independent confirmation.
2. Count ATAC fragments and RNA UMIs in exactly matched intervals per mouse. Model each assay with its own appropriate offsets and `sex + condition`, preserving age/genotype biology. Confirm comparable Microglia states and quantify state-composition differences. Separate nuclei from corresponding mice provide animal-level matching, not paired-cell measurements.
3. For primary TE RNA differential expression, subfamily-level quantification offers more support than sparse individual repeat copies. Retain an RNA-supported and mappability-aware locus analysis as a second endpoint. Compare the existing TE quantifiers at the subfamily level without converting family totals into copy-specific expression.
4. Distinguish a TE promoter expected to initiate transcription from a TE-overlapping regulatory element. Increased accessibility at a regulatory TE interval may be associated with a nearby gene rather than more RNA assigned to that TE copy. Test TE–gene links on independently defined windows, and report this as a separate hypothesis; the present audit does not establish the mechanism.
5. Use mouse-level matched association models and uncertainty estimates; avoid treating loci, cells or technical resamples as animal replicates. A genuinely paired RNA–ATAC multiome experiment or deeper matched assays would provide a stronger test of cell-state coupling.
6. Use the full sets for primary inference. The K4 exclusions are a display/sensitivity choice based on ATAC signal, not a direction-free biological validation filter. The current normalization and model comparisons are exploratory because multiple views have already been examined.

## Deliverables and execution

The count-model PDF contains model effect estimates and Wald intervals, held-out prediction, omission sensitivity, ATAC-profile and RNA-support checks. The matched-assay PDF shows all 20 animal measurements across the four fixed target sets and coupling diagnostics. The tables archive includes normalized exposures, tested locus lists, full per-locus model results, set totals, paired signals, sample-sensitivity results and package versions.

LiSC job 7752065 completed 0:0 in 3m34s, with 73,584 KiB maximum RSS, reading only existing processed ATAC bigWigs. Source identities, coordinate bounds, source immutability and before/during/after quota/storage checks passed. The retained output cap was 64 MB / 100 files with filesystem and matched scratch-user/group quota reserves. The preceding job 7752062 failed before Python because of profile startup and is preserved; its corrected version has a separate submission identity. RNA model fitting reused the saved small matrices in installed local R (edgeR 4.2.2, DESeq2 1.44.0). No RNA BAM remapping or recount was performed.
