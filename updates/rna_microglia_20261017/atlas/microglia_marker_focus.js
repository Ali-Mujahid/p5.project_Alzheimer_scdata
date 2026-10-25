/* Source-backed, cluster-selected Microglia RNA and ATAC marker dotplots. */
(function(){
  'use strict';
  const host=document.getElementById('microglia-marker-focus25');
  if(!host)return;
  const status=document.createElement('p');status.setAttribute('role','status');status.textContent='Loading cluster marker summaries…';host.appendChild(status);
  const panels=document.createElement('div');panels.className='paired-grid';host.appendChild(panels);
  const url='downloads/Paired_microglia_marker_summary.json';
  fetch(url).then(r=>{if(!r.ok)throw Error('Marker summary HTTP '+r.status);return r.json();}).then(D=>{
    if(!Array.isArray(D.genes)||!D.rna?.rows||!D.atac?.rows)throw Error('Marker summary schema mismatch');
    status.textContent='Rankings use the 19 measured Microglia candidate markers; six other-lineage QC genes remain in the full dotplots above. Higher rank means larger selected-cluster mean minus the mean of other clusters within the same assay; it is descriptive, not a differential-expression test.';
    for(const assay of ['rna','atac'])makePanel(D,assay);
  }).catch(e=>status.textContent=e.message);

  function makePanel(D,assay){
    const source=D[assay],box=document.createElement('article');box.className='paired-panel';panels.appendChild(box);
    const heading=document.createElement('h3');heading.textContent=assay==='rna'?'RNA cluster marker focus':'ATAC cluster gene-activity focus';box.appendChild(heading);
    const controls=document.createElement('div');controls.className='paired-controls';box.appendChild(controls);
    const label=(title,node)=>{const l=document.createElement('label');l.append(title+' ',node);controls.appendChild(l);return node;};
    const cluster=label('Cluster',document.createElement('select'));
    source.clusters.forEach((id,i)=>{const o=document.createElement('option');o.value=String(i);o.textContent=String(source.cluster_names?.[i]||'Cluster '+id).replace(/(?:[-\s]+like)\b/gi,'').trim();cluster.appendChild(o);});
    const n=label('Top markers',document.createElement('select'));for(const x of [5,8,12,19]){const o=document.createElement('option');o.value=x;o.textContent=x;n.appendChild(o);}n.value='8';
    const dot=label('Dot size',document.createElement('input'));dot.type='range';dot.min='4';dot.max='15';dot.value='9';
    const high=label('High color',document.createElement('input'));high.type='color';high.value='#d53e4f';
    const low=label('Low color',document.createElement('input'));low.type='color';low.value='#3288bd';
    const save=document.createElement('button');save.type='button';save.textContent='Download PDF';controls.appendChild(save);
    const plot=document.createElement('div');plot.className='dotplot-scroll';box.appendChild(plot);
    const note=document.createElement('p');note.className='hint';box.appendChild(note);
    const rows=source.rows,lookup=new Map(rows.map(r=>[r[0]+':'+r[1],r]));
    const blend=(a,b,t)=>{const A=[1,3,5].map(i=>parseInt(a.slice(i,i+2),16)),B=[1,3,5].map(i=>parseInt(b.slice(i,i+2),16));return '#'+A.map((v,i)=>Math.round(v+(B[i]-v)*t).toString(16).padStart(2,'0')).join('');};
    function render(){
      const focus=+cluster.value,N=+n.value;
      const otherLineageQC=new Set(['Rbfox3','Snap25','Mbp','Plp1','Aldh1l1','Gfap']);
      const ranking=D.genes.map((gene,j)=>{const selected=lookup.get(focus+':'+j)?.[2]||0;let total=0,count=0;for(let i=0;i<source.clusters.length;i++){if(i===focus)continue;total+=lookup.get(i+':'+j)?.[2]||0;count++;}return {gene,j,score:selected-total/count};}).filter(r=>!otherLineageQC.has(r.gene)).sort((a,b)=>b.score-a.score).slice(0,N);
      const width=Math.max(540,170+N*45),height=105+source.clusters.length*22;
      const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
      for(const [k,v] of Object.entries({viewBox:`0 0 ${width} ${height}`,width,height,role:'img','aria-label':heading.textContent}))svg.setAttribute(k,v);
      const add=(tag,attrs)=>{const e=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));svg.appendChild(e);return e;};
      add('rect',{x:0,y:86+focus*22,width,height:22,fill:'#f3eac2'});
      ranking.forEach((item,j)=>{const tx=add('text',{x:162+j*45,y:76,transform:`rotate(-50 ${162+j*45} 76)`,'text-anchor':'end','font-size':10});tx.textContent=item.gene;});
      source.clusters.forEach((id,i)=>{const ty=add('text',{x:148,y:101+i*22,'text-anchor':'end','font-size':10,'font-weight':i===focus?'bold':'normal'});ty.textContent=String(source.cluster_names?.[i]||'Cluster '+id).replace(/(?:[-\s]+like)\b/gi,'').trim();});
      ranking.forEach((item,j)=>{let max=0;for(let i=0;i<source.clusters.length;i++)max=Math.max(max,lookup.get(i+':'+item.j)?.[2]||0);for(let i=0;i<source.clusters.length;i++){
        const r=lookup.get(i+':'+item.j);if(!r)continue;const frac=max?r[2]/max:0,c=add('circle',{cx:162+j*45,cy:97+i*22,r:Math.max(.6,Math.sqrt(Math.max(0,r[3]))*(+dot.value)),fill:blend(low.value,high.value,frac),'fill-opacity':.25+.75*frac});const tip=document.createElementNS(ns,'title');tip.textContent=`${item.gene}; cluster ${source.clusters[i]}; mean ${r[2].toFixed(3)}; detected ${(100*r[3]).toFixed(1)}%`;c.appendChild(tip);
      }});
      plot.replaceChildren(svg);note.textContent=`${N} ranked markers across ${source.clusters.length} clusters. Yellow row: selected cluster. Dot area: detection fraction; color: mean scaled within each marker. ${source.mean_quantity}. RNA and ATAC scales are separate.`;
    }
    for(const el of [cluster,n,dot,high,low])el.addEventListener('input',render);render();
    save.addEventListener('click',()=>{const svg=plot.querySelector('svg');if(!svg||!window.jspdf?.jsPDF)return;const serialized=new XMLSerializer().serializeToString(svg),blob=new Blob([serialized],{type:'image/svg+xml;charset=utf-8'}),objectUrl=URL.createObjectURL(blob),img=new Image();img.onload=()=>{const canvas=document.createElement('canvas');canvas.width=svg.width.baseVal.value*2;canvas.height=svg.height.baseVal.value*2;const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(img,0,0,canvas.width,canvas.height);URL.revokeObjectURL(objectUrl);const pdf=new window.jspdf.jsPDF({orientation:'landscape',unit:'mm',format:'a4'});pdf.setFontSize(14);pdf.text(heading.textContent,10,13);const w=Math.min(270,180*canvas.width/canvas.height),h=Math.min(180,270*canvas.height/canvas.width);pdf.addImage(canvas.toDataURL('image/png'),'PNG',10,20,w,h);pdf.save('Microglia_'+assay+'_cluster_'+cluster.value+'_markers.pdf');};img.src=objectUrl;});
  }
})();
