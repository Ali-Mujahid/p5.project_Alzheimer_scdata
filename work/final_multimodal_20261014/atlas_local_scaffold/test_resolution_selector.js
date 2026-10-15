'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),vm=require('node:vm'),crypto=require('node:crypto');
const base=path.resolve('outputs/p5_workflow/full_workflow_20261014/atlas_preview'),pkg=path.resolve('outputs/p5_workflow/ATAC_initial_atlas_20261014/job-7470007/resolution1_package_job-7470531/validated_products'),C=require(path.join(base,'atlas_core.js'));
const context={window:{}};vm.createContext(context);
for(const file of [path.join(base,'data_adapter.js'),path.join(pkg,'corrected_activity_adapter.js'),path.join(pkg,'uncorrected_activity_adapter.js'),path.join(base,'resolution_registry.js'),path.join(base,'resolution_datasets.js'),path.join(base,'point_attributes.js'),path.join(pkg,'resolution1_labels.js')])vm.runInContext(fs.readFileSync(file,'utf8'),context,{filename:file});
const R=context.window.ATLAS_DATASET_REGISTRY,L=context.window.ATLAS_RESOLUTION1_LABELS,attrs=Buffer.from(context.window.ATLAS_POINT_ATTRIBUTES.base64,'base64'),html=fs.readFileSync(path.join(base,'index.html'),'utf8'),app=fs.readFileSync(path.join(base,'app.js'),'utf8');let checks=0;function ok(condition,message){assert.ok(condition,message);checks++;}
const expected={'0.6|corrected':11,'0.6|uncorrected':9,'1.0|corrected':12,'1.0|uncorrected':12};
for(const[key,n]of Object.entries(expected)){
 const D=R[key];ok(D.clusters.length===n,key+' actual count');ok(D.clusters.reduce((s,c)=>s+c.n,0)===456472,key+' total');ok(C.coverage(D).n===456472,key+' actual coverage');ok(C.coverage(D,{clusters:[]}).n===0,key+' empty selection');ok(C.coverage(D,{sex:'female'}).animals===10,key+' female filter');ok(C.allowedAnimals(D,{genotype:'APOE4/TREM2'}).length===4,key+' canonical genotype');
 for(const a of D.animals)ok(C.coverage(D,{animal:a.id}).n===a.n_initial_cells,key+' animal '+a.id);
 ok(D.microglia_candidate_cluster===(key==='0.6|corrected'?'6':null),key+' no numeric identity inheritance');
 const q=C.aggregate(D,{},{});if(!D.activity_available){ok(q.summary.length===0,key+' own activity unavailable');continue;}
 ok(q.summary.length===n*107,key+' distinct markers');ok(q.animalRows.length===n*107*20,key+' animal markers');
 for(const gene of D.genes.filter(g=>!g.mapped)){const values=q.summary.filter(r=>r.gene===gene.symbol);if(key.startsWith('1.0'))ok(values.every(r=>r.raw===null&&r.normalized===null&&r.detection===null),key+' explicit unmapped NA '+gene.symbol);}
 const z=C.zscores(q.summary,D.genes.map(g=>g.symbol));ok([...z.values()].every(Number.isFinite),key+' finite mapped z-scores');
 const label={dataset_id:D.dataset_id,resolution:D.resolution,partition_graph:D.partition_graph,labels:{'0':'Display only'}};ok(C.validateLabels(label,D.clusters,D.dataset_id)['0']==='Display only',key+' scoped labels');
 for(const other of Object.values(R).filter(x=>x.dataset_id!==D.dataset_id))assert.throws(()=>C.validateLabels(label,other.clusters,other.dataset_id));checks+=3;
}
for(const branch of ['corrected','uncorrected']){
 const D=R['1.0|'+branch],source=L.branches[branch],b=Buffer.from(source.base64,'base64'),counts={};ok(crypto.createHash('sha256').update(b).digest('hex')===source.derived_bytes_sha256,branch+' label bytes hash');ok(b.length===456472*2,branch+' label axis length');
 for(let i=0;i<456472;i++){const c=source.labels[b.readUInt16LE(i*2)];assert.ok(c!==undefined);counts[c]=(counts[c]||0)+1;}
 ok(D.clusters.every(c=>c.n===counts[c.id]),branch+' actual label counts');ok(D.clusters.every(c=>c.candidate==='Unreviewed resolution-1 cluster'),branch+' neutral candidates');
 ok(D.records.every(r=>r[3]>0&&(r[4]===null||Number.isInteger(r[4])&&r[4]>=0)),branch+' raw integers or NA');
}
ok(crypto.createHash('sha256').update(attrs).digest('hex')===context.window.ATLAS_RESOLUTION_REGISTRY_CONFIG.initial_point_attributes_sha256,'original attributes identity');
ok(/<option value="1\.0">1\.0 · verified results/.test(html),'actual resolution enabled');ok(/id="partitionGraph"/.test(html),'partition graph selector');ok(/Coordinate embedding<select id="embedding"/.test(html),'coordinate selector independent');ok(!/value="uncorrected">Uncorrected initial cluster/.test(html),'no ambiguous old color shortcut');ok(/D\.dataset_id\+'_'\+name/.test(app),'PDF filename scoped');ok(/datasetContext\(\)/.test(app)&&/D\.partition_graph/.test(app),'PDF context scoped');ok(/if\(!D\.activity_available\)/.test(app),'unavailable own marker gate');ok(/D\.microglia_candidate_cluster/.test(app),'microglia shortcut gated');
const result={tested_utc:new Date().toISOString(),all_passed:true,checks,actual_resolution1_enabled:true,clusters:expected,package_manifest_sha256:context.window.ATLAS_RESOLUTION_REGISTRY_CONFIG.manifest_sha256,all_nuclei:456472,graphs_and_coordinate_controls_separate:true,labels_scoped_by_dataset_resolution_graph:true,canonical_genotype_filter:true,initial_uncorrected_markers_explicitly_unavailable:true,raw_integer_NA_animal_coverage_and_label_axes:true,coordinate_or_raw_matrix_recomputed:false,browser_visual_check:false};fs.writeFileSync(path.join(base,'resolution_selector_tests.actual.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
