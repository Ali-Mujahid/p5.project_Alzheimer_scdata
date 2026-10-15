import datetime, hashlib, json, shutil
from pathlib import Path
ROOT=Path('/Users/mujahidali/Documents/Codex/2026-09-30/a')
W=ROOT/'work/TE_atlas_20261015'
A=ROOT/'outputs/p5_workflow/full_workflow_20261014/atlas_preview'
R=ROOT/'outputs/p5_workflow/ATAC_peak_TE_annotation_20261015/job-7471562'
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def ref(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def write(p,d):
 t=p.with_name(p.name+'.tmp'); t.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');t.replace(p)
m=json.loads((A/'te_data/manifest.json').read_text())
v=json.loads((W/'data_and_plot_validation.actual.json').read_text())
assert sha(A/'te_data/manifest.json')==v['adapter_manifest_sha256']
lazy=[]
for c in m['cell_types']:
 p=A/'te_data'/c['path'];r=ref(p)
 assert r['sha256']==c['sha256'] and r['bytes']==c['bytes']
 lazy.append({'cell_type':c['id'],**r})
assert len(lazy)==28
protected=json.loads((W/'protected_baseline_local_SHA.actual.json').read_text())
unchanged={name:sha(A/name)==digest for name,digest in protected['files'].items()}
assert all(unchanged.values())
bs=A/'export_validation/TE_overlap/browser_PDF_export_validation.actual.json'
b=json.loads(bs.read_text());assert b['all_passed'] and b['checks_passed']==36
assert sha(A/'te_overlap.js')==b['current_module_SHA256']
assert '"checks":35,"passed":35,"failed":0' in (W/'root_final_UI_tests.actual.log').read_text()
proof={
 'schema':'verified_TE_coordinate_overlap_atlas_import_v1','utc':now,
 'state':'verified_local_atlas_import_and_figures_ready',
 'producer_job_id':'7471562','producer_source_manifest_sha256':m['source_manifest_sha256'],
 'scope':m['scope'],'label_basis':m['label_basis'],
 'source_acceptance':{'download_manifest':ref(R/'download_manifest.actual.json'),'terminal_adoption':ref(R/'terminal_adoption.actual.json'),'remote_files_modified_this_turn':False,'new_remote_job_or_matrix_processing_this_turn':False,'hash_scope':'Local downloaded table/JSON/figure byte integrity. Download records preserve before/after remote byte/inode/mtime identity, not new allocated producer output-content SHA.'},
 'manifest':ref(A/'te_data/manifest.json'),'lazy_cell_type_files':lazy,'lazy_cell_type_bytes':sum(x['bytes'] for x in lazy),
 'data_validation':ref(W/'data_and_plot_validation.actual.json'),
 'independent_reviews':{n:ref(W/n) for n in ['independent_review.actual.json','independent_review.core.actual.json','independent_review.adapter.actual.json','independent_review.pdf.actual.json','independent_review.final.actual.json']},
 'final_UI_sources':{n:ref(A/n) for n in ['index.html','app.js','te_overlap.js','te_overlap_core.js','te_overlap.css','te_overlap_tests.cjs','README.md']},
 'current_source_revision_note':'Independent numerical/adapter/static-PDF reviews precede final PDF-unit placement change; root 35 UI checks and real-browser exports cover the final JS version, additionally read-only independently checked.',
 'UI_tests':{'new_TE_checks_passed':35,'log':ref(W/'root_final_UI_tests.actual.log'),'existing_atlas_state_tests':ref(A/'resolution_ui_state_tests.actual.json')},
 'real_browser':{'URL':'http://127.0.0.1:56404/full_workflow_20261014/atlas_preview/index.html#te-overlap','surface':'in-app browser via CUA','verified':['Microglia class absolute/default 3mo both sexes','all 28 types selectable','Pituitary 1/4 versus 0/4 NA; all 5 ages 1/20 total available','female n2 per condition, family, zscore, 36 categories','actual heatmap/boxplot PDF button downloads','2-page family heatmap PDF and TSV data export','restored default Microglia state'],'PDF_checks':ref(bs),'screenshot':ref(A/'export_validation/TE_overlap/atlas_microglia_TE_view.jpg'),'local_server_record':ref(W/'atlas_local_server.actual.json')},
 'protected_initial_adapters_unchanged':unchanged,'baseline_hash_proof':ref(W/'protected_baseline_local_SHA.actual.json'),
 'figures':{p.name:ref(p) for p in sorted((R/'genotype_visualizations').glob('*.pdf'))},
 'controls':{'all_initial_calibration_types':28,'extra_microglia':True,'genotype_3mo_comparison':True,'aging_separate':True,'sex_filter':True,'class_family_subfamily':True,'equal_animal_mean':True,'all_animals_visible_in_boxplots':True,'missing_empty_as_NA':True,'valid_zero_preserved':True,'metric_specific_denominators':True,'PDF_only_plot_buttons':True,'native_vector_TE_PDF':True,'TSV_data_exports':True,'TE_controls_independent_of_UMAP_Leiden_and_display_labels':True},
 'scientific_limits':m['limitations'],
 'final_QC_or_normalization_accepted':False,'TE_expression_or_fragment_accessibility_measured':False,'genotype_differential_test_performed':False,'new_final_cell_type_labels_assigned':False,
 'final_independent_readonly_check':{'current_source_hashes_match':True,'UI_checks':35,'real_browser_PDF_checks':36,'all_five_static_PDF_hashes_match':True,'screenshot_exists':True,'actionable_inconsistency':False}
}
write(A/'te_overlap_import_provenance.actual.json',proof)
backup=W/'before_final_durable_metadata';backup.mkdir(exist_ok=True)
p=ROOT/'outputs/p5_workflow/latest_execution.json'
shutil.copy2(p,backup/p.name)
d=json.loads(p.read_text());f=d['full_workflow_request_20261014'];at=f['atlas_preview']
at.update({'state':'functional provisional ATAC atlas; verified Leiden0.6/1.0 plus TE peak coordinate-overlap heatmaps and animal boxplots; final filtered RNA/ATAC and TE count analyses pending','Leiden_resolutions':{'0.6':'available','1.0':'available with verified fresh resolution-specific markers'},'TE_overlap':{'producer_job_id':'7471562','state':'verified_and_browser_tested','URL':proof['real_browser']['URL'],'provenance':str(A/'te_overlap_import_provenance.actual.json'),'all_initial_calibration_cell_types':28,'default_view':'Microglia','static_figures':str(R/'genotype_visualizations'),'new_TE_UI_checks':35,'actual_browser_PDF_checks':36,'normalization_ready':False,'statistical_genotype_effect_test':False},'local_HTTP_required_for_TE_lazy_JSON':True})
f['updated_utc']=now
f['next_stage_candidates']['atlas_preview']='functional provisional initial ATAC atlas with verified Leiden0.6/1.0 and TE coordinate overlap; final filtered RNA/ATAC, unbiased markers and TE count analyses remain pending'
f['atlas_export_preference']['implementation_state']='PDF-only plot buttons; prior UMAP/activity/composition checks retained; TE native-vector PDF and pagination verified by actual browser downloads'
f['atlas_export_preference']['TE_browser_PDF_proof']=str(bs)
d['updated_utc']=now
d['overnight_LiSC_20261015']['TE_peak_overlap_visualizations']={'updated_utc':now,'provenance':str(A/'te_overlap_import_provenance.actual.json'),'plots':str(R/'genotype_visualizations'),'atlas_URL':proof['real_browser']['URL'],'no_new_remote_observation_this_turn':True,'label_basis':'initial_calibration','descriptive_only':True}
write(p,d)
section=f'''## Verified TE overlap figures and atlas view — 15 October 2026

TE coordinate-overlap visualization from accepted job **7471562** is ready: all 28 initial calibration cell-type groups, class/family/subfamily heatmaps and animal-level genotype boxplots, with additional Microglia reports. The atlas opens at <{proof['real_browser']['URL']}>. All plot save buttons export PDF; data exports remain TSV/JSON. Three-month WT, 5xFAD and APOE4/TREM2 are compared at the same age; older WT remain separate. Every animal receives equal weight, and missing/empty groups remain NA.

Microglia have four callable animals (two female, two male) in each of five conditions. Mean primary-TE peak-base overlap at three months is WT **5.74%**, 5xFAD **6.46%**, APOE4/TREM2 **6.63%**. LTR contributes the largest class-level fraction. These are descriptive coordinate-overlap results from initial calibration peak sets, not TE expression, fragment-level accessibility, final annotations or a genotype significance test. Peak discovery depth, widths and genomic context remain limitations.

The seven downloaded source-table checks, 32,116 equal-animal summary matches, all 28 local JSON adapters, 35 UI checks and 36 actual-browser PDF checks are bound in `full_workflow_20261014/atlas_preview/te_overlap_import_provenance.actual.json`. Five prepared PDF reports and PNG previews are in `ATAC_peak_TE_annotation_20261015/job-7471562/genotype_visualizations/`. Original UMAP/activity/partition adapter bytes are unchanged. This local figure/atlas update made no new remote observation or job submission; the preceding QC/SCT observations retain their own measurement times. Full QC, normalization, independent final labels and TE count-based inference remain pending their recorded scientific gates.

'''
for rel in ['analysis_status.md','compute_acceleration.md','full_study_analysis_plan.md','full_workflow_20261014/analysis_plan.md']:
 p=ROOT/'outputs/p5_workflow'/rel
 shutil.copy2(p,backup/rel.replace('/','__'))
 text=p.read_text()
 marker='## Verified TE overlap figures and atlas view — 15 October 2026'
 assert marker not in text
 # Keep the main document title first, add one bounded current visualization note.
 if text.startswith('# '):
  i=text.index('\n');text=text[:i+1]+'\n'+section+text[i+1:].lstrip('\n')
 else:text=section+text
 p.write_text(text)
write(W/'durable_import_update.actual.json',{'utc':now,'atlas_provenance':ref(A/'te_overlap_import_provenance.actual.json'),'README':ref(A/'README.md'),'latest_execution':ref(ROOT/'outputs/p5_workflow/latest_execution.json'),'backups':str(backup),'remote_states_refreshed':False})
print(json.dumps({'status':'metadata_saved','UTC':now,'lazy_files':len(lazy),'bytes':sum(x['bytes'] for x in lazy),'PDF_reports':len(proof['figures']),'protected_unchanged':all(unchanged.values()),'provenance':str(A/'te_overlap_import_provenance.actual.json')},indent=2))
