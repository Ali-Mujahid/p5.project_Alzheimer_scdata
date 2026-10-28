/* Primary IRescue TE-copy differential RNA results; counts and fitted models stay unchanged. */
(() => {
 'use strict';
 const host=document.getElementById('irescue-de-explorer');if(!host)return;
 const $=s=>host.querySelector(s),ns='http://www.w3.org/2000/svg';let data=null,current=null,volcano=null,heatmap=null;
 const make=(tag,attrs={},text)=>{let n=document.createElementNS(ns,tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,String(v));if(text!==undefined)n.textContent=text;return n;};
 const title=(s,x,y,text,size=16)=>s.append(make('text',{x,y,'text-anchor':'middle','font-size':size},text));
 function render(){
  if(!data)return;current=data.comparisons.find(c=>c.target===$('[data-de-target]').value);
  const threshold=Number($('[data-de-fdr]').value),pointSize=Number($('[data-de-size]').value),high=$('[data-de-high]').value,low=$('[data-de-low]').value;
  const rows=current.volcano,sig=rows.filter(r=>r.FDR<threshold),up=sig.filter(r=>r.log2FC>0).length;
  $('[data-de-status]').textContent=`${current.target} vs WT_3mo: ${current.tested_loci.toLocaleString()} of ${current.total_loci.toLocaleString()} TE copies tested; ${up} higher and ${sig.length-up} lower at FDR < ${threshold}${threshold===.1?' (exploratory)':''}. Four mice per group; sex-adjusted primary gene-TMM model.`;
  const W=850,H=610,L=90,R=30,T=85,B=95,maxX=Math.max(1,...rows.map(r=>Math.abs(r.log2FC)))*1.08,maxY=Math.max(2,...rows.map(r=>-Math.log10(Math.max(r.FDR,1e-300))))*1.08;
  const x=v=>L+(v+maxX)/(2*maxX)*(W-L-R),y=v=>H-B-v/maxY*(H-T-B);
  volcano=make('svg',{xmlns:ns,viewBox:`0 0 ${W} ${H}`,width:W,height:H,role:'img','aria-label':'IRescue TE differential expression volcano',style:'font-family:Arial;background:white;max-width:100%;height:auto'});
  volcano.append(make('rect',{width:W,height:H,fill:'white'}));title(volcano,W/2,28,current.target+' vs WT_3mo',21);title(volcano,W/2,55,'Primary IRescue expected counts · edgeR QL · sex + condition',13);
  for(let i=0;i<=4;i++){
   let v=maxY*i/4;volcano.append(make('line',{x1:L,x2:W-R,y1:y(v),y2:y(v),stroke:'#e3e7e5'}));title(volcano,L-32,y(v)+4,v.toFixed(1),12);
   v=-maxX+2*maxX*i/4;title(volcano,x(v),H-B+24,v.toFixed(1),12);
  }
  volcano.append(make('line',{x1:L,x2:L,y1:T,y2:H-B,stroke:'#444'}));volcano.append(make('line',{x1:L,x2:W-R,y1:H-B,y2:H-B,stroke:'#444'}));
  volcano.append(make('line',{x1:L,x2:W-R,y1:y(-Math.log10(threshold)),y2:y(-Math.log10(threshold)),stroke:'#666','stroke-dasharray':'5 5'}));
  volcano.append(make('line',{x1:x(0),x2:x(0),y1:T,y2:H-B,stroke:'#aaa','stroke-dasharray':'3 3'}));
  for(const r of rows.slice().sort((a,b)=>b.FDR-a.FDR)){
   const c=r.FDR<threshold?(r.log2FC>0?high:low):'#b7b7b7';const n=make('circle',{cx:x(r.log2FC),cy:y(-Math.log10(Math.max(r.FDR,1e-300))),r:pointSize,fill:c,'fill-opacity':.65});
   n.append(make('title',{},`${r.TE_subfamily} | ${r.locus}; log2FC=${r.log2FC.toFixed(3)}; FDR=${r.FDR.toPrecision(3)}`));volcano.append(n);
  }
  title(volcano,W/2,H-38,'log₂ fold change (target / WT_3mo)',15);
  volcano.append(make('text',{transform:`translate(23 ${H/2}) rotate(-90)`,'text-anchor':'middle','font-size':14},'−log₁₀ BH-adjusted P-value'));
  title(volcano,W/2,H-12,'Color cutoff changes display only; no extra fold-change cutoff.',12);$('[data-de-volcano]').replaceChildren(volcano);
  const permitted=new Set(sig.map(r=>r.locus)),display=current.heatmap.filter(r=>permitted.has(r.label.slice(r.label.indexOf(' | ')+3))).slice(0,50);
  const hw=1100,hh=Math.max(400,170+display.length*17),left=460,top=85,cell=65;
  heatmap=make('svg',{xmlns:ns,viewBox:`0 0 ${hw} ${hh}`,width:hw,height:hh,role:'img','aria-label':'IRescue differential TE expression heatmap',style:'font-family:Arial;background:white;max-width:100%;height:auto'});
  heatmap.append(make('rect',{width:hw,height:hh,fill:'white'}));title(heatmap,hw/2,28,current.target+' | differential TE-copy RNA',21);title(heatmap,hw/2,53,`Up to 50 best-FDR copies at FDR < ${threshold}; row z-score, log₂(1+normalized CPM)`,13);
  function rgb(h){return [1,3,5].map(i=>parseInt(h.slice(i,i+2),16));}
  function color(z){let c=rgb(z>=0?high:low),a=Math.min(1,Math.abs(z)/2.5);return `rgb(${c.map(v=>Math.round(255*(1-a)+v*a)).join(',')})`;}
  if(!display.length)title(heatmap,hw/2,170,'No TE copies pass this FDR cutoff; none substituted.',17);
  display.forEach((r,i)=>{
   heatmap.append(make('text',{x:left-8,y:top+i*17+12,'text-anchor':'end','font-size':9},r.label));
   r.z.forEach((z,j)=>{const rect=make('rect',{x:left+j*cell,y:top+i*17,width:cell,height:17,fill:color(z)});rect.append(make('title',{},r.label+'; '+current.mice[j]+'; z='+z.toFixed(3)));heatmap.append(rect);});
  });
  if(display.length)current.mice.forEach((m,j)=>heatmap.append(make('text',{transform:`translate(${left+j*cell+25} ${top+display.length*17+12}) rotate(35)`,'font-size':9},m)));
  title(heatmap,hw/2,hh-14,'Blue: lower · white: row mean · red: higher; display clipped at ±2.5; mice are not reordered.',12);$('[data-de-heatmap]').replaceChildren(heatmap);
  $('[data-de-list]').href=`downloads/IRescue_${current.target}_DE_primary_all_TE_results.tsv.gz`;
 }
 async function exportPDF(svg,suffix){
  if(!svg||!window.jspdf?.jsPDF){$('[data-de-status]').textContent='Use the checked PDF links below; PDF export library is unavailable.';return;}
  try{
   const u=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml;charset=utf-8'})),img=new Image();await new Promise((res,rej)=>{img.onload=res;img.onerror=rej;img.src=u;});
   const vb=svg.viewBox.baseVal,c=document.createElement('canvas');c.width=vb.width*2;c.height=vb.height*2;const ctx=c.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,c.width,c.height);ctx.drawImage(img,0,0,c.width,c.height);URL.revokeObjectURL(u);
   const pdf=new window.jspdf.jsPDF({unit:'mm',format:[vb.width/4,vb.height/4],orientation:vb.width>vb.height?'landscape':'portrait'});pdf.addImage(c.toDataURL('image/png'),'PNG',0,0,vb.width/4,vb.height/4);pdf.save(`IRescue_${current.target}_DE_${suffix}.pdf`);
  }catch(e){$('[data-de-status]').textContent='PDF export failed: '+e.message+'. Checked PDF links remain available.';}
 }
 for(const s of ['[data-de-target]','[data-de-fdr]','[data-de-high]','[data-de-low]','[data-de-size]'])$(s).addEventListener('input',render);
 $('[data-de-volcano-pdf]').addEventListener('click',()=>exportPDF(volcano,'volcano'));$('[data-de-heatmap-pdf]').addEventListener('click',()=>exportPDF(heatmap,'heatmap'));
 fetch('data/irescue_microglia_DE.json').then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json();}).then(v=>{if(v.status!=='completed'||v.comparisons.length!==4)throw Error('Four completed comparisons required');data=v;$('[data-de-target]').replaceChildren(...v.comparisons.map(c=>{let n=document.createElement('option');n.value=c.target;n.textContent=c.target;return n;}));render();}).catch(e=>{$('[data-de-status]').textContent='Could not load differential results: '+e.message;});
})();
