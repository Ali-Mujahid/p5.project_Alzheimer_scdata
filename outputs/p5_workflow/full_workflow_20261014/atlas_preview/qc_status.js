'use strict';
/* Independent status adapter: it does not change scientific filters or data. */
(async function () {
  const host = document.getElementById('qcProgressApp');
  if (!host) return;
  const el = (tag, text, cls) => {
    const item = document.createElement(tag);
    if (text !== undefined) item.textContent = text;
    if (cls) item.className = cls;
    return item;
  };
  const fmt = value => Number(value).toLocaleString('en-US');
  const when = value => new Date(value).toISOString().replace('T', ' ').replace(/\.\d+Z$/, ' UTC');
  const card = (title, metric, description) => {
    const box = el('div');
    box.append(el('b', title), el('strong', metric, 'qc-metric'), el('p', description));
    return box;
  };
  const link = (href, label) => {
    const a = el('a', label); a.href = href; return a;
  };
  try {
    const response = await fetch('qc_status.json', {cache: 'no-store'});
    if (!response.ok) throw new Error('HTTP ' + response.status);
    const d = await response.json();
    if (d.schema_version !== 1 || d.full_QC_complete !== false || d.normalization_ready !== false) {
      throw new Error('Status adapter needs a reviewed schema update');
    }
    const heading = el('div', undefined, 'sectionhead');
    const title = el('div');
    title.append(el('p', 'QC / VERIFIED PROGRESS', 'eyebrow'), el('h2', 'QC and normalization progress'));
    heading.append(title, el('span', 'Full QC still in progress', 'qc-badge'));
    const grid = el('div', undefined, 'statusgrid qc-summary');
    grid.append(
      card('RNA candidate QC', `${d.rna.completed_libraries} / ${d.rna.total_libraries} libraries`,
        `${fmt(d.rna.candidate_cells)} candidate nuclei. Final retention remains under review.`),
      card('ATAC candidate QC', `${d.atac.accepted_completed} / ${d.atac.total_libraries} complete`,
        `${d.atac.running} running · ${d.atac.pending} queued · ${d.atac.failed_attempts} failed prior attempts.`),
      card('SCT technical profile', `${d.sct_technical_profile.independent_checks_passed} checks passed`,
        `One library (${d.sct_technical_profile.library_id}); not final study normalization.`)
    );
    const note = el('p', 'Dated snapshots below are independent of the initial-atlas filters above. Queue changes are shown only after a new verified observation.', 'hint');
    const tablewrap = el('div', undefined, 'tablewrap');
    const table = el('table'); table.setAttribute('aria-label', 'QC stage observations and evidence');
    const thead = el('thead'), hr = el('tr');
    ['Stage', 'Verified state', 'Evidence time (UTC)'].forEach(h => hr.append(el('th', h)));
    thead.append(hr); const tbody = el('tbody');
    const row = (stage, state, timestamp) => {
      const tr = el('tr'); [stage, state, timestamp].forEach(v => tr.append(el('td', v))); tbody.append(tr);
    };
    row('RNA review · job ' + d.rna.job_id,
      `${fmt(d.rna.doublet_unresolved_basic)} / ${fmt(d.rna.basic_supported_cells)} basic-supported nuclei have unresolved doublet models; ${d.rna.libraries_without_automatic_mt_threshold} libraries have no automatic mitochondrial threshold.`,
      when(d.rna.accepted_utc) + ' · accepted');
    row('ATAC array ' + d.atac.array_id,
      `${d.atac.accepted_completed} accepted completions, ${d.atac.running} running, ${d.atac.pending} queued. Tasks ${d.atac.failed_tasks.join(' and ')} failed before study processing.`,
      when(d.atac.observed_utc));
    const r = d.atac.new_recovery;
    const queues = Object.entries(r.queue_counts).map(([state, n]) => `${n} ${state.toLowerCase()}`).join(', ');
    row('Separate repair · array ' + r.array_id,
      `Tasks ${r.tasks.join(' and ')} only: ${queues || 'see accounting'}. ${r.started_receipts} started receipts; ${r.accepted_completed} accepted completions. Submitted by ${r.submitter}; allocated guard tests precede QC.`,
      when(r.observed_utc));
    row('SCT profile · job ' + d.sct_technical_profile.job_id,
      `${fmt(d.sct_technical_profile.candidate_cells)} provisional nuclei, including ${fmt(d.sct_technical_profile.unresolved_candidate_cells)} unresolved flags; ${fmt(d.sct_technical_profile.fitted_gene_models)} gene models and ${fmt(d.sct_technical_profile.candidate_HVG_count)} candidate features.`,
      when(d.sct_technical_profile.accepted_utc) + ' · accepted');
    row('Full-296 reconciliation' + (d.gather.job_id ? ' · job ' + d.gather.job_id : ''),
      d.gather.status,
      d.gather.observed_utc ? when(d.gather.observed_utc) + ' · observed' :
        d.gather.submitted_utc ? when(d.gather.submitted_utc) + ' · submitted' : 'Pending submission');
    table.append(thead, tbody); tablewrap.append(table);
    const caution = el('div', undefined, 'notice small qc-caution');
    caution.append(el('strong', 'Final retained cells and final normalized RNA values are unavailable. '),
      document.createTextNode('Candidate QC is not singlet certification. Failed attempts remain FAILED in their original accounting. Full reconciliation and documented retention decisions must pass before production normalization and new final embeddings. All cell types and unknown candidates remain in scope.'));
    const links = el('div', undefined, 'linkrow');
    links.append(link(d.rna.report_pdf, 'RNA animal QC report · PDF ↗'),
      link(d.rna.library_tsv, 'RNA library QC · TSV ↗'),
      link(d.rna.review_json, 'RNA unresolved-QC review · JSON ↗'),
      link(d.sct_technical_profile.profile_json, 'SCT technical profile ↗'),
      link(d.sct_technical_profile.candidate_features_tsv, 'Single-library candidate features · TSV ↗'),
      link('qc_status.json', 'Dated status · JSON ↗'),
      link('qc_status_import_provenance.actual.json', 'QC status source proof ↗'));
    host.replaceChildren(heading, grid, note, tablewrap, caution, links);
    host.dataset.loaded = 'true';
  } catch (error) {
    host.replaceChildren(el('h2', 'QC progress unavailable'),
      el('p', 'The dated QC status could not be loaded. Existing atlas views remain available. ' + error.message, 'hint'));
    host.dataset.loaded = 'error';
  }
}());
