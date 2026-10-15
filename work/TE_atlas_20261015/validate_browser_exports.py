"""Verify files received from actual CUA clicks; no synthetic PDF/download substitute."""
from pathlib import Path
import json,shutil,hashlib,datetime,re
from pypdf import PdfReader
R=Path(__file__).resolve().parents[2];D=R/'outputs/p5_workflow/full_workflow_20261014/atlas_preview/export_validation/TE_overlap';D.mkdir(parents=True,exist_ok=True)
files={'microglia_class_heatmap_browser_final.pdf':Path('/Users/mujahidali/Downloads/job7471562_TE_overlap_Microglia_heatmap (2).pdf'),'microglia_primaryTE_boxplot_browser_final.pdf':Path('/Users/mujahidali/Downloads/job7471562_TE_overlap_Microglia_boxplot (1).pdf'),'microglia_female_family_zscore_browser.pdf':Path('/Users/mujahidali/Downloads/job7471562_TE_overlap_Microglia_heatmap (1).pdf'),'microglia_female_family_means_browser.tsv':Path('/Users/mujahidali/Downloads/job7471562_Microglia_TE_overlap_means.tsv')}
proof={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'actual CUA UI click/download events','producer_job_id':'7471562','checks':{},'files':{},'current_module_SHA256':hashlib.sha256((D.parents[1]/'te_overlap.js').read_bytes()).hexdigest(),'family_PDF_test_scope':'pagination/filter/taxonomy from preceding module before PDF-only rotated-unit fix; final default boxplot/heatmap tested again after fix'}
for name,p in files.items():
 assert p.is_file();target=D/name
 if target.exists():assert target.read_bytes()==p.read_bytes()
 else:shutil.copy2(p,target)
 b=target.read_bytes();row={'path':str(target),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 if name.endswith('.pdf'):
  assert b.startswith(b'%PDF');r=PdfReader(target);text='\n'.join(page.extract_text() or '' for page in r.pages);target.with_suffix('.txt').write_text(text);row.update(pages=len(r.pages),native_text_extracted=True,embedded_images=sum(len(page.images) for page in r.pages));flat=re.sub(r'\s+',' ',text.lower())
  checks={'producer_job':'7471562' in text,'Microglia':'Microglia' in text,'scope_overlap':'overlap' in flat,'no_expression_claim':any(x in flat for x in ['no te expression','not te expression','not expression']),'no_inferential_claim':'inferential enrichment' in flat,'genotype_WT':'WT' in text,'genotype_FAD':'5xFAD' in text,'genotype_APOE':'APOE4' in text,'native_vectors':row['embedded_images']==0}
  if 'female_family' in name:checks.update(two_pages=len(r.pages)==2,zscore='z-score' in flat,female_filter='female' in flat,family_disambiguation='[LTR]' in text)
  if 'boxplot' in name:checks.update(median_boxlegend='median' in flat,animals_available='4/4' in text,sex_shapes='Female' in text and 'Male' in text,plot_units='Callable peak overlap (%)' in text)
  if 'class_heatmap' in name:checks.update(tiny_positive_RC_not_rounded_zero='0.0016%' in text and '0.0022%' in text)
  proof['checks'][name]=checks;assert all(checks.values()),(name,checks)
 else:
  lines=b.decode().splitlines();fields=lines[0].split('\t');assert all(x in fields for x in ['repClass','repFamily','repName','metric','condition','value','n_available','n_expected']);row['rows']=len(lines)-1
 proof['files'][name]=row
proof['all_passed']=True;proof['checks_passed']=sum(len(v) for v in proof['checks'].values());dest=D/'browser_PDF_export_validation.actual.json';old=D/'initial_literal_scope_parser_check.actual.json'
if dest.exists() and not old.exists():shutil.copy2(dest,old)
dest.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'all_passed':True,'checks_passed':proof['checks_passed'],'files':{k:{'pages':v.get('pages'),'bytes':v['bytes']} for k,v in proof['files'].items()}}))
