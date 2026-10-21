# Atlas-wide ATAC architecture and cell-type accessibility

Status: independently reviewed global coordinate panels B–E and the official CATlas benchmark, updated on 21 October 2026. The native pseudobulk aggregation is also independently accepted. Panel A models/motifs remain **PENDING**. Panel E uses the successfully completed and independently audited expected-hit/OE correction. Source review and generated runtime checks are distinguished from scientific results.

## Study scope and comparison

The coordinate comparison uses two complete catalogs on the same mm10 genome: **68,126 native peak regions** and **339,735 published peak regions** retained by the reviewed reciprocal-95% conversion from 339,951 original mm39 regions. The 216 excluded original regions remain documented. These catalogs summarize the atlas; they are not Microglia-only peak sets. Their different sizes and region widths can change overlap rates and do not establish which analysis is biologically better. Both catalogs originate from the same underlying study and are not independent biological replications.

Panel A currently uses only the native peak-count universe. Its population is the **360,530 native cells with exact library-qualified matches to the 31 published calibration labels**, across 20 mice and 104 libraries. These are transferred calibration labels, not independent annotation validation. The native initial atlas also contains **95,942 unassigned cells**, retained as a separate aggregation category and excluded from both target and annotated-rest inference. The **15,779 published-only cells** absent from the native count matrix are not fabricated as zero samples. All 456,472 native initial cells remain accounted for; this stage does not establish final singlets, retention or fine biological identity. No published count-matrix differential model is claimed.

The source paper supplies the Figure 2 presentation framework, rather than a matching dataset or identical statistical analysis: [bioRxiv Figure 2 paper](https://doi.org/10.1101/2025.10.13.682070), [author analysis code](https://github.com/umutcakir/ATAC_EPO_vs_Placebo). Its experimental conditions, cell populations and peak catalog differ from this study. Our methods below make the coordinate units, mouse-level replication and repeat background explicit.

## A. Mouse-paired cell-type accessibility and motifs

Raw integer native peak counts are aggregated per mouse and label. Each of the 31 published calibration types is contrasted with the other annotated types within the same mouse. Unassigned cells do not enter the annotated rest. The fixed design is **DESeq2 `~ animal_id + compartment`**, with Type-minus-Rest log2 fold changes and size factors proportional to each compartment's admitted unique-fragment exposure. The mouse block controls mouse-specific main effects; sex and condition are not added as collinear terms. This question measures intrinsic type-versus-rest accessibility, not disease or aging effects within a type.

A supported model requires at least four mice with positive exposure in both compartments. A peak is eligible when its combined Type-plus-Rest raw count is at least 10 in at least four paired mice. Every type and peak remains represented in support or result tables, including unsupported/NA rows. The default dispersion fit is used with any automatic fallback reported. If the initial fit has FALSE or missing beta convergence, one prespecified Wald-test retry uses maxit 1,000 and the same fitted dispersions and exposure size factors. Both default and final diagnostics are retained. Positive discoveries require exact TRUE final convergence, positive log2 fold change and the declared threshold. Final DESeq2 P values and BH values are retained unchanged; BH is not recomputed after the convergence screen.

Primary positive calls use q < 0.05, exploratory calls q < 0.10, and a paper-style q < 0.01 summary is supplementary. Correction is within each type's tested peak universe, not globally across all 31 types. Missing types or failed models receive explicit reasons rather than zero discoveries.

Motif testing, when completed, uses the pinned JASPAR2020 CORE vertebrate motif collection, all_versions=FALSE, on the mm10 native peak sequences. Positive-DAR foregrounds are tested against an eligible complement matched for GC, width and label-blind accessibility strata, with a common control-to-foreground ratio across retained strata. All tested motifs enter BH correction within each type/query; foreground/background shortages and missing covariates remain visible. Similar motifs do not identify a unique transcription factor, and sequence compatibility does not demonstrate binding or activity.

**Accepted aggregation facts:** job 7518050 completed successfully and passed independent terminal/source/input/exposure review. It produced 640 mouse-by-category groups, including the unassigned category, and 620 potential type/rest mouse pairs. There are 608 positive-exposure pairs and 12 absent-type pairs; each of the 31 types has 12–20 usable pairs. The complete raw aggregation conserves 384,930,817 peak assignments. The shared labeled population accounts for 256,143,636 assignments and 1,985,081,826 admitted unique fragments. Assignment totals can count a fragment in overlapping peaks and are not FRiP or fragment denominators.

**PENDING results:** fitted/unsupported type counts; positive DAR counts at q < 0.01/0.05/0.10; numerical retry/convergence counts; actual dispersion fit types; motif support and full tested motif counts. Do not replace these fields with source-readiness test counts.

## B. Genomic context and external cCRE coverage

For both catalogs, the primary one-base coordinate is the **lower center proxy** of each original BED0 region: `start + floor((end-start-1)/2)`, represented as `[center, center+1)`. It is not a measured summit. Even-width upper-center results are a fixed one-base boundary sensitivity. A native-only MACS summit sensitivity, if supplied later, must retain its original summit provenance and is not imputed for published regions.

Both peak-center universes and the centers of the complete canonical TE reference are annotated using the same pinned mm10 knownGene TxDb and ChIPseeker. Context priority is Promoter, 5′UTR, 3′UTR, Exon, Intron, Downstream, Intergenic, with a ±3 kb promoter window and 300 bp downstream window. First/other exon and intron annotations retain their raw provenance. The effective nearest-TSS feature set is the gene-associated transcript set used by ChIPseeker, not every orphan transcript in the TxDb. Context categories must partition their declared universe exactly. Nearest-gene annotation is not a demonstrated regulatory target.

The external benchmark is the **official CATlas adult mouse cerebrum resource**, using the pinned 160 BED roster available through the [official CATlas portal](https://www.catlas.org/catlas/index.php) and its [archived mouse-brain downloads](https://decoder-genetics.wustl.edu/catlasv1/catlas_mousebrain/downloads.html). These external data differ in brain-region and atlas scope from the present study. Full peak regions are tested for any overlap with the coordinate-deduplicated cCRE union; overlap and non-overlap counts retain the full original peak-ID denominators. Original raw files, acquisition metadata and computed payload hashes are retained. The official resource is an explicitly named benchmark: identity with the source paper's private local `catlasv1` folder is unproved. CATlas overlap describes coverage geometry; it is not a pipeline quality ranking or evidence that non-overlapping peaks lack biological function.

**Reviewed results:** job 7518091 completed the full context/overlap analysis; job 7518190 completed acquisition and the external cCRE benchmark. All 11 genomic contexts partition each of the five declared context universes, including all 3,651,522 canonical TE-locus midpoint proxies. The complete summaries and PDF show every context and denominator. Changing lower to upper centers changes 30 native and 103 published TE-overlap flags, respectively; these boundary sensitivities are exported separately.

The official 160 cCRE catalogs totaled 344,208,737 acquired bytes and yielded 491,818 distinct canonical coordinate intervals. Full-region cCRE overlap was **64,698/68,126 native peaks (94.9681%)** and **278,980/339,735 published peaks (82.1169%)**. Native peaks intersected 57,038 distinct cCREs; published peaks intersected 271,667. The native catalog's larger within-catalog overlap fraction and the published catalog's broader cCRE coverage measure different quantities. Neither establishes an analysis-quality ranking. All raw catalogs and provenance remain retained; the external reported total is a consistency check, not proof of identity with the paper's private folder.

## C. Peak-ID gene/TE overlap

Each original peak ID receives two booleans from the same primary center: overlap with a TxDb gene body and overlap with a canonical TE interval. Gene-only, TE-only, Both and Neither must sum to the complete peak-set size. This Venn diagram counts peak IDs, not genes or TE insertions, and does not test enrichment.

**Reviewed results (peak IDs at lower-center proxies):**

| Catalog | Gene only | TE only | Both | Neither | Total |
|---|---:|---:|---:|---:|---:|
| Native mm10 | 37,762 | 2,878 | 2,856 | 24,630 | 68,126 |
| Published mapped mm10 | 178,066 | 24,310 | 29,881 | 107,478 | 339,735 |

Thus 5,734 native centers (8.4168%) and 54,191 published centers (15.9510%) intersect canonical TE intervals. Full-region TE overlap, a separate geometry sensitivity, is 12,911 native regions (18.9516%) and 179,091 published regions (52.7149%). The Venn circles are schematic; their areas do not encode these counts.

## D. Repeat-family architecture

The reference contains **3,651,522 interval-defined TE loci**, deduplicated by chromosome/start/end/strand/repName from the pinned canonical mm10 RepeatMasker records. These are annotated intervals, not reconstructed full-length physical insertions. The declared primary scope is DNA, LINE, LTR, RC, Retroposon and SINE. Five classes are represented; Retroposon has no admitted reference rows. The taxonomy has 1,075 repName subfamilies and 43 canonical class|family bins, including explicitly unresolved family bins. Canonical aliases and uncertainty are retained.

For each family or subfamily, count an original peak ID once if its center intersects any corresponding reference locus. All distinct labels are retained for nested or multi-family overlaps. Fractions use the full peak-set denominator, and bars are nonexclusive across families. repName subfamilies are not renamed biological families. Simple_repeat and other non-TE repeat classes are separately labeled, outside the canonical TE denominator.

**Reviewed results:** both catalogs retain all 43 canonical family bins, and class summaries retain all six declared classes with Retroposon explicitly zero. The largest native midpoint family fractions were ERVL-MaLR (1,098/68,126; 1.6117%) and L1 (1,043/68,126; 1.5310%). The largest published fractions were L1 (12,680/339,735; 3.7323%) and ERVL-MaLR (9,565/339,735; 2.8154%). These are descriptive overlap fractions, not family-enrichment P values. Family bars retain every bin and nonexclusive membership; separate non-TE-repeat midpoint totals are 1,393 native and 5,845 published peak IDs.

## E. Interval-defined TE-locus coordinate association

The primary endpoint is a binary hit for each admitted reference TE locus when at least one fixed peak center intersects it. Repeated centers or overlapping peak IDs cannot multiply the locus hit. A peak can intersect more than one distinct locus. Let N be all admitted TE loci, K the loci hit by any center, n the loci in a family and k the family's hit loci. Expected hits are nK/N, and O/E is k/(nK/N). A one-sided upper-tail hypergeometric test, equivalently Fisher's family/rest by hit/not-hit table, is reported under this declared finite reference background.

BH correction spans all 43 family bins separately within each peak set. The 1,075-subfamily table has a distinct secondary correction scope. Primary q < 0.05 and exploratory q < 0.10 are kept separate. Every tested bin, zero support and undefined O/E remain exported; log-space tail probabilities avoid reporting a Monte Carlo P of zero. No across-peak-set or across-level global FDR is claimed.

A fixed label-blind sensitivity stratifies the reference by chromosome, global length quintile and GC quintile and reports observed hits, stratum-weighted expected hits and O/E **descriptively**. Unknown GC has its own missing-covariate stratum and completeness report. Family-versus-reference covariate distributions are retained. This does not supply covariate-adjusted P values. Copy exchangeability is an assumption: adjacent/nested related loci can be correlated, and repeat lengths, sequence composition and mappability differ between families. Mappability is not matched. The null tests coordinate association under a declared RepeatMasker interval background, not autonomous TE activity, TE RNA expression, causal regulation or condition effects.

**Reviewed results:** native centers hit **5,690** distinct reference TE loci, and published centers hit **54,231**, from the same 3,651,522-locus background. These are TE-locus counts; they differ from the peak-ID overlap counts in panels C–D because one peak can hit multiple loci and multiple peaks can hit one locus.

| Catalog | Hit TE loci | Family q < 0.05 / 43 | Family exploratory q < 0.10 / 43 | Secondary subfamily q < 0.05 / 1,075 | Secondary exploratory q < 0.10 / 1,075 |
|---|---:|---:|---:|---:|---:|
| Native mm10 | 5,690 | 26 | 26 | 168 | 202 |
| Published mapped mm10 | 54,231 | 30 | 30 | 480 | 521 |

Under this **raw interval-background null**, the smallest family q values include L2 and ERVL in the native set and L2 and ERVL-MaLR in the published set. For example, L2 has 346 observed versus 105.693 expected native hits (O/E 3.2736), and 2,412 observed versus 1,007.355 expected published hits (O/E 2.3944). These are coordinate-association effect sizes, not mappability-adjusted regulatory enrichment or evidence of autonomous TE activity. The separate chromosome/length/GC sensitivity remains descriptive and unchanged; no covariate-adjusted P value or robustness claim is added.

**Numerical correction:** the original completed job 7518112 preserved valid raw contingency counts, log P values, BH values and threshold flags, but integer multiplication overflowed in some expected-hit calculations. Correction job 7518312 recomputed only `expected_hits`, `observed_expected_ratio` and `log2_observed_expected` in double precision and regenerated the PDF. It repaired 36 missing expected values across the four unique family/subfamily tables; the combined family table repeats 16 of those rows. The corrected family and subfamily expected-hit totals each conserve K for both catalogs. All raw counts, P/BH values, underflow/FDR flags, GC-stratified fields and six original scientific inputs remained unchanged and were independently checked. Only corrected effect-size tables and the corrected E plot are used for presentation.

## Release and interpretation

Publish a panel only after its actual terminal, source, reference, input/output and conservation checks pass independent review. Retain all negative, unsupported and missing results. State the genome, peak universe, coordinate/statistical unit and denominator in every figure. Do not infer a better analysis from more peaks, more significant calls or cleaner separation. These architecture panels and native type/rest models do not replace the separately reviewed Microglia condition/age comparisons or their transgene-mapping caveats.

## Provenance to populate at final release

| Component | Current adoption status | Final source/job/result receipt |
|---|---|---|
| Native all-cell pseudobulk | Accepted aggregation only; no model | Job 7518050; source `0dbe45eb63dc8fab48bb5f052801d5c72de95fce68d3b8dda6b8cadaadc52bab`; independent terminal `bb7bced42bc58a3030850198a00557da726f1b27ac850dfddea6b9e5dd872676` |
| A paired native DAR | PENDING actual model adoption | PENDING |
| A motifs | PENDING actual motif adoption | PENDING |
| B–D architecture | Independently accepted coordinate architecture | Job 7518091; source `78fba80fadd2ee14ad93fe0732f2d739601b89f01b71b5a9257907f190c2305d`; independent review `14c4d84cbfe3f529cc63e3e78d7d43ca7e011f6d350f0c3d0b2a53749c755596` |
| Official CATlas benchmark | Independently accepted external full-region benchmark | Job 7518190; source `a6d80fbce717efb356bfda9c0128dcff2b01ef6c8eb491743d42f6c608bd1ec8`; independent review `316c193514f976aacd45a57fcefc092eb6273583b8e6daca33a10d2c7c9b11ec` |
| E TE-locus coordinate association | Independently accepted after narrow numerical correction | Original job 7518112 preserved; correction job 7518312; source `91ce43080e79dc64fe77b8232200943165e1b5a7c69ec12c8e6cf5af8b12ead2`; independent review `f27fc72ea1547b1f57b53db2fdbdc53a775f10415c54f104d464bed59e751d5f` |

This document reports only the independently reviewed stages named above; remaining stages stay explicit. No private filesystem paths are included.
