# Correction of Figure E expected-hit arithmetic
Original job7518112 completed, but n*K integer multiplication overflowed before division for some large TE bins. Its original counts and inferential P/BH fields are preserved as historical outputs.
This correction uses as.numeric(n)*(as.numeric(K)/as.numeric(N)), recalculates expected_hits, observed_expected_ratio and log2_observed_expected only, and proves each family/subfamily expected mass sums to K.
All four raw count contingency tables, upper-tail hypergeometric log P values, BH scopes, underflow flags and FDR0.05/0.10 flags were reproduced. Original P/BH/stratified sensitivity fields are unchanged.
The fifth combined family table retains the same86 rows and ordering and changes the same three columns. The PDF is regenerated using the corrected values and the original plotting function.
No RMSK, genome sequence, BAM, fragment or count matrix was read or recounted. No model or alternative test was selected.
Units are interval-defined TE loci from deduplicated RepeatMasker chromosome/start/end/strand/repName records, not reconstructed physical insertions. Hypergeometric exchangeability is an assumption; nearby related copies may be correlated. Mappability remains unmatched.
This is raw coordinate association under the declared canonical TE-locus background, not TE expression, autonomous activity, condition effects or causal regulation. Official downstream presentation must use these corrected effect-size fields.
