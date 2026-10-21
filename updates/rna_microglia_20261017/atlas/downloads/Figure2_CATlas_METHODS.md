# Official CATlas v1 external coordinate benchmark

All 160 official archived mousebrain mm10 cCRE BED catalogs were acquired over TLS with exact source-pinned HTTP identity headers, lengths and EOF checks. Their first payload SHA256 values are recorded; the HEAD roster did not provide payload hashes. These official files are an explicitly named external benchmark; equivalence to the paper authors local folder is unproved.

The primary benchmark deduplicates canonical mm10 chromosome/start/end triples across all catalogs. Catalog membership is retained. Noncanonical rows are excluded with counts, while all original 160 files remain unchanged. Distinct intervals and the separate union merging overlapping or book-ended intervals are both reported. Any-overlap peak flags are invariant to that merge. Original peak IDs are counted once using full BED0 half-open regions, not summits or midpoint proxies.

An external reported 491,818-cCRE count is shown only as a consistency diagnostic. Agreement would not establish file identity. No enrichment P value, annotation accuracy claim, independent biological validation or cell-type transfer is inferred.
