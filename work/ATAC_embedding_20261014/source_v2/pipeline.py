import sys;sys.dont_write_bytecode=True
import pathlib,json,gc,runpy,unittest
out=pathlib.Path(sys.argv[1]);src=pathlib.Path(__file__).parent
suite=unittest.defaultTestLoader.discover(str(src),pattern='test_*.py');result=unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful() or result.skipped:raise RuntimeError('Required runtime fixture QA failed or skipped')
inputs={pathlib.Path(x['path']).name:x['path'] for x in json.loads((src/'input_identity_manifest.json').read_text())}
sys.argv=['initial_atac.py','--input',inputs['atac_peaks_mm10.h5ad'],'--output',str(out/'embedding'),'--initial-atlas','--memory-gb','128','--threads','32','--n-components','50','--min-feature-cells','10','--n-neighbors','30','--resolution','0.6','--seed','1729','--batch-key','library_id','--batch-provenance','Verified PCR technical libraries; every library crosses all20 animals and five biological conditions; raw counts preserved']
runpy.run_path(str(src/'initial_atac.py'),run_name='__main__');gc.collect()
sys.argv=['marker_review.py',str(out/'embedding/atac_initial_atlas.h5ad'),inputs['atac_activity_mm10.h5ad'],str(out/'marker_review')]
runpy.run_path(str(src/'marker_review.py'),run_name='__main__')
