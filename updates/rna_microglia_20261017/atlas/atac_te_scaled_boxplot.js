/* Interactive display of saved, mouse-level ATAC coverage values. */
(() => {
  'use strict';
  const host = document.getElementById('atac-te-scaled-boxplot');
  if (!host) return;
  const $ = selector => host.querySelector(selector), ns = 'http://www.w3.org/2000/svg';
  const target = $('[data-box-target]'), normalization = $('[data-box-normalization]'), scale = $('[data-box-scale]');
  const low = $('[data-box-control-color]'), high = $('[data-box-target-color]');
  const pointSize = $('[data-box-point-size]'), boxWidth = $('[data-box-width]');
  const plotWidth = $('[data-box-plot-width]'), plotHeight = $('[data-box-plot-height]');
  const showPoints = $('[data-box-show-points]'), showTests = $('[data-box-show-tests]');
  const targets = ['WT_6mo', 'WT_21mo', '5xFAD_3mo', 'APOE4_TREM2_3mo'];
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
  // Two-sided exact permutation distribution of the Wilcoxon rank sum; average ranks handle ties.
  function rankTest(values, controlSize) {
    const ordered = values.map((v,i)=>({v,i})).sort((a,b)=>a.v-b.v), ranks=Array(values.length);
    for (let i=0;i<ordered.length;) {let j=i+1;while(j<ordered.length && ordered[j].v===ordered[i].v) j++;const rank=(i+1+j)/2;for(let k=i;k<j;k++)ranks[ordered[k].i]=rank;i=j;}
    const center=controlSize*(values.length+1)/2, observed=Math.abs(ranks.slice(0,controlSize).reduce((a,b)=>a+b,0)-center);
    let total=0, extreme=0;
    function enumerate(i,n,sum){if(n===0){total++;if(Math.abs(sum-center)+1e-10>=observed)extreme++;return;}for(let j=i;j<=ranks.length-n;j++)enumerate(j+1,n-1,sum+ranks[j]);}
    enumerate(0,controlSize,0);return extreme/total;
  }
  function comparison(name) {
    const selected=records.filter(x=>x.target===name), expected=name==='WT_21mo'?7:8;
    if(selected.length!==expected)throw new Error('Unexpected mouse count');
    const raw=selected.map(x=>x.signal);
    const logs=raw.map(x=>Math.log2(1+x)),mean=logs.reduce((a,b)=>a+b,0)/logs.length;
    const sd=Math.sqrt(logs.reduce((a,b)=>a+(b-mean)**2,0)/logs.length);
    const values=scale.value==='cpm'?raw:scale.value==='log'?logs:logs.map(x=>sd>0?(x-mean)/sd:0);
    if(!values.every(Number.isFinite))throw new Error('Invalid normalized values');
    const rows=selected.map((r,i)=>({...r,value:values[i]}));
    const control=rows.filter(r=>r.group==='WT_3mo').sort((a,b)=>a.animal.localeCompare(b.animal));
    const treated=rows.filter(r=>r.group===name).sort((a,b)=>a.animal.localeCompare(b.animal));
    if(control.length!==4||treated.length!==expected-4)throw new Error('Unexpected groups');
    return {name,control,treated,p:rankTest([...control,...treated].map(x=>x.value),control.length)};
  }
  function draw() {
    if(!records)return;
    const all=targets.map(comparison), ranked=all.map((x,i)=>({p:x.p,i})).sort((a,b)=>a.p-b.p);
    let q=1;for(let i=ranked.length-1;i>=0;i--){q=Math.min(q,ranked[i].p*ranked.length/(i+1));all[ranked[i].i].q=q;}
    const panels=target.value==='all'?all:all.filter(x=>x.name===target.value);
    const yLabel=scale.value==='cpm'?'Relative mean TE-body ATAC signal':scale.value==='log'?'log₂(1 + relative TE-body ATAC signal)':'Z-score of log₂(1 + relative TE-body ATAC signal)';
    const W=Math.max(Number(plotWidth.value),panels.length===4?1000:0), H=Number(plotHeight.value), L=100,R=35,T=80,B=120;
    const values=panels.flatMap(p=>[...p.control,...p.treated].map(x=>x.value)), min=Math.min(...values),max=Math.max(...values),spread=Math.max(max-min,0.2);
    const lo=min-spread*.16,hi=max+spread*(showTests.checked?.42:.18),y=v=>H-B-(v-lo)/(hi-lo)*(H-T-B);
    svg=el('svg',{xmlns:ns,viewBox:`0 0 ${W} ${H}`,width:W,height:H,role:'img','aria-label':'Mouse-level TE-body ATAC accessibility boxplots',style:'font-family:Arial,sans-serif;background:white;max-width:100%;height:auto'});
    svg.append(el('rect',{width:W,height:H,fill:'white'}));
    svg.append(el('text',{x:W/2,y:27,'text-anchor':'middle','font-size':18},panels.length===4?'Four target-specific TE sets · each compared with WT_3mo':`${panels[0].name} vs WT_3mo`));
    svg.append(el('text',{x:W/2,y:49,'text-anchor':'middle','font-size':12},`Relative per-mouse ATAC signal · ${panels.length===4?'each pair uses a different TE set':'same TE set for both groups'}`));
    for(let i=0;i<=4;i++){const v=lo+(hi-lo)*i/4,yy=y(v);svg.append(el('line',{x1:L,x2:W-R,y1:yy,y2:yy,stroke:'#e3e8e6'}));svg.append(el('text',{x:L-10,y:yy+4,'text-anchor':'end','font-size':12},v.toLocaleString(undefined,{maximumFractionDigits:2})));}
    if(scale.value==='z'&&lo<=0&&hi>=0)svg.append(el('line',{x1:L,x2:W-R,y1:y(0),y2:y(0),stroke:'#888','stroke-dasharray':'4 4'}));
    svg.append(el('line',{x1:L,x2:L,y1:T,y2:H-B,stroke:'#333'}));svg.append(el('line',{x1:L,x2:W-R,y1:H-B,y2:H-B,stroke:'#333'}));
    const groupW=(W-L-R)/panels.length;
    panels.forEach((panel,pidx)=>{
      const center=L+(pidx+.5)*groupW, boxCenters=[center-groupW*.23,center+groupW*.23],bw=Math.min(Number(boxWidth.value),groupW*.35);
      [panel.control,panel.treated].forEach((list,idx)=>{
        const arr=list.map(r=>r.value),cx=boxCenters[idx],color=idx?high.value:low.value,mn=Math.min(...arr),mx=Math.max(...arr),q1=quantile(arr,.25),q3=quantile(arr,.75),med=quantile(arr,.5);
        svg.append(el('line',{x1:cx,x2:cx,y1:y(mn),y2:y(mx),stroke:'#333','stroke-width':2}));
        for(const v of [mn,mx])svg.append(el('line',{x1:cx-bw*.25,x2:cx+bw*.25,y1:y(v),y2:y(v),stroke:'#333','stroke-width':2}));
        svg.append(el('rect',{x:cx-bw/2,y:y(q3),width:bw,height:Math.max(1,y(q1)-y(q3)),fill:color,'fill-opacity':.28,stroke:color,'stroke-width':2}));
        svg.append(el('line',{x1:cx-bw/2,x2:cx+bw/2,y1:y(med),y2:y(med),stroke:'#222','stroke-width':3}));
        if(showPoints.checked)list.forEach((r,i)=>{const px=cx+(i-(list.length-1)/2)*Math.min(12,bw/(list.length+1)),py=y(r.value),rad=Number(pointSize.value);const node=r.sex==='male'?el('path',{d:`M ${px} ${py-rad} L ${px+rad} ${py+rad} L ${px-rad} ${py+rad} Z`,fill:color,stroke:'white'}):el('circle',{cx:px,cy:py,r:rad,fill:color,stroke:'white'});node.append(el('title',{},`${r.animal}: ${r.value.toFixed(3)}; ${yLabel}`));svg.append(node);});
        const name=idx?panel.name:'WT_3mo';svg.append(el('text',{x:cx,y:H-B+23,'text-anchor':'middle','font-size':panels.length===4?11:15},`${name} (n=${list.length})`));
      });
      if(showTests.checked){const peak=Math.max(...[...panel.control,...panel.treated].map(x=>x.value));const py=y(peak+spread*.12);svg.append(el('path',{d:`M ${boxCenters[0]} ${py+6} V ${py} H ${boxCenters[1]} V ${py+6}`,fill:'none',stroke:'#333','stroke-width':1.5}));svg.append(el('text',{x:center,y:py-5,'text-anchor':'middle','font-size':panels.length===4?10:12},`p=${panel.p.toFixed(3)} · BH q=${panel.q.toFixed(3)}`));}
      if(panels.length===4&&pidx<3)svg.append(el('line',{x1:center+groupW/2,x2:center+groupW/2,y1:T,y2:H-B,stroke:'#ddd','stroke-dasharray':'3 4'}));
    });
    svg.append(el('text',{transform:`translate(22 ${H/2}) rotate(-90)`,'text-anchor':'middle','font-size':13},yLabel));
    svg.append(el('text',{x:W/2,y:H-62,'text-anchor':'middle','font-size':12},panels.length===4?'Control is repeated because each target has its own TE set.':'Control and target use the same TE set.'));
    svg.append(el('text',{x:W/2,y:H-40,'text-anchor':'middle','font-size':12},showTests.checked?'Exact two-sided rank-sum test per mouse; BH across four contrasts; unadjusted for sex.':'Descriptive mouse-level values; enable significance bars for exact rank-sum tests.'));
    svg.append(el('text',{x:W/2,y:H-20,'text-anchor':'middle','font-size':12},showPoints.checked?'Female: circle · male: triangle':'Mouse points hidden'));
    holder.replaceChildren(svg);
    status.textContent=`${panels.length===4?'All four comparisons: each control box uses that target’s TE set.':panels[0].name+': '+(panels[0].control.length+panels[0].treated.length)+' mice.'} Female chrY TE copies excluded. ATAC signal divided by each track’s covered-base genome-wide mean; ${scale.value==='z'?'z-scores calculated separately within each comparison from log-normalized values':scale.value==='log'?'log₂ normalized values':'normalized values'}. WT_21mo_female_1 is excluded only from WT_21mo. ${showTests.checked?'Exploratory two-sided exact rank-sum p values; BH q values across all four comparisons; sex not adjusted.':''}`;
  }
  for (const n of [target,normalization,scale,low,high,pointSize,boxWidth,plotWidth,plotHeight,showPoints,showTests]) n.addEventListener('input',draw);
  $('[data-box-pdf]').addEventListener('click',async()=>{
    if (!svg || !window.jspdf?.jsPDF) {status.textContent='PDF export unavailable; use the static PDF link below.';return;}
    try {
      const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml;charset=utf-8'}));
      const img=new Image();await new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=reject;img.src=url;});
      const vb=svg.viewBox.baseVal,c=document.createElement('canvas');c.width=vb.width*2;c.height=vb.height*2;
      const ctx=c.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,c.width,c.height);ctx.drawImage(img,0,0,c.width,c.height);URL.revokeObjectURL(url);
      const doc=new window.jspdf.jsPDF({orientation:vb.width>=vb.height?'landscape':'portrait',unit:'mm',format:[vb.width/4,vb.height/4]});
      doc.addImage(c.toDataURL('image/png'),'PNG',0,0,vb.width/4,vb.height/4);doc.save(`ATAC_TE_${target.value}_${scale.value}_boxplot.pdf`);
    } catch (e) {status.textContent=`PDF export failed: ${e.message}. Use the static PDF link below.`;}
  });
  fetch('downloads/ATAC_target_TE_mouse_values_female_chrY_excluded.tsv')
    .then(async r=>{if(!r.ok)throw new Error('Required ATAC mouse values unavailable');return r.text();})
    .then(text=>{const lines=text.trim().split(/\r?\n/),fields=lines.shift().split('\t');
      records=lines.map(line=>{const vals=line.split('\t'),r=Object.fromEntries(fields.map((key,i)=>[key,vals[i]]));return {...r,signal:Number(r.signal)};});
      if(records.length!==31||new Set(records.map(r=>`${r.target}|${r.animal}`)).size!==31||records.some(r=>!Number.isFinite(r.signal)||r.signal<0))throw new Error('Incomplete or invalid ATAC values');draw();
    }).catch(e=>{status.textContent=`Interactive ATAC boxplot could not load: ${e.message}.`;});
})();
