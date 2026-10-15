/* Four actual partitions. Coordinates are a separate, unchanged display layer. */
(function(root){
'use strict';
const old=root.ATLAS_DATA,cfg=root.ATLAS_RESOLUTION_REGISTRY_CONFIG;
const canonicalAnimals=animals=>animals.map(a=>({...a,genotype:a.genotype==='APOE4_TREM2'?'APOE4/TREM2':a.genotype}));
const first=old.genes[0].symbol,oldCoverage=old.records.filter(r=>r[2]===first).map(r=>[String(r[0]),r[1],r[3]]);
const original={...old,resolution:0.6,partition_graph:'corrected',activity_available:true,coverage_records:oldCoverage,animals:canonicalAnimals(old.animals),microglia_candidate_cluster:'6'};
const counts=new Map();for(const [c,,n]of cfg.initial_uncorrected_coverage)counts.set(c,(counts.get(c)||0)+n);
const uncorrected={...original,dataset_id:'ATAC_initial_7466270_uncorrected',partition_graph:'uncorrected',activity_available:false,records:[],coverage_records:cfg.initial_uncorrected_coverage,microglia_candidate_cluster:null,clusters:[...counts].sort((a,b)=>+a[0]-b[0]).map(([id,n])=>({id,n,candidate:'Unreviewed uncorrected cluster',status:'provisional; independent annotation pending'}))};
const registry={'0.6|corrected':original,'0.6|uncorrected':uncorrected};
for(const branch of ['corrected','uncorrected']){
 const actual=root.ATLAS_RESOLUTION_DATASETS['ATAC_resolution1_7470007_'+branch];
 if(!actual||actual.ordered_cell_ids_sha256!==cfg.ordered_cell_ids_sha256||actual.initial_point_attributes_sha256!==cfg.initial_point_attributes_sha256)throw Error('Resolution-1 adapter identity mismatch.');
 registry['1.0|'+branch]={...actual,activity_available:true,coverage_records:cfg.resolution1[branch].coverage_records,label_dictionary:cfg.resolution1[branch].label_dictionary,microglia_candidate_cluster:null,animals:canonicalAnimals(actual.animals),producer_completed_utc:'2026-10-14T23:21:47Z',pdfs:old.pdfs,status:{...old.status,'ATAC gene-body activity':'Actual resolution-1 '+branch+' partition and fresh 107-gene activity summaries available; final QC and independent annotation pending'},source_records:cfg.source_records,package_job_id:'7470531',package_manifest_sha256:cfg.manifest_sha256};
}
root.ATLAS_DATASET_REGISTRY=registry;
root.ATLAS_ACTIVE_DATASET_KEY=(resolution,graph)=>Number(resolution).toFixed(1)+'|'+graph;
})(window);
