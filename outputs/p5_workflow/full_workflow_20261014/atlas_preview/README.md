# Local initial ATAC atlas preview

Open the locally served atlas at `http://127.0.0.1:56404/full_workflow_20261014/atlas_preview/index.html`. Keep the full project layout together: producer PDF links and the TE adapter reference sibling project files. The TE view loads local JSON using HTTP and therefore requires the local server; opening `index.html` directly with a `file:` URL does not support that view. The server serves `outputs/p5_workflow` and binds only to `127.0.0.1`. No Internet connection, public upload, account connection or CDN request is used.

This is a **provisional initial ATAC explorer**, not the completed final RNA/ATAC/TE atlas. It uses accepted initial job 7466270 results plus the actual resolution-1 partitions and fresh marker summaries from job 7470007, verified in package job 7470531. It does not assign final identities, remove cells, change raw counts or infer genotype effects.

## Available now

- Real corrected and uncorrected initial ATAC UMAPs, with all 456,472 saved points. Coordinate files are loaded only on request, with no sampling, graph recomputation or raw CSR scan. Filter by initial cluster, genotype, age–genotype condition, animal and sex. Color by cluster/display label, condition, genotype, animal or sex; pan, zoom, inspect source-row metadata and export PDF.
- Activity dotplot builder over the **selected diagnostic 107-gene panel**. The five unmapped mitochondrial panel genes are NA, not evidence of absent activity. Choose canonical panels or type known panel gene symbols; split display groups by condition/genotype. Marker UMAP overlays are not included yet.
- Raw activity, saved normalized activity, or within-gene z-score colors. Dot **area** is proportional to the equal-animal nonzero-activity fraction. Mean raw display = per-animal activity sum / nuclei, then equal-animal mean. Saved normalized display = equal-animal mean of per-nucleus log1p(activity / full activity total × 10,000). Z-scores use the population SD across currently displayed group means and are recalculated when groups or filters change. Color saturation at ±2.5 does not truncate the exported numeric z-score.
- Descriptive selection of 20 panel genes with the largest activity difference for a chosen initial cluster. This is **not genome-wide marker discovery, DE or a statistical result**. The candidate panel cannot supply unbiased top markers for every final cell type.
- Animal points and descriptive condition boxplots. Biological replication is the animal, not individual nuclei. No p-values are attached.
- Initial composition by condition, with explicit per-condition initial-nucleus denominators.
- Editable display-only cluster labels, browser-local persistence and portable JSON export/import. Assigning the same display label combines plotted summaries: source clusters are nucleus-weighted within each animal first, then animals receive equal weight. It does not rewrite metadata or establish a biological annotation.
- All initial clusters selected by default. The extra microglia shortcut is limited to the independently reviewed initial corrected resolution-0.6 cluster 6; it is disabled in the other partitions, where the microglia marker panel can still be used across all clusters. Numeric cluster IDs are not cell identities across resolutions.
- Source/status panel, file hashes, exact download/coordinate provenance, producer PDF links, PDF figure and selected-value TSV exports.
- Verified **TE peak coordinate overlap** from accepted job **7471562**, with all 28 initial calibration cell-type groups and Microglia selected first. See the dedicated section below; these data are separate from gene-body activity and from pending TE expression/count-based accessibility analyses.

## TE overlap heatmaps and animal boxplots

Open `http://127.0.0.1:56404/full_workflow_20261014/atlas_preview/index.html#te-overlap`. Choose a cell-type group, native RepeatMasker class (`repClass`), family (`repFamily`, also called subclass in the interface) or subfamily (`repName`), sex, age scope, palette and absolute or within-category z-score heatmap. The default genotype comparison contains three-month WT, 5xFAD and APOE4/TREM2 animals; the all-condition view keeps 6- and 21-month WT separate. These controls are independent of the UMAP, Leiden partition and editable display labels.

Heatmap values are equal-animal means. Each boxplot point is one animal, with sex-specific shapes and explicit available/expected animal counts. Missing or empty peak-call groups remain NA; a valid observed zero remains zero. A missing genomic background produces NA for the fold metric without discarding a valid overlap fraction. The native TE categories can overlap one another, so their percentages need not sum to 100%. All 28 types and all taxonomy categories remain available; the extra Microglia figures do not select cells or exclude other types.

The primary metric is the fraction of blacklist-excluded callable peak-union bases overlapping the selected TE category. The optional descriptive fold uses a chromosome-weighted genomic reference; it is not a GC-, TSS- or mappability-matched enrichment test. These peak sets use **initial published calibration labels**, and their peak counts, widths and discovery depth vary. This view does not measure TE RNA expression, fragment-level accessibility, or a statistically established genotype effect.

Both interactive plot exports are **PDF only**, with vector marks, native legends, source, filters, units and limitations; larger heatmaps paginate. TSV exports preserve native taxonomy, animal identifiers, denominators and NA. The five prepared PDF reports include all-type class heatmaps plus additional Microglia class, family, subfamily and three-month animal comparisons. Top-20 family/subfamily selection is descriptive, not differential testing.

`te_overlap_import_provenance.actual.json` binds the accepted download, local JSON file hashes, independent numerical checks, protected original adapter bytes, real-browser filters and PDF downloads. `export_validation/TE_overlap/` contains actual exported PDFs, their validation and an atlas screenshot. The reproducible builder and independent reviews are in `work/TE_atlas_20261015/`; no raw matrix, BAM, new peak producer or remote job was run for this addition.

## Pending scientific outputs

Final reviewed QC retention and final labels, filtered RNA SCT/PCA/Harmony and ATAC embeddings, unbiased top 10–20 markers per reviewed type, RNA-to-ATAC transfer, cell-level feature UMAP overlays, TE expression/accessibility, animal-level gene/peak/TE differential results and gene/TE coverage tracks. These views are explicitly unavailable rather than populated with placeholder data.

Gene-body activity is accessibility, **not RNA expression**. RNA and ATAC nuclei are not barcode paired. The interface does not translate RNA cluster numbers into ATAC identities.

## Input/read scope

`build_provenance.actual.json` binds the small-table inputs and proves exact equal-animal summary parity. `coordinate_provenance.actual.json` records the bounded export of only `/obsm/X_umap_initial`, `/obsm/X_umap_initial_uncorrected` and the cell index from the already downloaded atlas. One metadata streaming pass verified every H5 cell ID in the exact saved row order. No `X/data`, `X/indices`, `X/indptr`, full AnnData object, raw matrix or LSI array was read; no large source-content hash was computed.

`core_tests.actual.json` contains aggregation/axis tests. Browser validation, when performed, is recorded separately; passing core tests alone does not claim a visual browser review.

The 440 identical duplicate panel rows were collapsed to 23,540 unique cluster × animal × gene records. All 11 clusters and 20 animals reconcile to 456,472 nuclei. The 107 symbols comprise 102 mapped genes and 5 unmapped genes. All original project files stay unchanged.

## Extending the atlas

See `adapter_contract.json`. Source-backed final outputs can replace/extend the versioned data adapters without conflating raw counts, SCT residuals, gene-body activity, TE expected-count sensitivity or coverage. Every new adapter must carry its provenance, axes, normalization/assignment semantics and provisional/final status. Pending views must stay unavailable until their actual outputs exist.

Build scripts and tests are in `work/final_multimodal_20261014/atlas_local_scaffold/` within the same project. The current HTML contains no bulk point arrays; data and lazy UMAP files are separate local assets. Chart.js is vendored with its license and SHA-256 fingerprint in `vendor/`.

## PDF figure exports

All visible plot save controls export PDF: UMAP, activity dotplot, animal comparison, condition composition, and TE heatmap/boxplot. PDFs include the plot, title, chosen filters, source job, units, provisional status, and export time. The original UMAP/activity/composition canvases are rendered at an increased pixel ratio (bounded at 9,000 pixels per dimension); those plotted images are raster within a PDF, with vector PDF header/context text. The TE heatmaps and boxplots instead use PDF-native vector marks and text. TSV/JSON exports remain for data and display mappings. jsPDF 4.2.1 is vendored locally with its MIT license; PDF creation uses no service or upload.

## Leiden resolutions

The resolution selector exposes **0.6** (job 7466270: 11 corrected / 9 uncorrected clusters) and **1.0** (job 7470007: 12 corrected / 12 uncorrected clusters). A separate **cluster partition graph** control chooses the actual corrected or uncorrected partition. **Coordinate embedding** is independent: both existing UMAP coordinate arrays remain unchanged, so changing the partition changes labels and marker summaries rather than recomputing UMAP.

Each resolution-1 branch uses its own fresh 107-gene activity summaries. Resolution-0.6 uncorrected labels and composition are available, but no independent activity summaries were produced for that partition: its activity dotplots, ranking and animal plots are explicitly unavailable. The corrected 0.6 means are never reused there.

Display-label browser storage and JSON import/export are isolated by dataset, resolution and partition graph. New resolution-1 candidates stay neutral and unreviewed. Every PDF and selected-value export identifies its active source, resolution and graph; figure export remains PDF only. Genotype filtering consistently uses canonical `APOE4/TREM2`, while the original animal and condition naming tokens are preserved.

`resolution1_import_provenance.actual.json` binds the exact package manifest SHA `07fb6736f0304ca87225dd8449a548a579072a4223092d2c2589ad58e288cc02`, the successful terminal review, all 47 verified downloaded files, and exact point-axis/label/animal/marker reconciliation. `resolution_selector_tests.actual.json` records the expanded four-partition data and UI-contract QA. The import reads small JSON/labels only, without raw matrix, graph, H5AD or producer execution. The package's verified adapter scripts are referenced in their sibling project directory, so keep the full project layout together for offline use.

### PDF legends

Dotplot PDFs include PDF-native color gradients with numeric endpoints (z-score ±2.5; actual selected mapped-value min/max for raw/normalized colors), 25%/50%/100% detection-area keys and an unmapped-NA cross key. The on-screen raw/normalized color scale uses the same selected-value min/max. UMAP PDFs include native UMAP1/UMAP2 labels and categorical swatches matching the selected color field/palette. The composition legend is inside its plot canvas; animal boxplot condition labels are inside the plot and its point/box interpretation is also included as PDF context. These additions are tested independently in `pdf_native_legend_tests.actual.json`; real browser visual checks are separate proof records.
