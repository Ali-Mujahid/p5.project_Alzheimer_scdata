# Independent review of TE overlap genotype atlas data

Verified job 7471562 saved group tables and download digests. All 502 checks passed. No raw peaks, cell matrices or BAMs were reread.

- All 28 initial calibration types remain represented. There are 467 available animal × type groups, of which 427 are callable and 40 have no callable peaks. A further 93 type × animal combinations were not available. Empty and absent groups must display as NA.
- All 20 microglia groups are callable. Each age–genotype condition has four animals, two female and two male.
- In microglia, any primary TE overlap covers a mean 5.7434% of callable peak bases in WT 3mo, 6.4630% in 5xFAD 3mo and 6.6265% in APOE4_TREM2 3mo. Respective descriptive genome-coverage folds are 0.1470, 0.1655 and 0.1697: all are below one. These descriptive differences are not a tested genotype effect.
- LTR is the largest microglia class by peak-base overlap in all five conditions. Its 3mo mean is 2.3601%, 2.4531% and 2.5979% for WT, 5xFAD and APOE4_TREM2. Native primary classes are DNA, LINE, LTR, RC and SINE; uncertain and non-TE repeat classes remain separate. Native repFamily is the family/subclass alias; repName is subfamily.
- RC coverage-fold rankings are sparse and animal driven. APOE4_TREM2 female R2 alone has 109 overlapping bp and fold 3.188, while the other three APOE4_TREM2 animals have zero. It must not be presented as a consistent enrichment.
- Microglia peak counts range from 4,829 to 11,679 across animals. Peak-call discovery, widths and sequencing depth are not matched by these overlap summaries.

All 32,116 saved equal-animal category summaries reproduce from 536,796 source coverage rows. No TE expression, fragment-level TE accessibility, final cell identities or differential inference is established.
