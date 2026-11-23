/* Microglial TE RNA and TE-body accessibility, aligned by the original display bins. */
(async function () {
  const root = document.getElementById('tc-view');
  if (!root) return;
  const clusterInfo = [
    ['C1','WT21_RNA_specific','WT 21 mo-specific RNA',66522,'#36769a'],
    ['C2','5xFAD_RNA_specific','5xFAD-specific RNA',38620,'#9a5773'],
    ['C3','WT21_additional','Higher in WT 21 mo',72749,'#59868d'],
    ['C4','5xFAD_additional','Higher in 5xFAD',54337,'#946649'],
    ['C5','both_targets','Higher in both targets',34810,'#746591']
  ];
  const groups = ['WT_3mo','WT_21mo','5xFAD_3mo'];
  const conditions = ['WT 3 mo','WT 21 mo','5xFAD 3 mo'];
  const assays = ['RNA','ATAC'];
  const units = ['TE RNA per million gene UMIs','Fold of mouse genome-wide ATAC coverage'];
  const data = new Map(clusterInfo.map(([,block]) => [block,[]]));
  try {
    const response = await fetch('downloads/Microglia_TE_C1-C5_bins.tsv');
    if (!response.ok) throw Error('Download failed');
    const lines = (await response.text()).trim().split(/\r?\n/);
    const columns = lines.shift().split('\t');
    const features = ['_RNA_per_M_gene_UMI','_ATAC_relative_coverage'].map(suffix =>
      groups.map(group => columns.indexOf(group + suffix)));
    for (const line of lines) {
      const items = line.split('\t');
      const block = data.get(items[columns.indexOf('figure_block')]);
      const values = features.map(cols => cols.map(i => Number(items[i])));
      const copies = Number(items[columns.indexOf('copies')]);
      if (!block || Number(items[columns.indexOf('figure_bin')]) !== block.length+1 ||
          !Number.isInteger(copies) || copies < 1 || !values.flat().every(v => Number.isFinite(v) && v >= 0))
        throw Error('Invalid heatmap values');
      block.push({values,copies});
    }
    for (const [,block,,count] of clusterInfo) {
      if (data.get(block).reduce((n,r) => n+r.copies,0) !== count) throw Error('Cluster size mismatch');
    }
  } catch (e) {
    root.innerHTML = '<p role="alert">The interactive heatmap could not load. The figure and per-copy downloads are available on this page. <button type="button">Retry</button></p>';
    root.querySelector('button').addEventListener('click', () => location.reload());
    return;
  }

  function percentile95(assay) {
    const v = Array.from(data.values()).flat().flatMap(r => r.values[assay]).sort((a,b) => a-b);
    const pos = (v.length-1)*0.95;
    return v[Math.floor(pos)] + (pos%1)*(v[Math.ceil(pos)]-v[Math.floor(pos)]);
  }
  const caps = [percentile95(0),percentile95(1)];
  const palettes = [['#3288bd','#f7f7f7','#d53e4f'],['#4d9221','#f7f7f7','#c51b7d']];
  const selectOptions = values => values.map(([value,name]) => '<option value="'+value+'">'+name+'</option>').join('');
  const seq = ['012','021','102','120','201','210'];
  function assayControls(name,i) {
    const colors = ['Low','Middle','High'].map((label,j) =>
      '<label>'+label+'<input type="color" aria-label="'+name+' '+label+' color" data-field="color'+j+'" value="'+palettes[i][j]+'"></label>').join('');
    return '<fieldset data-assay="'+i+'"><legend>'+name+'</legend><div class="tc-inputs">'+colors+
      '</div><div class="tc-inputs"><label>Minimum<input data-field="min" type="number" min="0" step="any" value="0" required></label>'+
      '<label>Maximum<input data-field="max" type="number" min="0" step="any" value="'+caps[i].toPrecision(7)+'" required></label>'+
      '<label>Color spacing<select data-field="transform"><option value="log">Log(1 + signal)</option><option value="linear">Linear</option></select></label></div></fieldset>';
  }
  root.innerHTML = '<details open><summary>RNA and ATAC colors and scales</summary><div class="tc-assays">'+assays.map(assayControls).join('')+
    '</div></details><details><summary>Cluster location, color, size and sequence</summary><div class="tc-inputs">'+
    '<label>Cluster<select id="tc-cluster">'+selectOptions(clusterInfo.map(([id,,label]) => [id,id+' · '+label]))+'</select></label>'+
    '<label>Position in figure<select id="tc-pos">'+selectOptions([1,2,3,4,5].map(i=>[i,i]))+'</select></label>'+
    '<label>Label color<input id="tc-accent" type="color"></label>'+
    '<label>Block height (% of default)<input id="tc-height" type="number" min="40" max="300" step="1" required></label>'+
    '<label>Within-cluster sequence<select id="tc-reverse"><option value="0">Original RNA rank</option><option value="1">Reverse RNA rank</option></select></label></div>'+
    '<div class="tc-inputs"><label>RNA maximum for this cluster<input type="number" min="0" step="any" id="tc-rna-cap" placeholder="Panel max"></label>'+
    '<label>ATAC maximum for this cluster<input type="number" min="0" step="any" id="tc-atac-cap" placeholder="Panel max"></label>'+
    '<label>Condition order in both panels<select id="tc-columns">'+selectOptions(seq.map(s=>[s,[...s].map(i=>conditions[i]).join(' → ')]))+'</select></label></div></details>'+
    '<div class="tc-actions"><button type="button" id="tc-export" class="secondary">Download edited figure · SVG</button>'+
    '<button type="button" id="tc-reset" class="secondary">Reset figure</button></div><p class="tc-error" role="status"></p>'+
    '<div class="tc-scroll" id="tc-drawing"></div>';
  const q = sel => root.querySelector(sel);
  const input = id => q('#tc-'+id);
  const settings = new Map();
  let order;
  function resetClusters() {
    order = clusterInfo.map(c=>c[0]);
    for (const [id,block,label,n,color] of clusterInfo)
      settings.set(id,{id,block,label,n,color,height:100,reverse:'0',cap:['','']});
  }
  const current = () => settings.get(input('cluster').value);
  function reflectCluster() {
    const c=current();
    input('pos').value = order.indexOf(c.id)+1;
    input('height').value=c.height;
    input('accent').value=c.color;
    input('reverse').value=c.reverse;
    input('rna-cap').value=c.cap[0];
    input('atac-cap').value=c.cap[1];
  }
  resetClusters();
  reflectCluster();
  const fmt = n => Number(n.toPrecision(3)).toString();
  const assaySettings = () => assays.map((_,i) => {
    const field = key => q('[data-assay="'+i+'"] [data-field="'+key+'"]');
    return {min:field('min').valueAsNumber,max:field('max').valueAsNumber,
      log:field('transform').value==='log',colors:[0,1,2].map(n=>field('color'+n).value)};
  });
  function palette(colors) {
    const channels = colors.map(c=>[1,3,5].map(n=>parseInt(c.slice(n,n+2),16)));
    return Array.from({length:257},(_,i)=>{
      const a = i<=128 ? 0 : 1, t=(i-a*128)/128;
      return '#'+channels[a].map((v,k)=>Math.round(v+(channels[a+1][k]-v)*t).toString(16).padStart(2,'0')).join('');
    });
  }
  const transform=(v,log)=>log ? Math.log1p(v) : v;
  function render() {
    const styles=assaySettings();
    let message='';
    for (const [i,s] of styles.entries()) {
      if (!(s.min>=0 && s.max>s.min)) message=assays[i]+' needs a nonnegative minimum and a larger maximum.';
      for (const c of settings.values())
        if (c.cap[i]!=='' && !(Number(c.cap[i])>s.min)) message=c.id+' needs a '+assays[i]+' maximum above the panel minimum.';
    }
    if (!input('height').validity.valid) message='Choose a cluster height from 40 to 300 percent.';
    if ([input('rna-cap'),input('atac-cap')].some(e=>e.validity.badInput)) message='Enter a numeric cluster maximum, or clear it to use the panel scale.';
    q('.tc-error').textContent=message;
    input('export').disabled=Boolean(message);
    if (message) return;
    const columns=[...input('columns').value].map(Number);
    const xs=[248,558],w=280;
    const lookups=styles.map(s=>palette(s.colors));
    const svg=[];
    const txt=(x,y,str,opt='')=>svg.push('<text x="'+x+'" y="'+y+'" '+opt+'>'+str+'</text>');
    const rect=(x,y,w,h,color,opt='')=>svg.push('<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" fill="'+color+'" '+opt+'/>');
    const bold='font-weight="700"', mid='text-anchor="middle"';
    txt(12,28,'Microglial TE RNA and ATAC coverage',bold+' font-size="22"');
    txt(12,50,'WT 21 mo and 5xFAD 3 mo compared with WT 3 mo','font-size="14"');
    xs.forEach((x,j)=>txt(x+w/2,83,['TE RNA expression','ATAC coverage over the TE'][j],mid+' '+bold+' font-size="15"'));
    let y=96;
    for (const id of order) {
      const c=settings.get(id),h=100*c.height/100;
      const rows=data.get(c.block);
      rect(12,y+4,4,h-8,c.color);
      txt(25,y+h/2-3,id+' · '+c.label,bold+' font-size="14"');
      txt(25,y+h/2+15,c.n.toLocaleString('en-US')+' copies','font-size="12"');
      if (c.cap.some(v=>v!=='')) txt(25,y+h/2+29,c.cap.map((v,j)=>v===''?'':assays[j]+' max '+fmt(Number(v))).filter(Boolean).join(' · '),'font-size="10"');
      for (let j=0;j<2;j++) {
        const s=styles[j], low=transform(s.min,s.log), high=transform(Number(c.cap[j]||s.max),s.log);
        // Group equal colors into paths; all six display columns use the same bins.
        const paths=new Map();
        rows.forEach((row,index)=>{
          const rowIndex=c.reverse==='1'?rows.length-index-1:index;
          columns.forEach((column,k)=>{
            const value=transform(row.values[j][column],s.log);
            const t=Math.max(0,Math.min(1,(value-low)/(high-low)));
            const color=lookups[j][Math.round(256*t)];
            if(!paths.has(color)) paths.set(color,[]);
            paths.get(color).push('M'+k+' '+rowIndex+'h1v1h-1z');
          });
        });
        svg.push('<g data-cluster="'+id+'" data-panel="'+assays[j]+'" shape-rendering="crispEdges" transform="translate('+xs[j]+' '+y+') scale('+w/3+' '+h/rows.length+')">');
        for(const [color,parts] of paths) svg.push('<path fill="'+color+'" d="'+parts.join('')+'"/>');
        svg.push('</g>');
      }
      y+=h+12;
    }
    for(let j=0;j<2;j++) {
      const x=xs[j],s=styles[j],colors=s.colors;
      columns.forEach((k,col)=>txt(x+(col+.5)*w/3,y+5,conditions[k],mid+' font-size="12"'));
      svg.push('<defs><linearGradient id="tc-gradient-'+j+'">'+colors.map((c,i)=>'<stop offset="'+i*50+'%" stop-color="'+c+'"/>').join('')+'</linearGradient></defs>');
      rect(x,y+25,w,10,'url(#tc-gradient-'+j+')');
      for (const fraction of [0,.5,1]) {
        const transformed=transform(s.min,s.log)+fraction*(transform(s.max,s.log)-transform(s.min,s.log));
        const value=s.log?Math.expm1(transformed):transformed;
        const align=fraction===0?'start':fraction===1?'end':'middle';
        txt(x+w*fraction,y+49,(fraction===1?'≥':'')+fmt(value),'text-anchor="'+align+'" font-size="11"');
      }
      txt(x+w/2,y+68,units[j],mid+' font-size="12"');
      txt(x+w/2,y+84,s.log?'Log(1 + signal) spacing':'Linear spacing',mid+' font-size="11"');
    }
    txt(12,y+113,'Each display row averages the same RNA-ranked TE copies in both panels.','font-size="12"');
    txt(12,y+131,'Mice per group (WT 3 mo / WT 21 mo / 5xFAD): RNA 4 / 3 / 4, ATAC 4 / 4 / 4.','font-size="12"');
    const height=y+148;
    input('drawing').innerHTML='<svg xmlns="http://www.w3.org/2000/svg" width="858" height="'+height+'" viewBox="0 0 858 '+height+'" role="img" aria-labelledby="tc-svg-title" font-family="Arial, sans-serif" fill="#213a40"><title id="tc-svg-title">Microglial TE RNA and ATAC coverage, clusters '+order.join(', ')+'</title><rect width="100%" height="100%" fill="white"/>'+svg.join('')+'</svg>';
  }
  root.addEventListener('input',event=>{
    const e=event.target,c=current();
    if(e===input('cluster')) reflectCluster();
    if(e===input('pos')) {
      order.splice(order.indexOf(c.id),1);
      order.splice(Number(e.value)-1,0,c.id);
    }
    if(e===input('accent')) c.color=e.value;
    if(e===input('height') && e.validity.valid) c.height=e.valueAsNumber;
    if(e===input('reverse')) c.reverse=e.value;
    if(e===input('rna-cap')) c.cap[0]=e.value;
    if(e===input('atac-cap')) c.cap[1]=e.value;
    render();
  });
  input('reset').addEventListener('click',()=>{
    root.querySelectorAll('[data-assay] input').forEach(e=>e.value=e.defaultValue);
    root.querySelectorAll('select').forEach(e=>e.selectedIndex=0);
    resetClusters();reflectCluster();render();
  });
  input('export').addEventListener('click',()=>{
    const markup=new XMLSerializer().serializeToString(q('svg'));
    const url=URL.createObjectURL(new Blob([markup],{type:'image/svg+xml'}));
    const a=document.createElement('a');a.href=url;a.download='Microglia_TE_C1-C5_edited.svg';a.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  render();
})();
