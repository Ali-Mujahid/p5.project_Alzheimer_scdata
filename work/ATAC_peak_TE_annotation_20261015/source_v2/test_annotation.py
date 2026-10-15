"""Generated coordinate fixtures: no study inputs or matrices are read."""
import sys
sys.dont_write_bytecode=True
import copy,csv,gzip,json,random,tempfile,unittest
from pathlib import Path
from annotate import (IntervalIndex,Masks,categories,kind,length,load_reference,merge,read_peaks,summarize_group,validate_catalog)

class Tests(unittest.TestCase):
    def test_half_open_nested_all_hits(self):
        x=IntervalIndex([('chr1',0,100,'outer'),('chr1',20,30,'inner'),('chr1',30,40,'touch')])
        self.assertEqual({v[2] for v in x.overlap('chr1',29,30)},{'outer','inner'})
        self.assertEqual({v[2] for v in x.overlap('chr1',30,31)},{'outer','touch'})
    def test_blacklist_nested_and_touching(self):
        self.assertEqual(Masks({'chr1':[(3,6),(4,5),(6,7)]}).callable('chr1',1,9),[(1,3),(7,9)])
        self.assertEqual(length([(0,4),(2,8),(8,10)]),10)
    def test_random_independent_base_oracle(self):
        rng=random.Random(59)
        for trial in range(250):
            black=[tuple(sorted(rng.sample(range(31),2))) for _ in range(5)]
            peaks=[tuple(sorted(rng.sample(range(31),2))) for _ in range(4)]
            masks=Masks({'chr1':black})
            expected={i for a,b in peaks for i in range(a,b)}-{i for a,b in black for i in range(a,b)}
            actual={i for a,b in merge(peaks) for x,y in masks.callable('chr1',a,b) for i in range(x,y)}
            self.assertEqual(actual,expected)
    def test_native_taxonomy_context_and_uncertainty(self):
        self.assertEqual(kind('LINE?'),'uncertain_TE_class')
        self.assertEqual(kind('Simple_repeat'),'non_TE_repeat')
        self.assertNotIn(('family','Simple_repeat','x',''),categories('Simple_repeat','x','y'))
        self.assertNotEqual(categories('LINE','A','X'),categories('SINE','A','X'))
    def fixture_summary(self,peaks):
        t=tempfile.TemporaryDirectory();d=Path(t.name)
        # Duplicate repeat records are retained as hits; union endpoint counts bases once.
        payloads=[('chr1',0,8,(1,'1','+','LINE','L1','X')),('chr1',4,10,(2,'2','-','LINE','L1','X')),('chr1',0,8,(3,'3','+','LINE','L1','X')),('chr1',6,9,(4,'4','+','Simple_repeat','Simple','R'))]
        index=IntervalIndex(payloads);m=Masks({'chr1':[(2,4)]})
        bg={('any_repeat','ALL','ALL','ALL'):{'chr1':8},('class','LINE','',''):{'chr1':8},('class','Simple_repeat','',''):{'chr1':3},('family','LINE','L1',''):{'chr1':8}}
        rows,s=summarize_group(peaks,index,m,{'chr1':18},bg,d/'wide.gz',d/'long.gz',['original'])
        return t,d,rows,s
    def test_multihits_union_and_chromosome_weighted_fold(self):
        t,d,rows,s=self.fixture_summary([({'original':'keep'},'p1','chr1',0,7),({'original':'also'},'p2','chr1',5,12)])
        try:
            by={r['level']+r['repClass']:r for r in rows}
            self.assertEqual(s['callable_peak_union_bp'],10)
            self.assertEqual(by['classLINE']['overlap_union_bp'],8)
            self.assertAlmostEqual(by['classLINE']['chromosome_weighted_expected_bp'],10*8/18)
            self.assertAlmostEqual(by['classLINE']['chromosome_coverage_fold_descriptive'],1.8)
            with gzip.open(d/'long.gz','rt') as f: hits=list(csv.DictReader(f,delimiter='\t'))
            self.assertEqual(len(hits),8)
            with gzip.open(d/'wide.gz','rt') as f: wide=list(csv.DictReader(f,delimiter='\t'))
            self.assertEqual([r['original'] for r in wide],['keep','also'])
            self.assertEqual(json.loads(wide[0]['native_repClass_json']),['LINE','Simple_repeat'])
        finally:t.cleanup()
    def test_empty_group_NA(self):
        t,d,rows,s=self.fixture_summary([])
        try:
            self.assertTrue(s['empty_or_noncallable']);self.assertTrue(all(r['overlap_fraction_descriptive'] is None and r['chromosome_coverage_fold_descriptive'] is None for r in rows))
        finally:t.cleanup()
    def test_17column_RMSK_and_nuclear_exclusion(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t);(d/'sizes').write_text(''.join(f'chr{i}\t100\n' for i in range(1,20))+'chrX\t100\nchrY\t100\nchrM\t100\n')
            (d/'black').write_text('chr1\t2\t4\n')
            def row(c,a,b,cl='LINE',fam='L1',name='X'):return '\t'.join(map(str,[0,1,0,0,0,c,a,b,-1,'+',name,cl,fam,0,1,0,1]))+'\n'
            (d/'rm').write_text(row('chr1',0,10)+row('chrM',0,10))
            ix,m,sz,cs,bg,tax,excluded=load_reference(d/'rm',d/'sizes',d/'black')
            self.assertEqual(bg[('class','LINE','','')]['chr1'],8);self.assertNotIn('chrM',sz);self.assertEqual(excluded['rmsk_non_nuclear_rows'],1)
            (d/'rm').write_text(row('chr1',0,10).split('\t',1)[1])
            with self.assertRaises(RuntimeError):load_reference(d/'rm',d/'sizes',d/'black')
    def test_input_schema_bounds_and_group_association(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'peaks';p.write_text('chr1\t0\t10\tPB00001_peak_1\t1\t.\t1\t1\t1\t4\n')
            self.assertEqual(len(read_peaks(p,'narrowPeak',{'chr1':10},'PB00001')[1]),1)
            with self.assertRaises(RuntimeError):read_peaks(p,'narrowPeak',{'chr1':10},'PB00002')
            with self.assertRaises(RuntimeError):read_peaks(p,'narrowPeak',{'chr1':9},'PB00001')
    def test_actual_MACS_call_summits_names_and_wrong_prefix(self):
        evidence=json.loads((Path(__file__).parent/'actual_first_rejected_peak_name.recorded.json').read_text())
        actual=evidence['first_rejected']['columns']
        self.assertEqual(actual[3],'PB00000_peak_102a')
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'peaks'
            # Actual observed102a;102b and multi-letter suffix are generated grammar fixtures.
            for name in [actual[3],'PB00000_peak_102b','PB00000_peak_102aa','PB00000_peak_103']:
                row=list(actual);row[3]=name;p.write_text('\t'.join(row)+'\n')
                self.assertEqual(read_peaks(p,'narrowPeak',{'chr1':200000000},'PB00000')[1][0][1],name)
            for name in ['PB00001_peak_102a','PB00000_peak_102A','PB00000_peak_102a_extra','PB00000_peak_a102']:
                row=list(actual);row[3]=name;p.write_text('\t'.join(row)+'\n')
                with self.assertRaises(RuntimeError):read_peaks(p,'narrowPeak',{'chr1':200000000},'PB00000')
    def generated_catalog(self,d):
        animals=[f'{g}_3mo_{sex}_{rep}' for g in ['WT','FAD','APOE4_TREM2','Other','Fifth'] for sex in ['male','female'] for rep in [1,2]]
        groups=[]
        for i in range(467):
            animal=animals[i%20];g,age,sex,rep=animal.rsplit('_',3);gid=f'PB{i:05}'
            groups.append(dict(group_id=gid,animal_id=animal,cell_type='type'+str(i//20),descriptive_name=f'type{i}',genotype=g,age=age,sex=sex,replicate='R'+rep,input={'path':str(d/'peak_calls'/gid/(gid+'_peaks.narrowPeak')),'allowed_resolved_root':str(d/'peak_calls')}))
        tab=d/'groups.tsv'
        with tab.open('w') as f:
            w=csv.DictWriter(f,fieldnames=['group_id','animal_id','cell_type'],delimiter='\t');w.writeheader();w.writerows({k:r[k] for k in w.fieldnames} for r in groups)
        return dict(assembly='mm10',groups=groups,groups_table={'path':str(tab)})
    def test_exact467_catalog_routes(self):
        with tempfile.TemporaryDirectory() as t:validate_catalog(self.generated_catalog(Path(t)))
    def test_catalog_colliding_slug_and_wrong_biology_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.generated_catalog(Path(t));c['groups'][1]['descriptive_name']=c['groups'][0]['descriptive_name'].upper()
            with self.assertRaises(RuntimeError):validate_catalog(c)
            c=self.generated_catalog(Path(t));c['groups'][0]['sex']='female'
            with self.assertRaises(RuntimeError):validate_catalog(c)
    def test_catalog_group_swap_and_path_swap_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.generated_catalog(Path(t));c['groups'][0]['animal_id']=c['groups'][1]['animal_id']
            with self.assertRaises(RuntimeError):validate_catalog(c)
            c=self.generated_catalog(Path(t));c['groups'][0]['input'],c['groups'][1]['input']=c['groups'][1]['input'],c['groups'][0]['input']
            with self.assertRaises(RuntimeError):validate_catalog(c)

if __name__=='__main__':unittest.main(verbosity=2)
