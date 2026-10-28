/* Exploratory RUVr plots; original counts and DE results are unchanged. */
(() => {
 'use strict';const host=document.getElementById('irescue-ruv-explorer');if(!host)return;
 const $=s=>host.querySelector(s),NS='http://www.w3.org/2000/svg';let data=null,svg=null;
 const el=(tag,a={},t)=>{const n=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(a))n.setAttribute(k,String(v));if(t!==undefined)n.textContent=t;return n;};
 const quant=(v,p)=>{let x=v.slice().sort((a,b)=>a-b),i=(x.length-1)*p;return x[Math.floor(i)]+(x[Math.ceil(i)]-x[Math.floor(i)])*(i%1);};
 const labels={all_rows:'All original copies · gene normalization',nonzero:'Remove all-eight-zero copies · gene normalization',RUVr_k1:'Nonzero copies + protected RUVr k=1',RUVr_k2:'Nonzero copies + protected RUVr k=2 · sensitivity'};
 function render(){
  if(!data)return;const target=$('[data-ruv-target]').value,method=$('[data-ruv-method]').value,metric=$('[data-ruv-metric]').value;
  const rows=data.points.filter(r=>r.target===target&&r.method===method);if(rows.length!==8)throw Error('Eight mice required');
  const value=r=>r[metric],vals=rows.map(value),range=Math.max(...vals)-Math.min(...vals),pad=Math.max(.15*range,.02),lo=Math.min(...vals)-pad,hi=Math.max(...vals)+pad;
  const W=1050,H=620,L=100,R=30,T=92,B=140,y=v=>H-B-(v-lo)/(hi-lo)*(H-T-B),x=i=>L+(i+.5)/2*(W-L-R);
  svg=el('svg',{xmlns:NS,viewBox:`0 0 ${W} ${H}`,width:W,height:H,role:'img','aria-label':'Mouse-level TE RNA expression after zero filtering or RUVr',style:'font-family:Arial;background:white;max-width:100%;height:auto'});
  svg.append(el('rect',{width:W,height:H,fill:'white'}));svg.append(el('text',{x:W/2,y:30,'text-anchor':'middle','font-size':21},target+' vs WT_3mo'));svg.append(el('text',{x:W/2,y:57,'text-anchor':'middle','font-size':15},labels[method]));
  for(let i=0;i<=5;i++){let v=lo+(hi-lo)*i/5;svg.append(el('line',{x1:L,x2:W-R,y1:y(v),y2:y(v),stroke:'#e1e6e5'}));svg.append(el('text',{x:L-12,y:y(v)+4,'text-anchor':'end','font-size':13},v.toFixed(3)));}
  if(lo<0&&hi>0)svg.append(el('line',{x1:L,x2:W-R,y1:y(0),y2:y(0),stroke:'#999','stroke-dasharray':'5 5'}));
  ['WT_3mo',target].forEach((g,i)=>{
   const rs=rows.filter(r=>r.condition===g);if(rs.length!==4)throw Error('Four mice per group required');const v=rs.map(value),xx=x(i),c=i?$('[data-ruv-high]').value:$('[data-ruv-low]').value;
   const min=Math.min(...v),max=Math.max(...v),q1=quant(v,.25),q3=quant(v,.75),med=quant(v,.5);
   svg.append(el('line',{x1:xx,x2:xx,y1:y(min),y2:y(max),stroke:'#333','stroke-width':2}));
   for(const z of[min,max])svg.append(el('line',{x1:xx-25,x2:xx+25,y1:y(z),y2:y(z),stroke:'#333','stroke-width':2}));
   svg.append(el('rect',{x:xx-55,y:y(q3),width:110,height:Math.max(1,y(q1)-y(q3)),fill:c,'fill-opacity':.28,stroke:c,'stroke-width':2}));svg.append(el('line',{x1:xx-55,x2:xx+55,y1:y(med),y2:y(med),stroke:'#222','stroke-width':3}));
   rs.forEach((r,j)=>{const px=xx+(j-1.5)*12,py=y(value(r)),rad=Number($('[data-ruv-size]').value),p=r.sex==='male'?el('path',{d:`M${px} ${py-rad} L${px+rad} ${py+rad} L${px-rad} ${py+rad} Z`,fill:c,stroke:'white'}):el('circle',{cx:px,cy:py,r:rad,fill:c,stroke:'white'});p.append(el('title',{},`${r.animal}; mean log2 normalized expression=${r.mean_log2_1plus_CPM}; z=${r.z_score}`));svg.append(p);});
   svg.append(el('text',{x:xx,y:H-B+30,'text-anchor':'middle','font-size':17},g));
  });
  const text=metric==='z_score'?'Z-score of mean normalized TE expression across the same eight mice':'Mean log₂(1 + gene-normalized CPM) per TE copy; adjusted where labeled';
  svg.append(el('text',{x:W/2,y:H-55,'text-anchor':'middle','font-size':14},text));svg.append(el('text',{x:W/2,y:H-28,'text-anchor':'middle','font-size':13},'One point per mouse · female circle / male triangle · descriptive · adjusted log values are not counts'));
  $('[data-ruv-plot]').replaceChildren(svg);const s=data.filter_summary.find(r=>r.target===target);
  $('[data-ruv-status]').textContent=`${s.retained_loci.toLocaleString()} of ${s.original_loci.toLocaleString()} copies remain after removing ${s.all_zero_in_same8_removed.toLocaleString()} copies with zero counts in all eight mice. Same copies and four mice per condition. Raw totals and previous DE results are unchanged.`;
 }
 for(const s of['[data-ruv-target]','[data-ruv-method]','[data-ruv-metric]','[data-ruv-high]','[data-ruv-low]','[data-ruv-size]'])$(s).addEventListener('input',render);
 $('[data-ruv-pdf]').addEventListener('click',async()=>{
  if(!svg||!window.jspdf?.jsPDF){$('[data-ruv-status]').textContent='Use the checked PDF links below; interactive PDF library unavailable.';return;}
  try{let url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml;charset=utf-8'})),img=new Image();await new Promise((ok,no)=>{img.onload=ok;img.onerror=no;img.src=url;});let c=document.createElement('canvas');c.width=3150;c.height=1860;let ctx=c.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,c.width,c.height);ctx.drawImage(img,0,0,c.width,c.height);URL.revokeObjectURL(url);let pdf=new window.jspdf.jsPDF({unit:'mm',format:'a4',orientation:'landscape'});pdf.addImage(c.toDataURL('image/png'),'PNG',8,10,281,166);pdf.save(`IRescue_${$('[data-ruv-target]').value}_${$('[data-ruv-method]').value}_boxplot.pdf`);}catch(e){$('[data-ruv-status]').textContent='PDF export failed: '+e.message;}
 });
 fetch('data/irescue_nonzero_ruv.json').then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json();}).then(v=>{if(v.status!=='completed'||v.points.length!==128)throw Error('Completed checked values required');data=v;$('[data-ruv-target]').replaceChildren(...v.filter_summary.map(r=>{let n=document.createElement('option');n.value=r.target;n.textContent=r.target;return n;}));render();}).catch(e=>{$('[data-ruv-status]').textContent='Could not load data: '+e.message;});
})();
