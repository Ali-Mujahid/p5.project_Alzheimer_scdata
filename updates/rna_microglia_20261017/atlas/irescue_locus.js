/* Completed RNA data only. Display controls never change count matrices or primary method. */
(() => {
  'use strict';
  const host = document.getElementById('irescue-locus-explorer');
  if (!host) return;
  const S = 'http://www.w3.org/2000/svg';
  const select = host.querySelector('[data-ir-target]');
  const method = host.querySelector('[data-ir-method]');
  const measure = host.querySelector('[data-ir-measure]');
  const controlColor = host.querySelector('[data-ir-control-color]');
  const targetColor = host.querySelector('[data-ir-target-color]');
  const radius = host.querySelector('[data-ir-radius]');
  const status = host.querySelector('[data-ir-status]');
  const frame = host.querySelector('[data-ir-plot]');
  let data = null, svg = null;
  function el(name, props, text) {
    const n = document.createElementNS(S, name);
    Object.entries(props || {}).forEach(([k, v]) => n.setAttribute(k, String(v)));
    if (text !== undefined) n.textContent = text;
    return n;
  }
  const q = (xs, p) => {
    const a = xs.slice().sort((x, y) => x - y), x = (a.length - 1) * p;
    return a[Math.floor(x)] + (a[Math.ceil(x)] - a[Math.floor(x)]) * (x % 1);
  };
  function value(r) {
    if (measure.value === 'raw') return r.raw_set_count;
    if (measure.value === 'cpm') return r.set_count_per_million_gene_UMIs;
    if (measure.value === 'z') {
      const a = data.mouse_expression.filter(x => x.target === r.target && x.method === r.method).map(x => x.set_count_per_million_gene_UMIs);
      const mean = a.reduce((s, x) => s + x, 0) / a.length;
      const sd = Math.sqrt(a.reduce((s, x) => s + (x - mean) ** 2, 0) / a.length);
      return sd ? (r.set_count_per_million_gene_UMIs - mean) / sd : 0;
    }
    return r.log2_1plus_gene_normalized_set_expression;
  }
  function redraw() {
    if (!data) return;
    const target = select.value;
    const ms = method.value === 'Both' ? ['IRescue', 'Stellarscope'] : [method.value];
    const rows = data.mouse_expression.filter(r => r.target === target && ms.includes(r.method));
    const bins = ms.flatMap(m => ['WT_3mo', target].map(g => ({method: m, group: g,
      rows: rows.filter(r => r.method === m && r.group === g)})));
    if (!bins.every(b => b.rows.length === ((target === 'WT_21mo' && b.method === 'IRescue' && b.group === target) ? 3 : 4))) throw new Error('Unexpected mouse replicate count.');
    const W = 1100, H = 620, left = 110, right = 35, top = 92, bottom = 150;
    const max = Math.max(...rows.map(value)), min = Math.min(...rows.map(value));
    const padding = Math.max((max - min) * .2, max * .025, .05);
    const lo = measure.value === 'z' ? min - padding : Math.max(0, min - padding), hi = max + padding;
    const y = v => H - bottom - (v - lo) / (hi - lo) * (H - bottom - top);
    const x = i => left + (i + .5) / bins.length * (W - left - right);
    svg = el('svg', {xmlns: S, viewBox: `0 0 ${W} ${H}`, width: W, height: H,
      role: 'img', 'aria-label': 'Mouse-level RNA TE expression for the same fixed TE loci',
      style: 'font-family:Arial,sans-serif;max-width:100%;height:auto;background:white;color:#173c38'});
    svg.append(el('rect', {width: W, height: H, fill: 'white'}));
    svg.append(el('text', {x: W / 2, y: 31, 'text-anchor': 'middle', 'font-size': 23, fill: '#173c38'},
      `${target}: RNA signal at the same ${bins[0].rows[0].TE_loci.toLocaleString()} TE loci`));
    svg.append(el('text', {x: W / 2, y: 59, 'text-anchor': 'middle', 'font-size': 15, fill: '#455c59'},
      'IRescue is primary; Stellarscope is a separate comparison. Each point is one mouse.'));
    for (let i = 0; i <= 5; i++) {
      const v = lo + (hi - lo) * i / 5, yy = y(v);
      svg.append(el('line', {x1: left, x2: W - right, y1: yy, y2: yy, stroke: '#e0e7e5'}));
      svg.append(el('text', {x: left - 12, y: yy + 5, 'text-anchor': 'end', 'font-size': 14},
        v.toLocaleString(undefined, {maximumFractionDigits: ['log', 'z'].includes(measure.value) ? 2 : 1})));
    }
    svg.append(el('line', {x1: left, x2: left, y1: top, y2: H - bottom, stroke: '#173c38'}));
    svg.append(el('line', {x1: left, x2: W - right, y1: H - bottom, y2: H - bottom, stroke: '#173c38'}));
    bins.forEach((b, i) => {
      const xx = x(i), vals = b.rows.map(value), c = b.group === 'WT_3mo' ? controlColor.value : targetColor.value;
      const a = Math.min(...vals), d = Math.max(...vals), q1 = q(vals, .25), q3 = q(vals, .75), med = q(vals, .5);
      svg.append(el('line', {x1: xx, x2: xx, y1: y(a), y2: y(d), stroke: '#333', 'stroke-width': 2}));
      [a, d].forEach(v => svg.append(el('line', {x1: xx - 22, x2: xx + 22, y1: y(v), y2: y(v), stroke: '#333', 'stroke-width': 2})));
      svg.append(el('rect', {x: xx - 45, y: y(q3), width: 90, height: Math.max(1, y(q1) - y(q3)),
        fill: c, 'fill-opacity': .28, stroke: c, 'stroke-width': 2}));
      svg.append(el('line', {x1: xx - 45, x2: xx + 45, y1: y(med), y2: y(med), stroke: '#222', 'stroke-width': 3}));
      b.rows.forEach((r, j) => {
        const px = xx + (j - (b.rows.length - 1) / 2) * 10, py = y(value(r)), rr = Number(radius.value);
        const n = r.sex === 'male' ? el('path', {d: `M ${px} ${py - rr} L ${px + rr} ${py + rr} L ${px - rr} ${py + rr} Z`, fill: c, stroke: 'white'})
          : el('circle', {cx: px, cy: py, r: rr, fill: c, stroke: 'white'});
        n.append(el('title', {}, `${r.animal}; ${r.method}; raw=${r.raw_set_count}; gene-normalized=${r.set_count_per_million_gene_UMIs}`));
        svg.append(n);
      });
      svg.append(el('text', {x: xx, y: H - bottom + 26, 'text-anchor': 'middle', 'font-size': 16}, b.group));
      svg.append(el('text', {x: xx, y: H - bottom + 51, 'text-anchor': 'middle', 'font-size': 14},
        b.method === 'IRescue' ? 'IRescue — primary' : 'Stellarscope — comparison'));
    });
    const labels = {raw: 'Raw RNA set counts: expected UMIs (IRescue) / assigned UMIs (Stellarscope)',
      cpm: 'RNA set counts per million gene UMIs, using fixed gene-derived TMM exposure',
      log: 'log₂(1 + RNA set counts per million gene UMIs); fixed gene-derived TMM exposure',
      z: 'Z-score of gene-normalized set expression; centered separately within each method across each method’s displayed mice'};
    svg.append(el('text', {x: W / 2, y: H - 43, 'text-anchor': 'middle', 'font-size': 15}, labels[measure.value]));
    svg.append(el('text', {x: W / 2, y: H - 17, 'text-anchor': 'middle', 'font-size': 13, fill: '#526863'},
      target === 'WT_21mo' ? 'WT_21mo IRescue: 3 target / 4 control mice; Stellarscope: original 4 / 4. Female: circle · male: triangle.' : 'Female: circle · male: triangle · n=4 per group · descriptive, no significance claim'));
    frame.replaceChildren(svg);
    const matrix = data.matrices.find(r => r.target === target);
    host.querySelector('[data-ir-matrix]').href = 'downloads/' + matrix.file;
    status.textContent = `${matrix.rows.toLocaleString()} TE rows, including zeros; ` + (target === 'WT_21mo' ? 'IRescue uses four controls and three WT_21mo mice (female 1 excluded); Stellarscope retains its historical four-per-group data. ' : 'four control and four target mice. ') +
      'IRescue values are fractional expected allocations. Display controls do not alter the downloadable counts.';
  }
  [select, method, measure, controlColor, targetColor, radius].forEach(n => n.addEventListener('input', redraw));
  host.querySelector('[data-ir-pdf]').addEventListener('click', async () => {
    if (!svg || !window.jspdf?.jsPDF) {status.textContent = 'PDF export is unavailable; use the checked PDF links below.';return;}
    try {
      const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)], {type: 'image/svg+xml;charset=utf-8'}));
      const img = new Image();await new Promise((resolve, reject) => {img.onload = resolve;img.onerror = reject;img.src = url;});
      const canvas = document.createElement('canvas');canvas.width = 3300;canvas.height = 1860;
      const ctx = canvas.getContext('2d');ctx.fillStyle = 'white';ctx.fillRect(0, 0, canvas.width, canvas.height);ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      const pdf = new window.jspdf.jsPDF({orientation: 'landscape', unit: 'mm', format: 'a4'});
      pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 8, 12, 281, 158.38);
      pdf.setFontSize(9);pdf.text('GSE212606; selected Microglia. Same TE loci and mice in both conditions. IRescue primary; methods kept separate.', 9, 183);
      pdf.save(`Microglia_TE_RNA_${select.value}_${method.value}_${measure.value}.pdf`);
    } catch (e) {status.textContent = 'PDF export failed: ' + e.message + '. Checked PDF downloads remain available.';}
  });
  fetch('data/irescue_microglia_locus.json?v=WT21_7mice').then(r => {if (!r.ok) throw new Error(`HTTP ${r.status}`);return r.json();}).then(v => {
    if (v.status !== 'completed_checked' || v.animals !== 20 || v.Microglia_cells !== 22251) throw new Error('Completed 20-mouse data required.');
    data = v;select.replaceChildren(...v.matrices.map(r => {const n = document.createElement('option');n.value = r.target;n.textContent = r.target;return n;}));redraw();
  }).catch(e => {status.textContent = 'Interactive RNA data could not load: ' + e.message + '. Use the checked matrix and PDF links below.';});
})();
