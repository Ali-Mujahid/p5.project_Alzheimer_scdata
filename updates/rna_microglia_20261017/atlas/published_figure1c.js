(() => {
  const section = document.getElementById('trackersci-figure1c-control');
  if (!section) return;
  const $ = id => document.getElementById(id);
  const NS = 'http://www.w3.org/2000/svg';
  const defaults = {low:'#3288bd', mid:'#ffffff', high:'#d53e4f', contrast:1};
  const data = {paper:null, expanded:null, extra:null, combined:null};
  const state = {
    RNA:{mode:'paper', style:'dots', markers:[], cells:[], size:12, colWidth:40, rowHeight:29, fontSize:13, grid:false},
    ATAC:{mode:'paper', style:'heatmap', markers:[], cells:[], size:12, colWidth:40, rowHeight:29, fontSize:13, grid:false}
  };
  const axes = {};
  function svgNode(parent, tag, attrs, label) {
    const node = document.createElementNS(NS, tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
    if (label !== undefined) node.textContent = label;
    parent.appendChild(node);
    return node;
  }
  const channel = (a,b,t) => Math.round(a+(b-a)*Math.max(0,Math.min(1,t)));
  function mix(left,right,t) {
    const a=[1,3,5].map(i=>parseInt(left.slice(i,i+2),16));
    const b=[1,3,5].map(i=>parseInt(right.slice(i,i+2),16));
    return `rgb(${a.map((v,i)=>channel(v,b[i],t)).join(',')})`;
  }
  function shade(v,min,max,low,mid,high,contrast) {
    if (v<0) return mix(mid,low,Math.min(1,contrast*v/min));
    return mix(mid,high,Math.min(1,contrast*v/max));
  }
  function parseTable(text) {
    const lines=text.trimEnd().split(/\r?\n/);
    const fields=lines.shift().split('\t');
    if (fields.join('|')!=='assay|cell_type|gene|mean_normalized|fraction_detected|scaled_mean') throw Error('Unexpected marker table columns');
    return lines.map(line=>{
      const p=line.split('\t');
      if(p.length!==6) throw Error('Incomplete marker row');
      const row={assay:p[0],cell:p[1],gene:p[2],mean:Number(p[3]),fraction:Number(p[4]),scaled:Number(p[5])};
      if(!['RNA','ATAC'].includes(row.assay) || !row.cell || !row.gene ||
         !Number.isFinite(row.mean) || !Number.isFinite(row.scaled) ||
         !Number.isFinite(row.fraction) || row.fraction<0 || row.fraction>1) throw Error('Invalid marker measurement');
      return row;
    });
  }
  function genesFor(assay,mode) {
    return [...new Set(data[mode].filter(row=>row.assay===assay).map(row=>row.gene))];
  }
  function checkTables() {
    for(const assay of ['RNA','ATAC']) {
      const base=data.paper.filter(row=>row.assay===assay);
      axes[assay]=[...new Set(base.map(row=>row.cell))];
      const expected=assay==='RNA'?16:14;
      if(axes[assay].length!==expected || genesFor(assay,'paper').length!==expected) throw Error('Published Figure 1C axes changed');
      for(const mode of ['paper','expanded','combined']) {
        const selected=data[mode].filter(row=>row.assay===assay);
        const genes=genesFor(assay,mode);
        const keys=new Set(selected.map(row=>`${row.cell}\t${row.gene}`));
        if(keys.size!==selected.length || keys.size!==axes[assay].length*genes.length ||
           selected.some(row=>!axes[assay].includes(row.cell))) throw Error(`Incomplete ${assay} ${mode} marker grid`);
      }
    }
  }
  function control(label,element) {
    const wrap=document.createElement('label');
    wrap.append(label,element);
    return wrap;
  }
  function select(options,value) {
    const e=document.createElement('select');
    for(const [key,label] of options) {
      const o=document.createElement('option');o.value=key;o.textContent=label;e.append(o);
    }
    e.value=value;return e;
  }
  function slider(min,max,value,step=1) {
    const e=document.createElement('input');e.type='range';e.min=min;e.max=max;e.step=step;e.value=value;return e;
  }
  function makePanel(assay) {
    const s=state[assay];
    const panel=document.createElement('div');panel.className='figure1c-plot';
    const title=document.createElement('h3');title.textContent=assay==='RNA'?'Published RNA marker plot':'Published ATAC gene-activity plot';panel.append(title);
    const tools=document.createElement('div');tools.className='figure1c-panel-controls';panel.append(tools);
    const source=select([['paper','Figure 1C markers'],['combined','Published + extra QC markers'],['expanded','Expanded QC markers only']],s.mode);
    const style=select([['dots','Dotplot'],['squares','Square dotplot'],['heatmap','Heatmap']],s.style);
    const size=slider(2,19,s.size), colWidth=slider(26,62,s.colWidth), rowHeight=slider(19,44,s.rowHeight), fontSize=slider(9,18,s.fontSize);
    const grid=document.createElement('input');grid.type='checkbox';grid.checked=s.grid;
    tools.append(control('Marker source',source),control('Plot style',style),control('Max dot size',size),control('Column spacing',colWidth),control('Row spacing',rowHeight),control('Label size',fontSize),control('Grid lines',grid));
    const markerControls=document.createElement('div');markerControls.className='figure1c-marker-controls';panel.append(markerControls);
    const markerInput=document.createElement('input');markerInput.type='text';markerInput.className='figure1c-marker-input';markerInput.setAttribute('aria-label',`${assay} markers, comma-separated`);markerInput.value=s.markers.join(', ');
    const apply=document.createElement('button');apply.type='button';apply.textContent='Apply marker list';
    const all=document.createElement('button');all.type='button';all.textContent='Show all available';
    const available=document.createElement('small');available.className='figure1c-available';
    markerControls.append(control('Markers (comma-separated; order is adjustable)',markerInput),apply,all,available);
    const picker=document.createElement('div');picker.className='figure1c-pickers';panel.append(picker);
    const addMarker=select([], '');addMarker.setAttribute('aria-label',`Add ${assay} marker`);
    const addButton=document.createElement('button');addButton.type='button';addButton.textContent='+ Add marker';
    const markerChips=document.createElement('div');markerChips.className='figure1c-chips';markerChips.setAttribute('aria-label',`${assay} selected markers`);
    const markerPicker=document.createElement('div');markerPicker.className='figure1c-picker';
    markerPicker.append(control('Add a measured marker',addMarker),addButton,markerChips);
    const cellPicker=document.createElement('div');cellPicker.className='figure1c-picker';
    const cellHeading=document.createElement('strong');cellHeading.textContent='Cell types on y-axis';
    const cellActions=document.createElement('div');cellActions.className='figure1c-cell-actions';
    const allCells=document.createElement('button');allCells.type='button';allCells.textContent='Show all cell types';
    const noCells=document.createElement('button');noCells.type='button';noCells.textContent='Clear selection';
    cellActions.append(allCells,noCells);
    const cellList=document.createElement('div');cellList.className='figure1c-cell-list';
    cellPicker.append(cellHeading,cellActions,cellList);
    picker.append(markerPicker,cellPicker);
    const plot=document.createElement('div');plot.className='figure1c-svg';panel.append(plot);
    const single=document.createElement('button');single.type='button';single.textContent=`Download ${assay} PDF`;panel.append(single);
    source.addEventListener('change',()=>{
      s.mode=source.value;
      const permitted=genesFor(assay,s.mode);
      s.markers=s.markers.filter(g=>permitted.includes(g));
      if(!s.markers.length) s.markers=[...permitted];
      markerInput.value=s.markers.join(', ');refreshAvailable();refreshPickers();render();
    });
    style.addEventListener('change',()=>{s.style=style.value;render();});
    for(const [element,key] of [[size,'size'],[colWidth,'colWidth'],[rowHeight,'rowHeight'],[fontSize,'fontSize']]) element.addEventListener('input',()=>{s[key]=Number(element.value);render();});
    grid.addEventListener('change',()=>{s.grid=grid.checked;render();});
    function applyMarkers() {
      const canonical=new Map(genesFor(assay,'combined').map(g=>[g.toLowerCase(),g]));
      const typed=markerInput.value.split(',').map(x=>x.trim()).filter(Boolean);
      const requested=typed.map(g=>canonical.get(g.toLowerCase())||g);
      const combined=genesFor(assay,'combined');
      const invalid=requested.filter(g=>!combined.includes(g));
      if(!requested.length || invalid.length || new Set(requested).size!==requested.length) {
        $('figure1c-status').textContent=invalid.length?`Unavailable ${assay} marker(s) in this source: ${invalid.join(', ')}`:'Choose at least one marker and do not repeat a gene.';
        markerInput.focus();return;
      }
      if(requested.some(g=>!genesFor(assay,s.mode).includes(g))) {s.mode='combined';source.value='combined';}
      s.markers=requested;markerInput.value=requested.join(', ');refreshPickers();render();
    }
    apply.addEventListener('click',applyMarkers);
    markerInput.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();applyMarkers();}});
    all.addEventListener('click',()=>{s.markers=genesFor(assay,s.mode);markerInput.value=s.markers.join(', ');refreshPickers();render();});
    addButton.addEventListener('click',()=>{
      const gene=addMarker.value;
      if(!gene || s.markers.includes(gene)) return;
      if(!genesFor(assay,s.mode).includes(gene)) {s.mode='combined';source.value='combined';}
      s.markers.push(gene);markerInput.value=s.markers.join(', ');refreshPickers();render();
    });
    allCells.addEventListener('click',()=>{s.cells=[...axes[assay]];refreshPickers();render();});
    noCells.addEventListener('click',()=>{s.cells=[];refreshPickers();render();});
    single.addEventListener('click',()=>exportPdf([assay]).catch(e=>{$('figure1c-status').textContent='PDF export failed: '+e.message;}));
    function refreshAvailable() {available.textContent='Measured markers (including Tmem119, Cx3cr1 and P2ry12): '+genesFor(assay,'combined').join(', ');}
    function refreshPickers() {
      addMarker.replaceChildren();
      const remaining=genesFor(assay,'combined').filter(g=>!s.markers.includes(g));
      for(const gene of remaining) {const option=document.createElement('option');option.value=gene;option.textContent=gene;addMarker.append(option);}
      addButton.disabled=!remaining.length;
      markerChips.replaceChildren();
      for(const gene of s.markers) {
        const remove=document.createElement('button');remove.type='button';remove.className='figure1c-chip';
        remove.textContent=`${gene} ×`;remove.setAttribute('aria-label',`Remove ${gene} from ${assay} markers`);
        remove.addEventListener('click',()=>{
          if(s.markers.length===1) {$('figure1c-status').textContent='Keep at least one marker.';return;}
          s.markers=s.markers.filter(g=>g!==gene);markerInput.value=s.markers.join(', ');refreshPickers();render();
        });
        markerChips.append(remove);
      }
      cellList.replaceChildren();
      for(const cell of axes[assay]) {
        const checkbox=document.createElement('input');checkbox.type='checkbox';checkbox.checked=s.cells.includes(cell);
        checkbox.setAttribute('aria-label',`Show ${cell} in ${assay}`);
        checkbox.addEventListener('change',()=>{
          s.cells=axes[assay].filter(name=>name===cell?checkbox.checked:s.cells.includes(name));
          refreshPickers();render();
        });
        const label=document.createElement('label');label.append(checkbox,document.createTextNode(cell));cellList.append(label);
      }
    }
    refreshAvailable();
    refreshPickers();
    return {panel,plot,markerInput,source,style,size,colWidth,rowHeight,fontSize,grid,refreshAvailable,refreshPickers};
  }
  function draw(assay,host) {
    const s=state[assay], selected=data[s.mode].filter(row=>row.assay===assay);
    const cells=s.cells,genes=s.markers;
    const byKey=new Map(selected.map(row=>[`${row.cell}\t${row.gene}`,row]));
    const min=Math.min(...selected.map(row=>row.scaled)),max=Math.max(...selected.map(row=>row.scaled));
    const left=Math.max(220,Math.min(360,Math.max(0,...cells.map(c=>c.length))*7+34));
    const top=35,bottom=140,width=left+genes.length*s.colWidth+55,height=top+cells.length*s.rowHeight+bottom;
    const svg=svgNode(host,'svg',{viewBox:`0 0 ${width} ${height}`,role:'img','aria-label':`${assay} ${s.style} of ${genes.length} markers across ${cells.length} cell types`});
    svgNode(svg,'rect',{x:0,y:0,width,height,fill:'#ffffff'});
    if(!cells.length) {svgNode(svg,'text',{x:35,y:65,'font-size':16,fill:'#52636a'},'Select at least one cell type above.');return;}
    if(s.grid) {
      for(let i=0;i<=cells.length;i++) svgNode(svg,'line',{x1:left,y1:top+i*s.rowHeight,x2:left+genes.length*s.colWidth,y2:top+i*s.rowHeight,stroke:'#e3e9eb','stroke-width':.7});
      for(let j=0;j<=genes.length;j++) svgNode(svg,'line',{x1:left+j*s.colWidth,y1:top,x2:left+j*s.colWidth,y2:top+cells.length*s.rowHeight,stroke:'#e3e9eb','stroke-width':.7});
    }
    cells.forEach((name,i)=>{
      const y=top+i*s.rowHeight+s.rowHeight/2;
      svgNode(svg,'text',{x:left-10,y:y+s.fontSize*.33,'text-anchor':'end','font-size':s.fontSize,fill:'#263738'},name);
      genes.forEach((gene,j)=>{
        const row=byKey.get(`${name}\t${gene}`);
        if(!row) throw Error(`Missing ${assay} value for ${name} / ${gene}`);
        const x=left+j*s.colWidth+s.colWidth/2;
        const fill=shade(row.scaled,min,max,$('figure1c-low').value,$('figure1c-mid').value,$('figure1c-high').value,Number($('figure1c-contrast').value));
        let mark;
        if(s.style==='heatmap') mark=svgNode(svg,'rect',{x:x-s.colWidth/2+2,y:y-s.rowHeight/2+2,width:s.colWidth-4,height:s.rowHeight-4,fill});
        else if(s.style==='squares') {const side=Math.max(1,2*s.size*Math.sqrt(row.fraction));mark=svgNode(svg,'rect',{x:x-side/2,y:y-side/2,width:side,height:side,fill});}
        else mark=svgNode(svg,'circle',{cx:x,cy:y,r:Math.max(.5,s.size*Math.sqrt(row.fraction)),fill});
        svgNode(mark,'title',{},`${name} · ${gene} · scaled mean ${row.scaled.toFixed(3)} · detected ${(100*row.fraction).toFixed(1)}%`);
      });
    });
    genes.forEach((gene,j)=>{
      const x=left+j*s.colWidth+s.colWidth/2,y=top+cells.length*s.rowHeight+10;
      svgNode(svg,'text',{transform:`translate(${x},${y}) rotate(-55)`,'text-anchor':'end','font-size':s.fontSize,fill:'#263738'},gene);
    });
    const legendY=height-30,legendX=left,lo=$('figure1c-low').value,mid=$('figure1c-mid').value,hi=$('figure1c-high').value,contrast=Number($('figure1c-contrast').value);
    for(let i=0;i<100;i++) {const v=min+(max-min)*(i+.5)/100;svgNode(svg,'rect',{x:legendX+i*3,y:legendY,width:3.2,height:12,fill:shade(v,min,max,lo,mid,hi,contrast)});}
    svgNode(svg,'text',{x:legendX,y:legendY-7,'font-size':11},`Within-gene scaled mean · ${min.toFixed(1)}`);
    svgNode(svg,'text',{x:legendX+300*(0-min)/(max-min),y:legendY-7,'font-size':11,'text-anchor':'middle'},'0');
    svgNode(svg,'text',{x:legendX+300,y:legendY-7,'font-size':11,'text-anchor':'end'},max.toFixed(1));
    if(s.style!=='heatmap') svgNode(svg,'text',{x:legendX+355,y:legendY+11,'font-size':11},'Dot area ∝ detected-cell fraction');
  }
  function render() {
    for(const assay of ['RNA','ATAC']) {const host=panels[assay].plot;host.replaceChildren();draw(assay,host);}
    $('figure1c-status').textContent='Plots updated. Add or remove measured markers and choose the cell types shown on each y-axis. The combined source mixes separately processed gene-wise scaled values.';
  }
  async function exportPdf(assays) {
    if(!window.jspdf?.jsPDF) throw Error('PDF library unavailable');
    const svgs=assays.map(a=>panels[a].plot.querySelector('svg'));
    if(svgs.some(x=>!x)) throw Error('Plot not ready');
    const width=1800,heights=svgs.map(svg=>Math.round(width*svg.viewBox.baseVal.height/svg.viewBox.baseVal.width));
    const canvas=document.createElement('canvas');canvas.width=width;canvas.height=heights.reduce((a,b)=>a+b,0)+24*(svgs.length-1);
    const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);
    let y=0;
    for(let i=0;i<svgs.length;i++) {
      const image=new Image();
      await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=reject;image.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(new XMLSerializer().serializeToString(svgs[i]));});
      ctx.drawImage(image,0,y,width,heights[i]);y+=heights[i]+24;
    }
    const pdf=new window.jspdf.jsPDF({orientation:'portrait',unit:'px',format:[canvas.width,canvas.height]});
    pdf.addImage(canvas.toDataURL('image/png'),'PNG',0,0,canvas.width,canvas.height);
    pdf.save(`TrackerSci_${assays.join('_')}_custom_markers.pdf`);
  }
  let panels={};
  for(const id of ['figure1c-low','figure1c-mid','figure1c-high','figure1c-contrast']) $(id).addEventListener('input',()=>{if(data.combined)render();});
  $('figure1c-reset').addEventListener('click',()=>{
    for(const [key,value] of Object.entries(defaults)) $(`figure1c-${key}`).value=value;
    for(const assay of ['RNA','ATAC']) {
      const s=state[assay],p=panels[assay];s.mode='paper';s.style=assay==='RNA'?'dots':'heatmap';s.markers=genesFor(assay,'paper');s.cells=[...axes[assay]];s.size=12;s.colWidth=40;s.rowHeight=29;s.fontSize=13;s.grid=false;
      p.source.value=s.mode;p.style.value=s.style;p.markerInput.value=s.markers.join(', ');p.size.value=s.size;p.colWidth.value=s.colWidth;p.rowHeight.value=s.rowHeight;p.fontSize.value=s.fontSize;p.grid.checked=false;p.refreshAvailable();p.refreshPickers();
    }
    render();
  });
  $('figure1c-export').addEventListener('click',()=>exportPdf(['RNA','ATAC']).catch(e=>{$('figure1c-status').textContent='PDF export failed: '+e.message;}));
  Promise.all([
    fetch('downloads/Figure_1C_publication_order_values.tsv').then(r=>{if(!r.ok)throw Error(`Figure 1C HTTP ${r.status}`);return r.text();}),
    fetch('downloads/TrackerSci_expanded_marker_values.tsv').then(r=>{if(!r.ok)throw Error(`Expanded markers HTTP ${r.status}`);return r.text();}),
    fetch('downloads/TrackerSci_microglia_extra_marker_values.tsv').then(r=>{if(!r.ok)throw Error(`Microglia markers HTTP ${r.status}`);return r.text();})
  ]).then(([paper,expanded,extra])=>{
    data.paper=parseTable(paper);data.expanded=parseTable(expanded);data.extra=parseTable(extra);
    const paperGenes=new Set(data.paper.map(row=>`${row.assay}\t${row.gene}`));
    const extraGenes=new Set(data.extra.map(row=>`${row.assay}\t${row.gene}`));
    data.combined=[...data.paper,...data.extra.filter(row=>!paperGenes.has(`${row.assay}\t${row.gene}`)),
      ...data.expanded.filter(row=>!paperGenes.has(`${row.assay}\t${row.gene}`)&&!extraGenes.has(`${row.assay}\t${row.gene}`))];
    checkTables();
    const container=$('figure1c-interactive');
    for(const assay of ['RNA','ATAC']) {state[assay].markers=genesFor(assay,'paper');state[assay].cells=[...axes[assay]];panels[assay]=makePanel(assay);container.append(panels[assay].panel);}
    render();
  }).catch(error=>{$('figure1c-status').textContent='Published marker values could not load: '+error.message;});
})();
