from pathlib import Path
from pypdf import PdfReader
import json,hashlib,datetime
r=Path('/Users/mujahidali/Documents/Codex/2026-09-30/a')
p=r/'outputs/p5_workflow/ATAC_peak_TE_annotation_20261015/job-7471562/genotype_visualizations'
checks=[];files={}
for f in sorted(p.glob('*.pdf')):
 d=PdfReader(f);texts=[page.extract_text() or '' for page in d.pages];text='\n'.join(texts)
 q={'pages':len(d.pages),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'all_pages_producer_scope':all('7471562' in t and 'coordinate overlap' in t and 'No TE expression' in t for t in texts),'all_pages_descriptive_no_inference_limit':all('Descriptive only' in t and 'differential test' in t and 'final cell-type claim' in t for t in texts),'extractable_native_text':len(text)>500}
 if 'boxplots' in f.name:q['age_matched_only']='21 mo' not in text and '6 mo' not in text and '3 mo' in text and 'n=4' in text
 if 'all_cell_types' in f.name:q['six_pages_all28_types']=len(d.pages)==6 and all('Pituitary cells' in t and 'Microglia' in t and 'Choroid plexus epithelial cells' in t for t in texts)
 if 'microglia_TE_class' in f.name:q['tiny_RC_values_not_fabricated_zero']='<0.01 0 <0.01 0 <0.01' in text
 checks.extend({'name':f.name+' '+k,'passed':v} for k,v in q.items() if isinstance(v,bool));files[f.name]=q
 for k,v in q.items():
  if isinstance(v,bool) and not v:raise AssertionError(f.name+' '+k)
 (r/'work/TE_atlas_20261015'/('independent_review.'+f.stem+'.txt')).write_text(text)
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Independent static PDF native text, producer/limits and category/condition scope review','checks':checks,'passed':all(c['passed'] for c in checks),'files':files,'detailed_peak_depth_GC_TSS_mappability_limit_location':'HTML method note and adapter manifest; not part of static plot footer'}
(r/'work/TE_atlas_20261015/independent_review.pdf.actual.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
