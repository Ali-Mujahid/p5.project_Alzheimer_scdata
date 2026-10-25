(function(){
  'use strict';
  const root=document.getElementById('microglia-deg25');
  if(!root)return;
  const NS='http://www.w3.org/2000/svg';
  const $=id=>document.getElementById(id);
  const svg=(name,attrs={})=>{const x=document.createElementNS(NS,name);for(const [k,v] of Object.entries(attrs))x.setAttribute(k,String(v));return x;};
  const add=(parent,name,attrs={},label)=>{const x=svg(name,attrs);if(label!==undefined)x.textContent=String(label);parent.appendChild(x);return x;};
  const rgb=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
  const blend=(a,b,t)=>'#'+rgb(a).map((v,i)=>Math.round(v+(rgb(b)[i]-v)*t).toString(16).padStart(2,'0')).join('');
  const color=(x,max,low,high)=>x<0?blend('#ffffff',low,Math.min(1,-x/max)):blend('#ffffff',high,Math.min(1,x/max));
  let data;
  function state(){return{pop:$('mgdeg-pop').value,target:$('mgdeg-target').value,fdr:Number($('mgdeg-fdr').value),
    dot:Number($('mgdeg-dot').value),low:$('mgdeg-low').value,high:$('mgdeg-high').value};}
  function drawVolcano(s){
    const holder=$('mgdeg-volcano');holder.replaceChildren();
    const row=data.summary.find(r=>r.population===s.pop&&r.contrast===s.target+'_vs_WT_3mo');
    if(!row||row.status!=='tested'){holder.textContent='Untested: '+(row?row.status:'no mouse-supported result');return;}
    const points=((data.volcano_by_population[s.pop]||{})[s.target]||[]);
    const w=650,h=420,l=55,r=15,t=20,b=48;
    const plot=add(holder,'svg',{viewBox:`0 0 ${w} ${h}`,role:'img','aria-label':'Mouse-level DEG volcano plot'});
    const maxX=Math.max(1,...points.map(p=>Math.abs(p[2])))*1.08,maxY=Math.max(1,...points.map(p=>p[3]))*1.08;
    const xx=v=>l+(v+maxX)/(2*maxX)*(w-l-r), yy=v=>h-b-v/maxY*(h-b-t);
    add(plot,'line',{x1:l,y1:h-b,x2:w-r,y2:h-b,stroke:'#657674'});
    add(plot,'line',{x1:xx(0),y1:t,x2:xx(0),y2:h-b,stroke:'#a5afae','stroke-dasharray':'4 3'});
    add(plot,'text',{x:w/2,y:h-7,'text-anchor':'middle','font-size':13},'log₂ fold change');
    add(plot,'text',{x:8,y:18,'font-size':12},'−log₁₀ p');
    for(const p of points){const hit=p[4]<=s.fdr;const circle=add(plot,'circle',{cx:xx(p[2]),cy:yy(p[3]),r:hit?s.dot:Math.max(1,s.dot*.5),fill:hit?(p[2]>=0?s.high:s.low):'#aeb7bb',opacity:hit?.85:.43});
      add(circle,'title',{},`${p[1]||p[0]} · log2FC ${p[2]} · FDR ${p[4]}`);}
    $('mgdeg-volcano-note').textContent=`${row.FDR_0_10} genes at FDR < 0.1; plot shows ${points.length} top-ranked tested genes. Full results are in the downloadable archive.`;
  }
  function drawHeatmap(s){
    const holder=$('mgdeg-heatmap');holder.replaceChildren();
    const rows=data.differential_heatmap_genes,w=650,step=16,l=145,t=35,h=t+rows.length*step+30,cw=(w-l-15)/4;
    const plot=add(holder,'svg',{viewBox:`0 0 ${w} ${h}`,role:'img','aria-label':'Gene log2 fold-change heatmap'});
    data.contrasts.forEach((target,j)=>add(plot,'text',{x:l+j*cw+cw/2,y:17,'text-anchor':'middle','font-size':11},target.replace('_3mo','')));
    rows.forEach((g,i)=>{add(plot,'text',{x:l-6,y:t+i*step+12,'text-anchor':'end','font-size':11},g[1]||g[0]);
      g[2].forEach((v,j)=>{const box=add(plot,'rect',{x:l+j*cw,y:t+i*step,width:cw-2,height:step-1,fill:color(v,3,s.low,s.high)});
        add(box,'title',{},`${g[1]||g[0]} · ${data.contrasts[j]} · log2FC ${v}`);});});
  }
  function drawCluster(s){
    const holder=$('mgdeg-clusters');holder.replaceChildren();
    const w=650,l=70,t=42,step=17,cw=(w-l-15)/4,h=t+24*step+30;
    const plot=add(holder,'svg',{viewBox:`0 0 ${w} ${h}`,role:'img','aria-label':'Microglia subcluster DEG counts heatmap'});
    data.contrasts.forEach((target,j)=>add(plot,'text',{x:l+j*cw+cw/2,y:17,'text-anchor':'middle','font-size':11},target.replace('_3mo','')));
    for(let i=0;i<24;i++){add(plot,'text',{x:l-6,y:t+i*step+12,'text-anchor':'end','font-size':11},'MG'+i);
      data.contrasts.forEach((target,j)=>{const row=data.summary.find(r=>r.population==='MG'+i&&r.contrast===target+'_vs_WT_3mo');
        const n=row&&row.status==='tested'?Number(row.FDR_0_10):null;
        add(plot,'rect',{x:l+j*cw,y:t+i*step,width:cw-2,height:step-1,fill:n===null?'#eef0ed':color(Math.log1p(n),Math.log1p(10),s.low,s.high)});
        add(plot,'text',{x:l+j*cw+cw/2,y:t+i*step+12,'text-anchor':'middle','font-size':10},n===null?'–':n);});}
  }
  function drawLinks(s){
    const rows=data.TE_peak_candidate_links.filter(r=>r.population===s.pop&&r.contrast===s.target+'_vs_WT_3mo');
    $('mgdeg-link-count').textContent=`${rows.length} named TE-peak candidate rows for this population and contrast`;
    const body=$('mgdeg-link-body');body.replaceChildren();
    for(const r of rows.slice(0,40)){const tr=document.createElement('tr');
      for(const value of [r.gene_symbol,r.TE_subfamilies,r.peak_id,r.distance_to_TSS_bp,Number(r.ATAC_log2_change).toFixed(2),Number(r.gene_FDR).toExponential(2),r.TE_RNA_FDR]){
        const td=document.createElement('td');td.textContent=value;tr.appendChild(td);}body.appendChild(tr);}
  }
  function render(){const s=state();drawVolcano(s);drawHeatmap(s);drawCluster(s);drawLinks(s);}
  async function exportPdf(id,name){const source=$(id).querySelector('svg');if(!source)return;
    const serial=new XMLSerializer().serializeToString(source);const img=new Image();img.onload=()=>{
      const canvas=document.createElement('canvas');canvas.width=1500;canvas.height=Math.round(1500*source.viewBox.baseVal.height/source.viewBox.baseVal.width);
      const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(img,0,0,canvas.width,canvas.height);
      if(window.jspdf&&window.jspdf.jsPDF){const pdf=new window.jspdf.jsPDF({orientation:canvas.width>=canvas.height?'landscape':'portrait',unit:'px',format:[canvas.width,canvas.height]});pdf.addImage(canvas.toDataURL('image/png'),'PNG',0,0,canvas.width,canvas.height);pdf.save(name+'.pdf');}
      else{const link=document.createElement('a');link.download=name+'.png';link.href=canvas.toDataURL('image/png');link.click();}
    };img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(serial);}
  fetch('downloads/Microglia_DEG_atlas_data.json').then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json();}).then(value=>{
    data=value;const pop=$('mgdeg-pop');['all_microglia',...Array.from({length:24},(_,i)=>'MG'+i)].forEach(v=>{const opt=document.createElement('option');opt.value=v;opt.textContent=v==='all_microglia'?'All Microglia':v;pop.appendChild(opt);});
    data.contrasts.forEach(v=>{const opt=document.createElement('option');opt.value=v;opt.textContent=v+' vs WT_3mo';$('mgdeg-target').appendChild(opt);});
    $('mgdeg-target').value='APOE4_TREM2_3mo';for(const id of ['mgdeg-pop','mgdeg-target','mgdeg-fdr','mgdeg-dot','mgdeg-low','mgdeg-high'])$(id).addEventListener('input',render);
    document.querySelectorAll('#microglia-deg25 [data-export-svg]').forEach(button=>button.addEventListener('click',()=>exportPdf(button.dataset.exportSvg,button.dataset.filename)));
    $('mgdeg-status').textContent='Mouse-level DEG results loaded · low '+value.low+' / high '+value.high;render();
  }).catch(e=>{$('mgdeg-status').textContent='DEG data could not load: '+e.message;});
})();
