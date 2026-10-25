(() => {
  const section = document.getElementById('trackersci-figure1c-control');
  if (!section) return;
  const $ = id => document.getElementById(id);
  const NS = 'http://www.w3.org/2000/svg';
  const defaults = {low:'#3288bd', high:'#d53e4f', size:12};
  let rows = null;
  const svgNode = (parent, tag, attrs, label) => {
    const node = document.createElementNS(NS, tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
    if (label !== undefined) node.textContent = label;
    parent.appendChild(node);
    return node;
  };
  const channel = (a, b, t) => Math.round(a + (b-a)*Math.max(0,Math.min(1,t)));
  function mix(left, right, t) {
    const a = [1,3,5].map(i => parseInt(left.slice(i,i+2),16));
    const b = [1,3,5].map(i => parseInt(right.slice(i,i+2),16));
    return `rgb(${a.map((v,i)=>channel(v,b[i],t)).join(',')})`;
  }
  function shade(v, min, max, low, high) {
    return v < 0 ? mix(low,'#ffffff',(v-min)/(0-min)) : mix('#ffffff',high,v/max);
  }
  function parsed(text) {
    const lines = text.trimEnd().split(/\r?\n/);
    const fields = lines.shift().split('\t');
    if (fields.join('|') !== 'assay|cell_type|gene|mean_normalized|fraction_detected|scaled_mean') throw Error('Unexpected published marker table');
    return lines.map(line => {
      const parts = line.split('\t');
      if (parts.length !== 6) throw Error('Incomplete published marker row');
      return {assay:parts[0], cell:parts[1], gene:parts[2], mean:Number(parts[3]), fraction:Number(parts[4]), scaled:Number(parts[5])};
    });
  }
  function plot(assay, low, high, size) {
    const selected = rows.filter(row => row.assay === assay);
    const cells = [...new Set(selected.map(row => row.cell))];
    const genes = [...new Set(selected.map(row => row.gene))];
    const expected = assay === 'RNA' ? 16 : 14;
    if (cells.length !== expected || genes.length !== expected || selected.length !== expected*expected) throw Error('Published marker axes changed');
    const byKey = new Map(selected.map(row => [`${row.cell}\t${row.gene}`,row]));
    const min = Math.min(...selected.map(row => row.scaled));
    const max = Math.max(...selected.map(row => row.scaled));
    const left=295, top=36, cellWidth=40, rowHeight=29, bottom=150;
    const width=left+genes.length*cellWidth+50;
    const height=top+cells.length*rowHeight+bottom;
    const holder = document.createElement('div');
    holder.className='figure1c-plot';
    const heading=document.createElement('h3');
    heading.textContent=assay === 'RNA' ? 'Published RNA marker dotplot' : 'Published ATAC gene-activity heatmap';
    holder.appendChild(heading);
    const svg=svgNode(holder,'svg',{viewBox:`0 0 ${width} ${height}`,role:'img','aria-label':heading.textContent});
    svgNode(svg,'rect',{x:0,y:0,width,height,fill:'#ffffff'});
    cells.forEach((name,i)=>{
      const y=top+i*rowHeight+rowHeight/2;
      svgNode(svg,'text',{x:left-10,y:y+4,'text-anchor':'end','font-size':13,fill:'#263738'},name);
      genes.forEach((gene,j)=>{
        const row=byKey.get(`${name}\t${gene}`);
        if (!row) throw Error('Missing published marker value');
        const x=left+j*cellWidth+cellWidth/2;
        const fill=shade(row.scaled,min,max,low,high);
        const mark=assay === 'RNA'
          ? svgNode(svg,'circle',{cx:x,cy:y,r:size*Math.sqrt(Math.max(0,Math.min(1,row.fraction))),fill})
          : svgNode(svg,'rect',{x:x-cellWidth/2+2,y:y-rowHeight/2+2,width:cellWidth-4,height:rowHeight-4,fill});
        svgNode(mark,'title',{},`${name} · ${gene} · scaled mean ${row.scaled.toFixed(3)} · detected ${(100*row.fraction).toFixed(1)}%`);
      });
    });
    genes.forEach((gene,j)=>{
      const x=left+j*cellWidth+cellWidth/2, y=top+cells.length*rowHeight+9;
      svgNode(svg,'text',{transform:`translate(${x},${y}) rotate(-55)`,'text-anchor':'end','font-size':13,fill:'#263738'},gene);
    });
    const legendY=height-32, legendX=left;
    for(let i=0;i<100;i++){
      const v=min+(max-min)*(i+.5)/100;
      svgNode(svg,'rect',{x:legendX+i*3,y:legendY,width:3.2,height:12,fill:shade(v,min,max,low,high)});
    }
    svgNode(svg,'text',{x:legendX,y:legendY-7,'font-size':11},`Gene-wise scaled mean · ${min.toFixed(1)}`);
    svgNode(svg,'text',{x:legendX+300*(0-min)/(max-min),y:legendY-7,'font-size':11,'text-anchor':'middle'},'0');
    svgNode(svg,'text',{x:legendX+300,y:legendY-7,'font-size':11,'text-anchor':'end'},max.toFixed(1));
    if(assay === 'RNA') svgNode(svg,'text',{x:legendX+355,y:legendY+11,'font-size':11},'Dot area ∝ detected-cell fraction');
    return holder;
  }
  function render() {
    if (!rows) return;
    const low=$('figure1c-low').value,high=$('figure1c-high').value,size=Number($('figure1c-size').value);
    const container=$('figure1c-interactive');
    container.replaceChildren(plot('RNA',low,high,size),plot('ATAC',low,high,size));
    $('figure1c-status').textContent=`Published marker values loaded · low ${low} / high ${high}; original cell-type and gene order retained.`;
  }
  async function exportPdf() {
    const svgs=[...$('figure1c-interactive').querySelectorAll('svg')];
    if(svgs.length !== 2 || !window.jspdf?.jsPDF) return;
    const width=1800, heights=svgs.map(svg=>Math.round(width*svg.viewBox.baseVal.height/svg.viewBox.baseVal.width));
    const canvas=document.createElement('canvas');canvas.width=width;canvas.height=heights[0]+heights[1]+24;
    const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);
    let y=0;
    for(let i=0;i<svgs.length;i++){
      const image=new Image();
      await new Promise((resolve,reject)=>{
        image.onload=resolve;image.onerror=reject;
        image.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(new XMLSerializer().serializeToString(svgs[i]));
      });
      ctx.drawImage(image,0,y,width,heights[i]);y+=heights[i]+24;
    }
    const pdf=new window.jspdf.jsPDF({orientation:'portrait',unit:'px',format:[canvas.width,canvas.height]});
    pdf.addImage(canvas.toDataURL('image/png'),'PNG',0,0,canvas.width,canvas.height);
    pdf.save('TrackerSci_Figure1C_recolored.pdf');
  }
  for(const id of ['figure1c-low','figure1c-high','figure1c-size']) $(id).addEventListener('input',()=>{try{render();}catch(e){$('figure1c-status').textContent=e.message;}});
  $('figure1c-reset').addEventListener('click',()=>{for(const [id,value] of Object.entries({'figure1c-low':defaults.low,'figure1c-high':defaults.high,'figure1c-size':defaults.size}))$(id).value=value;render();});
  $('figure1c-export').addEventListener('click',()=>exportPdf().catch(e=>{$('figure1c-status').textContent='PDF export failed: '+e.message;}));
  fetch('downloads/Figure_1C_publication_order_values.tsv').then(response=>{if(!response.ok)throw Error('HTTP '+response.status);return response.text();}).then(text=>{rows=parsed(text);render();}).catch(error=>{$('figure1c-status').textContent='Published marker values could not load: '+error.message;});
})();
