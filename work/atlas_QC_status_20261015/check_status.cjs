/* Render the real adapter using a minimal text DOM; no browser or science reads. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const base = path.resolve('outputs/p5_workflow/full_workflow_20261014/atlas_preview');
const status = JSON.parse(fs.readFileSync(path.join(base, 'qc_status.json')));
class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.dataset = {}; this.textContent = ''; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  setAttribute() {}
  get text() { return this.textContent + this.children.map(x => x.text).join(' '); }
}
async function render(data, ok=true) {
  const host = new Element('host');
  const document = {
    getElementById: name => name === 'qcProgressApp' ? host : null,
    createElement: tag => new Element(tag),
    createTextNode: text => { const x = new Element('text'); x.textContent = text; return x; }
  };
  const run = vm.runInNewContext(fs.readFileSync(path.join(base, 'qc_status.js'), 'utf8'), {
    document, fetch: async () => ({ok, status: ok ? 200 : 404, json: async () => data}), Date
  });
  await run;
  return host;
}
(async () => {
  const real = await render(status);
  assert.equal(real.dataset.loaded, 'true');
  for (const text of ['192 / 192 libraries', `${status.atac.accepted_completed} / 104 complete`,
    `${status.atac.running} running`, `${status.atac.pending} queued`,
    'array 7472294', '2 pending', '0 started receipts', '119 checks passed',
    '1,469,390 / 2,318,796', '6,995 unresolved flags',
    'not singlet certification', new Date(status.atac.observed_utc).toISOString().slice(0,19).replace('T',' ') + ' UTC']) {
    assert.ok(real.text.includes(text), 'Missing source-backed text: ' + text);
  }
  assert.ok(!real.text.includes('Full QC complete'));
  const badSchema = await render({...status, normalization_ready:true});
  assert.equal(badSchema.dataset.loaded, 'error');
  assert.ok(badSchema.text.includes('QC progress unavailable'));
  assert.ok(!badSchema.text.includes(`${status.atac.accepted_completed} / 104`));
  const missing = await render(status, false);
  assert.equal(missing.dataset.loaded, 'error');
  assert.ok(missing.text.includes('HTTP 404'));
  console.log(JSON.stringify({status:'passed_QC_status_render_and_failure_paths', checks:19,
    source_snapshot_utc:status.atac.observed_utc, no_browser_or_study_matrix_read:true}));
})().catch(err => { console.error(err); process.exitCode=1; });
