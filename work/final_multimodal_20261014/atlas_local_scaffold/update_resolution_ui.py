from pathlib import Path
p=Path('outputs/p5_workflow/full_workflow_20261014/atlas_preview/app.js')
s=p.read_text()
s=s.replace("const D=window.ATLAS_DATA,C=window.AtlasCore,$=id=>document.getElementById(id),nf=new Intl.NumberFormat('en-US');", "const registry=window.ATLAS_DATASET_REGISTRY,C=window.AtlasCore,$=id=>document.getElementById(id),nf=new Intl.NumberFormat('en-US');\nlet D=registry['0.6|corrected'];")
s=s.replace('const mapped=new Map', 'let mapped=new Map')
s=s.replace("attrs:null,zoom:", "attrs:null,resolutionLabels:{},switchId:0,zoom:")
s=s.replace("subject:'Provisional GSE212606 initial ATAC atlas; source job 7466270'", "subject:'Provisional GSE212606 initial ATAC atlas; '+datasetContext()")
s=s.replace("keywords:'ATAC,provisional,animal-balanced,7466270'", "keywords:'ATAC,provisional,animal-balanced,'+D.job_id")
s=s.replace("doc.text('GSE212606 | Initial ATAC | Job 7466270 | PROVISIONAL - final QC and identities pending',margin,27);", "doc.text('GSE212606 | Job '+D.job_id+' | Leiden '+D.resolution.toFixed(1)+' / '+D.partition_graph+' | PROVISIONAL - final QC and identities pending',margin,27);")
s=s.replace("doc.text('Source: accepted initial job 7466270; Leiden 0.6; completed 2026-10-14 08:22 UTC. Exported '+new Date().toISOString(),margin,h-11);", "doc.text(datasetContext()+' | Exported '+new Date().toISOString(),margin,h-11);")
s=s.replace("doc.save(name);", "doc.save(D.dataset_id+'_'+name);")
s=s.replace("function saveLabels(){", "function datasetContext(){return 'Source job '+D.job_id+'; Leiden '+D.resolution.toFixed(1)+'; '+D.partition_graph+' partition; coordinate producer 7466270';}\nfunction labelPayload(){return{schema_version:'1.1',dataset_id:D.dataset_id,resolution:D.resolution,partition_graph:D.partition_graph,display_only:true,labels:state.labels};}\nfunction saveLabels(){")
s=s.replace("JSON.stringify({dataset_id:D.dataset_id,labels:state.labels})", "JSON.stringify(labelPayload())")
start=s.index('function init(){')
end=s.index('\nfunction renderChips()',start)
s=s[:start]+'''function configureDataset(){
 mapped=new Map(D.genes.map(g=>[g.symbol,g.mapped]));animalMap=new Map(D.animals.map(a=>[a.id,a]));state.clusters=new Set(D.clusters.map(c=>c.id));state.labels={};
 try{const raw=localStorage.getItem('atlas_display_labels_'+D.dataset_id);if(raw)state.labels=C.validateLabels(JSON.parse(raw),D.clusters,D.dataset_id);}catch(e){state.labels={};}
 for(const[id,key,all]of [['genotype','genotype','All genotypes'],['condition','condition','All conditions'],['animal','id','All animals']]){const previous=$(id).value;$(id).replaceChildren();option($(id),'',all);[...new Set(D.animals.map(a=>a[key]))].sort().forEach(x=>option($(id),x,x));if([...$(id).options].some(o=>o.value===previous))$(id).value=previous;}
 $('rankCluster').replaceChildren();D.clusters.forEach(c=>option($('rankCluster'),c.id,'Cluster '+c.id+' · '+c.candidate));
 $('boxGene').replaceChildren();D.genes.forEach(g=>option($('boxGene'),g.symbol,g.symbol+(g.mapped?'':' · NA')));$('boxGene').value='P2ry12';
 $('activeSource').textContent='Label / marker producer '+D.job_id;
 $('partitionDescription').textContent=(D.partition_graph==='corrected'?'PCR Harmony':'Uncorrected')+' graph · Leiden '+D.resolution.toFixed(1);
 $('resolutionStatus').textContent='Leiden '+D.resolution.toFixed(1)+' · '+D.partition_graph+' partition · '+D.clusters.length+' actual clusters. '+(D.activity_available?'Fresh summaries specific to this partition are available.':'Labels and composition are available; marker/activity summaries for this original uncorrected partition were not produced, so activity plots are unavailable.')+' Coordinate selection is independent; all identities remain provisional.';
 $('microglia').disabled=!D.microglia_candidate_cluster;$('microglia').title=D.microglia_candidate_cluster?'Initial corrected cluster 6 only':'A microglia cluster has not been independently assigned for this partition. Use the microglia marker panel across all clusters.';
 const unavailable=!D.activity_available,message='No gene-body activity summaries were produced for resolution 0.6 on the uncorrected graph. Select the corrected graph or either verified resolution-1 partition. Corrected marker means are never reused here.';
 for(const id of ['markerUnavailable','animalUnavailable']){$(id).hidden=!unavailable;$(id).textContent=message;}
 for(const id of ['dotPlotArea','dotScale','animalPlotArea'])$(id).hidden=unavailable;
 for(const id of ['exportDot','exportDotData','exportAnimalPlot','exportAnimals','rankGenes','boxGene','boxGroup','applyGenes'])$(id).disabled=unavailable;
 $('statusGrid').replaceChildren();for(const[key,value]of Object.entries({...D.status,'Selected partition':D.resolution.toFixed(1)+' / '+D.partition_graph+'; '+D.clusters.length+' actual clusters','Activity summaries':D.activity_available?'Own selected 107-gene diagnostic panel; not genome-wide top DE markers':'Unavailable for this partition; no cross-partition reuse','Resolution 1.0':'Both 12-cluster partitions completed in producer 7470007; package 7470531 verified'})){const e=document.createElement('div');if(key==='Selected partition'||key==='Activity summaries'&&D.activity_available)e.className='available';const b=document.createElement('b'),q=document.createElement('p');b.textContent=key;q.textContent=value;e.append(b,q);$('statusGrid').append(e);}
 $('sourceList').replaceChildren();for(const r of D.source_records){const e=document.createElement('div');e.className='sourceitem';const q=document.createElement('div'),h=document.createElement('code');q.textContent=r.path;h.textContent=r.sha256+' · '+nf.format(r.bytes)+' bytes';e.append(q,h);$('sourceList').append(e);}
 $('activeProvenance').textContent=datasetContext()+'. '+(D.package_job_id?'Validated package '+D.package_job_id+'; manifest '+D.package_manifest_sha256+'. ':'')+'The existing UMAP coordinates are reused unchanged on the exact ordered cell axis. No raw CSR matrix, graph, or embedding was read or recomputed for this import. Display labels are isolated by resolution and graph. Animals remain biological replicates.';
 renderChips();renderLabelEditor();selectPanel();render();
}
async function ensureResolutionLabels(){
 if(state.resolutionLabels.corrected)return;
 await loadScript(window.ATLAS_RESOLUTION_REGISTRY_CONFIG.package_path+'validated_products/resolution1_labels.js');const a=window.ATLAS_RESOLUTION1_LABELS,cfg=window.ATLAS_RESOLUTION_REGISTRY_CONFIG;
 if(a.n_cells!==456472||a.ordered_cell_ids_sha256!==cfg.ordered_cell_ids_sha256)throw Error('Resolution-1 label cell axis mismatch.');
 for(const branch of ['corrected','uncorrected']){const q=a.branches[branch],b=decode64(q.base64);if(q.n!==456472||q.dtype!=='uint16-little-endian'||b.length!==456472*2)throw Error('Resolution-1 label format mismatch.');const v=new DataView(b.buffer,b.byteOffset,b.byteLength),out=new Uint16Array(q.n);for(let i=0;i<out.length;i++){out[i]=v.getUint16(i*2,true);if(out[i]>=q.labels.length)throw Error('Resolution-1 label dictionary mismatch.');}state.resolutionLabels[branch]=out;delete q.base64;}
}
async function switchDataset(){const ticket=++state.switchId,key=window.ATLAS_ACTIVE_DATASET_KEY($('resolution').value,$('partitionGraph').value);try{if(key.startsWith('1.0'))await ensureResolutionLabels();if(ticket!==state.switchId)return;saveLabels();D=registry[key];if(!D)throw Error('Selected actual partition is unavailable.');configureDataset();toast('Loaded '+D.clusters.length+' actual '+D.partition_graph+' clusters at Leiden '+D.resolution.toFixed(1)+'.');}catch(e){toast(e.message);$('resolution').value=D.resolution.toFixed(1);$('partitionGraph').value=D.partition_graph;}}
function init(){
 Object.keys(D.panels).forEach(p=>option($('panel'),p,p.replaceAll('_',' ')));
 D.pdfs.forEach(p=>{const a=document.createElement('a');a.href=p.path;a.textContent=p.label+' ↗';a.target='_blank';a.rel='noopener';$('pdfLinks').appendChild(a);});
 ['condition','genotype','animal','sex'].forEach(id=>$(id).addEventListener('change',render));['resolution','partitionGraph'].forEach(id=>$(id).addEventListener('change',switchDataset));['valueMode','groupBy','geneOrder','palette'].forEach(id=>$(id).addEventListener('change',()=>{renderChips();render();}));$('panel').onchange=()=>{selectPanel();render();};$('applyGenes').onclick=()=>{parseGenes();render();};$('geneInput').onkeydown=e=>{if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){parseGenes();render();}};
 $('boxGene').onchange=renderBox;$('boxGroup').onchange=renderBox;$('rankGenes').onclick=rankGenes;$('reset').onclick=reset;
 $('microglia').onclick=()=>{if(!D.microglia_candidate_cluster)return;state.clusters=new Set([D.microglia_candidate_cluster]);$('panel').value='microglia';$('boxGene').value='P2ry12';selectPanel();renderChips();render();$('umap').scrollIntoView({behavior:'smooth'});toast('Initial corrected resolution-0.6 cluster 6 is a provisional microglia-associated candidate, not a final label.');};
 $('exportLabels').onclick=()=>download(D.dataset_id+'_display_labels.json',JSON.stringify(labelPayload(),null,2),'application/json');$('importLabels').onchange=importLabels;$('resetLabels').onclick=()=>{state.labels={};saveLabels();renderLabelEditor();renderChips();render();};
 $('exportDot').onclick=()=>plotPDF('dotCanvas','ATAC_activity_dotplot.pdf','ATAC gene-body activity dotplot','dot');$('exportUmap').onclick=()=>plotPDF('umapCanvas','ATAC_initial_'+$('embedding').value+'_UMAP.pdf','Initial ATAC '+$('embedding').selectedOptions[0].text+' UMAP');$('exportAnimalPlot').onclick=()=>plotPDF('boxCanvas','ATAC_animal_activity.pdf','ATAC activity by animal','box');$('exportComposition').onclick=()=>plotPDF('compositionCanvas','ATAC_initial_cluster_composition.pdf','Initial cluster composition by condition','comp');$('exportDotData').onclick=()=>download(D.dataset_id+'_activity_dotplot_values.tsv',tsv(state.dotRows,['source_job','resolution','partition_graph','group','gene','n','nAnimals','raw','normalized','detection','zscore','color_value','mapped']),'text/tab-separated-values');$('exportAnimals').onclick=()=>download(D.dataset_id+'_animal_activity.tsv',tsv(state.animalRows,['source_job','resolution','partition_graph','group','animal','condition','genotype','gene','n','rawSum','raw','normalized','detection']),'text/tab-separated-values');
 $('loadUmap').onclick=loadUmap;$('embedding').onchange=()=>{state.zoom={scale:1,tx:0,ty:0};if(state.attrs)loadUmap();};$('umapColor').onchange=renderScatter;$('umapReset').onclick=()=>{state.zoom={scale:1,tx:0,ty:0};renderScatter();};window.addEventListener('resize',()=>{if(state.attrs)renderScatter();});setupScatterGestures();configureDataset();
}''' +s[end:]
s=s.replace("state.clusters.size===11?'all 11 selected'", "state.clusters.size===D.clusters.length?'all '+D.clusters.length+' selected'")
s=s.replace("if(state.clusters.has(c.id)){if(state.clusters.size===1)return toast('Keep at least one cluster selected.');state.clusters.delete(c.id);}","if(state.clusters.has(c.id)){state.clusters.delete(c.id);}")
s=s.replace("function renderDot(){const", "function renderDot(){if(!D.activity_available){state.dotRows=[];if(state.charts.dot){state.charts.dot.destroy();delete state.charts.dot;}return;}const")
s=s.replace("({...r,mapped:mapped.get(r.gene)", "({...r,source_job:D.job_id,resolution:D.resolution,partition_graph:D.partition_graph,mapped:mapped.get(r.gene)")
s=s.replace("function renderBoxGroups(){const", "function renderBoxGroups(){if(!D.activity_available){$('boxGroup').replaceChildren();return;}const")
s=s.replace("function renderBox(){const", "function renderBox(){if(!D.activity_available){state.animalRows=[];if(state.charts.box){state.charts.box.destroy();delete state.charts.box;}return;}const")
s=s.replace("({...r,mapped:mapped.get(gene)", "({...r,source_job:D.job_id,resolution:D.resolution,partition_graph:D.partition_graph,mapped:mapped.get(gene)")
s=s.replace("for(const r of D.records){if(r[2]!==D.genes[0].symbol||!set.has(r[1])||!state.clusters.has(String(r[0])))continue;", "for(const r of C.coverageRows(D)){if(!set.has(r[1])||!state.clusters.has(String(r[0])))continue;")
s=s.replace("counts[key]=(counts[key]||0)+r[3];", "counts[key]=(counts[key]||0)+r[2];")
s=s.replace("categorical(+c.id,11)", "categorical(D.clusters.findIndex(q=>q.id===c.id),D.clusters.length)")
s=s.replace("function rankGenes(){const", "function rankGenes(){if(!D.activity_available)return;const")
s=s.replace("C.validateLabels(JSON.parse(await f.text()),D.clusters)", "C.validateLabels(JSON.parse(await f.text()),D.clusters,D.dataset_id)")
s=s.replace("if(mode==='uncorrected')return Array.from({length:9},(_,i)=>'Uncorrected '+i);", "")
a=s.index('function pointKey(i)');b=s.index('\nfunction renderScatter()',a)
s=s[:a]+"function activeCluster(i){return D.resolution===1?D.label_dictionary[state.resolutionLabels[D.partition_graph][i]]:String(state.attrs[i*3+(D.partition_graph==='corrected'?0:1)]);}\nfunction pointKey(i){const mode=$('umapColor').value,c=activeCluster(i),a=state.pointAnimals[state.attrs[i*3+2]];return mode==='cluster'?(state.labels[c]||'Cluster '+c):mode==='animal'?a.id:a[mode];}"+s[b:]
s=s.replace("const c=String(state.attrs[i*3]),a=state.pointAnimals", "const c=activeCluster(i),a=state.pointAnimals")
s=s.replace("const i=best[2],c=state.attrs[i*3],u=state.attrs[i*3+1],a=state.pointAnimals", "const i=best[2],c=activeCluster(i),a=state.pointAnimals")
s=s.replace("tip.textContent='Initial cluster '+c+' · '+(state.labels[c]||'display label unset')+' | '+a.id+' | uncorrected '+u+' | source row '+(i+1)", "tip.textContent='Leiden '+D.resolution.toFixed(1)+' / '+D.partition_graph+' cluster '+c+' · '+(state.labels[c]||'display label unset')+' | '+a.id+' | source row '+(i+1)")
s=s.replace("window.ATLAS_PREVIEW={state,data:D,filters,render,core:C};init();", "window.ATLAS_PREVIEW={state,get data(){return D;},registry,filters,render,core:C,switchDataset,activeCluster};init();")
p.write_text(s)
