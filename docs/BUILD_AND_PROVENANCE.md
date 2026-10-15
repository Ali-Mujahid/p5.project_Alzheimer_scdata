# GSE212606 mouse RNA / ATAC / TE atlas

This repository preserves the current working atlas, its accepted display data, linked PDF reports, build/validation scripts and source-bound provenance. It is a **provisional research explorer**, not a completed final filtered atlas. All supported cell types and unknown/rare populations remain in scope; Microglia has additional views.

## Open the atlas on another computer

Clone or download this public repository. From the repository root, use Python 3.10 or newer:

```bash
python3 start_atlas.py --open
```

Then open:

<http://127.0.0.1:56404/full_workflow_20261014/atlas_preview/index.html#qc-progress>

The launcher verifies and restores the included archive parts before serving `outputs/p5_workflow` as the HTTP document root. The existing app loads a sibling resolution-1 package and links sibling producer reports; TE report links start at the server root. Opening `index.html` with a `file:` URL does not support lazy JSON loading.

The ready-to-view copy needs a modern browser and a local HTTP server. It does not need LiSC, Slurm, R, raw BAM/FASTQ, Python scientific packages, npm packages, a CDN, or Internet after download. Plot save buttons produce PDF; TSV/JSON exports remain available. Running this server does not submit processing jobs or change source data.

The local address works only while the server runs on that computer. A GitHub backup is not itself an always-online hosted atlas; use this saved copy on any computer. Live web hosting has not been enabled by this backup.

## What is present

- Current HTML/CSS/JavaScript application, complete initial ATAC UMAP coordinates and point attributes, actual Leiden 0.6 / 1.0 partitions, and the resolution-specific diagnostic activity summaries.
- TE coordinate-overlap adapters for all 28 initial calibration cell-type groups, heatmaps, animal boxplots, linked PDF reports and the aggregate source tables used to generate these views.
- Dated, source-bound QC progress, accepted candidate RNA QC reports, and the one-library SCT technical profile. A progress snapshot is not a promise of the present scheduler state.
- Offline vendored Chart.js 4.5.1 and jsPDF 4.2.1 with their MIT license notices.
- Original local adapter builders and validators, selected upstream scientific algorithm source and original source manifests, all in the original `work/` and `outputs/` layout.
- SHA-256/byte inventory and provenance records. These identify copied bytes; a report containing an older hash remains historical provenance, not an assertion that a later adapter is unchanged.

## Source and optional rebuilds

The generated static atlas is already usable. Original builders are preserved for reproducibility and inspection:

- `work/final_multimodal_20261014/atlas_local_scaffold/`: initial table adapter, bounded coordinate extraction, resolution import, and JavaScript tests.
- `work/TE_atlas_20261015/`: TE adapter and descriptive PDF plots, numerical/adapter/PDF review sources.
- `work/atlas_QC_status_20261015/`: strict dated status adapter and tests.

Historical originals contain either the original Mac project path or assumptions about directory depth. They are archival originals. Any portable variants should resolve the repository root from their own file location and be clearly distinguished from the SHA-bound originals. Do not reapply `update_resolution_ui.py` to the finished UI: it is a historical one-use source transformation. Do not routinely execute `finalize_atlas_import.py`: besides provenance it updates the broader project's status/automation argument documents. Viewing and validating the saved site does not require either script.

Optional local rebuild dependencies are Python `numpy`, `pandas`, `matplotlib`, plus `h5py` only to re-extract existing H5AD coordinates and `pypdf` for PDF text checks. The catalog records observed local versions where installed; this does not certify every future package combination. Runtime Node tests use Node's built-in `fs`, `path`, `vm`, `assert` and `crypto` modules, plus the included jsPDF bundle. No npm install is required.

The 1.63 GB clustered raw-peak H5AD is deliberately excluded because the app uses the accepted exported coordinates, labels and summaries already included. Re-extracting coordinates would additionally require that separately preserved accepted H5AD and its original download identity. The atlas does not need its raw CSR matrix. Original biological processing requires its own external raw inputs, compute environment, quotas, frozen source and scheduler gates; the archived algorithm sources are not an automatically runnable cluster workflow.

## Scientific limits

Activity values are **gene-body accessibility**, not RNA expression. The 107-gene diagnostic panel is not unbiased genome-wide marker discovery. Initial candidate labels and published peak-discovery calibration groups are provisional; equal numeric cluster IDs across resolutions or RNA/ATAC are not identities. RNA and ATAC nuclei are not barcode paired.

TE views measure descriptive genomic peak-coordinate overlap, not TE RNA expression, per-cell fragment accessibility, matched-background enrichment or a significant genotype effect. Empty/absent groups remain NA, valid zero remains zero, age-matched disease comparisons keep older WT separate, and plotted animals are biological replicates. Full reviewed retention, final RNA/ATAC normalization/labels, count-based TE inference and coverage tracks remain unavailable until actual accepted analyses exist.

## Excluded from the portable atlas

Credentials, authentication sockets, account configuration, one-use remote dispatch payloads and submission launchers are excluded. Raw BAM/FASTQ and the large H5AD are excluded. Individual peak TE annotation files not read by the app/builders are not needed for the portable explorer; the accepted aggregate source tables and all display adapters are retained. No processing job was run to create this backup.

## Licenses

The retained vendor notices apply to Chart.js and jsPDF. Scientific Python packages are optional installed dependencies and retain their own licenses. No project-wide license was present in the source workspace, so this archive does not assign a new license or relicense original code/data.


## Complete archival source update

All42members of the four frozen producer source manifests, including the four originalSlurm wrappers, are included. Earlier inventory text about wrapper omission is superseded by this completeness check. Nothing in the launcher invokes an HPC job.
