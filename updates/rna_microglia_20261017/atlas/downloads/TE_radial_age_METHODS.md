# Circular TE divergence diagram (25 October 2026)

The figure uses the same **circular branching composition** as the supplied example. It is a RepeatMasker **annotation hierarchy** (TE class → family → subfamily), not a tree estimated from TE sequences. All branch lengths are drawing conventions and cannot be read as evolutionary time or relatedness.

The source is the canonical UCSC mm10 RepeatMasker table `references/mm10/canonical.rmsk.txt` on LiSC. Only primary chromosomes 1–19, X and Y and TE classes LINE, LTR, SINE, DNA and RC were retained. The 3,651,522 valid copies form 1,082 class/family/subfamily rows in the downloadable TSV. The `milliDiv` value is a copy's divergence from its RepeatMasker consensus in tenths of a percent. The lower-divergence bin is <10% (553,880 copies), the intermediate bin is 10–<20% (834,310), and the higher-divergence bin is ≥20% (2,263,332).

Panel A displays 59 abundant subfamilies, selected reproducibly as up to five most numerous families per class and up to three most numerous subfamilies per family, requiring at least 50 genomic copies. Panels B and C apply the corresponding dominance requirement (at least 30 copies and at least 60% of a subfamily's copies in the indicated lower- or higher-divergence bin) and display 12 and 26 subfamilies. Orange and teal outer arcs represent the fractions of each plotted subfamily's copies in those two bins. All 1,082 rows and intermediate counts remain in the TSV.

Lower divergence can indicate a relatively younger insertion but is not a calibrated age: copy-specific mutation rates, CpG decay, consensus reconstruction and subfamily heterogeneity affect the measure. This is a **genomic-copy reference diagram**, not a Microglia-specific expression/accessibility result. The separate chromosome Circos plots show the measured Microglia tracks.

The summarization ran on LiSC compute as job 7666955 and completed 0:0. Its script and the rendering script are saved with this methods file. No read alignment or TE expression was recomputed for this figure.
