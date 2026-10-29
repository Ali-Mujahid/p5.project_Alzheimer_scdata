/* Interactive display of saved, mouse-level IRescue expression values. */
(() => {
  'use strict';
  const host = document.getElementById('irescue-scaled-boxplot');
  if (!host) return;
  const $ = selector => host.querySelector(selector), ns = 'http://www.w3.org/2000/svg';
  const target = $('[data-box-target]'), normalization = $('[data-box-normalization]'), scale = $('[data-box-scale]');
  const low = $('[data-box-control-color]'), high = $('[data-box-target-color]');
  const pointSize = $('[data-box-point-size]'), boxWidth = $('[data-box-width]');
  const plotWidth = $('[data-box-plot-width]'), plotHeight = $('[data-box-plot-height]');
  const status = $('[data-box-status]'), holder = $('[data-box-plot]');
  let records = null, svg = null;
  const el = (tag, attrs, content) => {
    const node = document.createElementNS(ns, tag);
    for (const [key, val] of Object.entries(attrs || {})) node.setAttribute(key, String(val));
    if (content !== undefined) node.textContent = content;
    return node;
  };
  function quantile(v, q) {
    const a = v.slice().sort((x, y) => x - y), x = (a.length - 1) * q;
    return a[Math.floor(x)] + (a[Math.ceil(x)] - a[Math.floor(x)]) * (x % 1);
  }
  function draw() {
    if (!records) return;
    const selected = records.filter(x => x.target === target.value);
    const expected = target.value === 'WT_21mo' ? 7 : 8;
    if (selected.length !== expected) throw new Error('Unexpected mouse count');
    const unscaled = selected.map(x => normalization.value === 'gene_depth' ? x.geneDepth : x.geneTMM);
    let values, yLabel;
    if (scale.value === 'cpm') {
      values = unscaled;
      yLabel = 'Normalized TE expression (per million gene UMIs)';
    } else {
      const logs = unscaled.map(x => Math.log2(1 + x));
      if (scale.value === 'log') {
        values = logs;
        yLabel = 'log₂(1 + normalized TE expression)';
      } else {
        const mean = logs.reduce((a, b) => a + b, 0) / logs.length;
        const sd = Math.sqrt(logs.reduce((a, b) => a + (b - mean) ** 2, 0) / logs.length);
        values = logs.map(x => sd > 0 ? (x - mean) / sd : 0);
        yLabel = 'Z-score of log₂(1 + normalized TE expression)';
      }
    }
    if (!values.every(Number.isFinite)) throw new Error('Invalid normalized values');
    const W = Number(plotWidth.value), H = Number(plotHeight.value), L = 100, R = 35, T = 75, B = 105;
    const min = Math.min(...values), max = Math.max(...values), padding = Math.max((max - min) * 0.18, 0.04);
    const lo = min - padding, hi = max + padding, y = v => H - B - (v - lo) / (hi - lo) * (H - T - B);
    svg = el('svg', {xmlns: ns, viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: 'img',
      'aria-label': 'IRescue mouse-level scaled TE expression boxplot', style: 'font-family:Arial,sans-serif;background:white;max-width:100%;height:auto'});
    svg.append(el('rect', {width: W, height: H, fill: 'white'}));
    svg.append(el('text', {x: W/2, y: 28, 'text-anchor': 'middle', 'font-size': 19}, `${target.value} vs WT_3mo`));
    svg.append(el('text', {x: W/2, y: 51, 'text-anchor': 'middle', 'font-size': 12}, `${normalization.value === 'gene_depth' ? 'Same-cell raw gene depth' : 'Gene-TMM effective depth'} · each point is one mouse`));
    for (let i=0; i<=4; i++) {
      const v = lo + (hi-lo)*i/4, yy = y(v);
      svg.append(el('line', {x1:L,x2:W-R,y1:yy,y2:yy,stroke:'#e3e8e6'}));
      svg.append(el('text',{x:L-10,y:yy+4,'text-anchor':'end','font-size':12},v.toLocaleString(undefined,{maximumFractionDigits:scale.value==='cpm'?0:2})));
    }
    if (scale.value === 'z' && lo <= 0 && hi >= 0) svg.append(el('line',{x1:L,x2:W-R,y1:y(0),y2:y(0),stroke:'#888','stroke-dasharray':'4 4'}));
    svg.append(el('line',{x1:L,x2:L,y1:T,y2:H-B,stroke:'#333'}));
    svg.append(el('line',{x1:L,x2:W-R,y1:H-B,y2:H-B,stroke:'#333'}));
    ['WT_3mo',target.value].forEach((group,index) => {
      const list = selected.map((r,i)=>({...r,value:values[i]})).filter(r=>r.group===group).sort((a,b)=>a.animal.localeCompare(b.animal));
      const arr = list.map(r=>r.value), cx = L + (index ? .75 : .25)*(W-L-R), bw = Number(boxWidth.value);
      const color = index ? high.value : low.value, mn = Math.min(...arr), mx = Math.max(...arr), q1 = quantile(arr,.25), q3 = quantile(arr,.75), med = quantile(arr,.5);
      svg.append(el('line',{x1:cx,x2:cx,y1:y(mn),y2:y(mx),stroke:'#333','stroke-width':2}));
      for (const v of [mn,mx]) svg.append(el('line',{x1:cx-bw*.25,x2:cx+bw*.25,y1:y(v),y2:y(v),stroke:'#333','stroke-width':2}));
      svg.append(el('rect',{x:cx-bw/2,y:y(q3),width:bw,height:Math.max(1,y(q1)-y(q3)),fill:color,'fill-opacity':.28,stroke:color,'stroke-width':2}));
      svg.append(el('line',{x1:cx-bw/2,x2:cx+bw/2,y1:y(med),y2:y(med),stroke:'#222','stroke-width':3}));
      list.forEach((r,i)=>{
        const px=cx+(i-(list.length-1)/2)*Math.min(12,bw/(list.length+1)), py=y(r.value), rad=Number(pointSize.value);
        const node = r.sex==='male' ? el('path',{d:`M ${px} ${py-rad} L ${px+rad} ${py+rad} L ${px-rad} ${py+rad} Z`,fill:color,stroke:'white'}) : el('circle',{cx:px,cy:py,r:rad,fill:color,stroke:'white'});
        node.append(el('title',{},`${r.animal}: ${r.value.toFixed(3)}; ${yLabel}`));svg.append(node);
      });
      svg.append(el('text',{x:cx,y:H-B+26,'text-anchor':'middle','font-size':15},`${group} (n=${list.length})`));
    });
    svg.append(el('text',{transform:`translate(22 ${H/2}) rotate(-90)`,'text-anchor':'middle','font-size':13},yLabel));
    svg.append(el('text',{x:W/2,y:H-23,'text-anchor':'middle','font-size':12},'Female: circle · male: triangle · descriptive mouse-level values'));
    holder.replaceChildren(svg);
    status.textContent = `${target.value}: ${expected} mice. ${normalization.value === 'gene_depth' ? 'Raw gene depth from the same nuclei' : 'Gene-TMM effective depth'}; ${scale.value === 'z' ? 'z-scores calculated across all mice in this comparison from log-normalized values' : scale.value === 'log' ? 'log₂ normalized values' : 'normalized values'}. ${target.value === 'WT_21mo' ? 'WT_21mo_female_1 excluded only here. ' : ''}Colors and sizes change display only.`;
  }
  for (const n of [target,normalization,scale,low,high,pointSize,boxWidth,plotWidth,plotHeight]) n.addEventListener('input',draw);
  $('[data-box-pdf]').addEventListener('click',async()=>{
    if (!svg || !window.jspdf?.jsPDF) {status.textContent='PDF export unavailable; use the static PDF link below.';return;}
    try {
      const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml;charset=utf-8'}));
      const img=new Image();await new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=reject;img.src=url;});
      const vb=svg.viewBox.baseVal,c=document.createElement('canvas');c.width=vb.width*2;c.height=vb.height*2;
      const ctx=c.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,c.width,c.height);ctx.drawImage(img,0,0,c.width,c.height);URL.revokeObjectURL(url);
      const doc=new window.jspdf.jsPDF({orientation:vb.width>=vb.height?'landscape':'portrait',unit:'mm',format:[vb.width/4,vb.height/4]});
      doc.addImage(c.toDataURL('image/png'),'PNG',0,0,vb.width/4,vb.height/4);doc.save(`IRescue_${target.value}_${normalization.value}_${scale.value}_boxplot.pdf`);
    } catch (e) {status.textContent=`PDF export failed: ${e.message}. Use the static PDF link below.`;}
  });
  Promise.all([fetch('downloads/four_comparisons_raw_matched_gene_depth_mouse_values.tsv'),fetch('data/irescue_microglia_locus.json?v=WT21_7mice')])
    .then(async rs=>{if(rs.some(r=>!r.ok))throw new Error('Required mouse values unavailable');return [await rs[0].text(),await rs[1].json()];})
    .then(([text,data])=>{
      const lines=text.trim().split(/\r?\n/),fields=lines.shift().split('\t');
      const mapping=new Map(data.mouse_expression.filter(x=>x.method==='IRescue').map(x=>[`${x.target}|${x.animal}`,x]));
      records=lines.map(line=>{
        const vals=line.split('\t'),r=Object.fromEntries(fields.map((key,i)=>[key,vals[i]]));
        const tmm=mapping.get(`${r.target}|${r.animal}`);if(!tmm || tmm.group!==r.group || tmm.sex!==r.sex)throw new Error('Mouse identity mismatch');
        return {target:r.target,animal:r.animal,group:r.group,sex:r.sex,geneDepth:Number(r.TE_per_million_matched_gene_UMIs),geneTMM:Number(tmm.set_count_per_million_gene_UMIs)};
      });
      if(records.length!==31 || new Set(records.map(r=>`${r.target}|${r.animal}`)).size!==31)throw new Error('Incomplete or duplicated mouse values');
      draw();
    }).catch(e=>{status.textContent=`Interactive boxplot could not load: ${e.message}. Use the static PDF below.`;});
})();
