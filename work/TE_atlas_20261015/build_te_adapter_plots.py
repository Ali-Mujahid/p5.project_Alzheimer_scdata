#!/usr/bin/env python3
"""Verified coordinate-overlap adapter and descriptive animal-level PDF figures.
No matrix reads, biological filtering, TE expression or differential analysis.
"""
import sys
sys.dont_write_bytecode = True
import csv, gzip, hashlib, json, math, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/p5_workflow/ATAC_peak_TE_annotation_20261015/job-7471562'
ANNOT=BASE/'annotation'
DATA=ROOT/'outputs/p5_workflow/full_workflow_20261014/atlas_preview/te_data'
PLOTS=BASE/'genotype_visualizations'
WORK=ROOT/'work/TE_atlas_20261015'
PRIMARY=['DNA','LINE','LTR','RC','Retroposon','SINE']
CONDS=['WT_3mo','5xFAD_3mo','APOE4_TREM2_3mo','WT_6mo','WT_21mo']
CLABEL={'WT_3mo':'WT · 3 mo','5xFAD_3mo':'5xFAD · 3 mo','APOE4_TREM2_3mo':'APOE4/TREM2 · 3 mo','WT_6mo':'WT · 6 mo','WT_21mo':'WT · 21 mo'}
PALETTE={'WT_3mo':'#3b6f8b','5xFAD_3mo':'#c95d47','APOE4_TREM2_3mo':'#9472a8','WT_6mo':'#5d8d73','WT_21mo':'#b18b42'}
SOURCE_TEXT='Job 7471562 · mm10 RepeatMasker coordinate overlap · initial calibration cell types'
LIMIT_TEXT='Descriptive only; equal animal weight. No TE expression, differential test or final cell-type claim.'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,'axes.labelsize':10,'pdf.fonttype':42,'ps.fonttype':42,'figure.facecolor':'white','axes.spines.top':False,'axes.spines.right':False})


def need(test, msg):
    if not test: raise AssertionError(msg)

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n')

def opt(value):
    return None if pd.isna(value) or value=='' else float(value)

def mean_available(values):
    valid=[float(x) for x in values if x is not None and math.isfinite(float(x))]
    return sum(valid)/len(valid) if valid else None

def fixture_checks():
    checks={}
    checks['missing_is_not_zero']=mean_available([None,None]) is None
    checks['valid_zero_is_retained']=mean_available([0.,.1,None])==.05
    checks['equal_animals_not_peak_weighted']=mean_available([.1,.9])==.5
    checks['aging_not_disease_control']=set(CONDS[:3])=={'WT_3mo','5xFAD_3mo','APOE4_TREM2_3mo'} and not any('21mo' in c or '6mo' in c for c in CONDS[:3])
    checks['different_levels_have_distinct_ids']=catid('class','SINE','','')!=catid('family','SINE','','')
    for name,ok in checks.items():need(ok,name)
    return checks

def catid(level,cl,fam,name):
    return level+'_'+hashlib.sha256(json.dumps([level,cl,fam,name],separators=(',',':')).encode()).hexdigest()[:14]

def slug(x):return re.sub(r'[^A-Za-z0-9]+','_',x).strip('_')

def footer(fig,extra=''):
    fig.text(.01,.060,SOURCE_TEXT,fontsize=8,color='#465266')
    fig.text(.01,.036,LIMIT_TEXT,fontsize=8,color='#465266')
    if extra:fig.text(.01,.012,extra,fontsize=8,color='#465266')

def save(fig,name):
    fig.savefig(PLOTS/(name+'.pdf'),bbox_inches='tight',facecolor='white')
    fig.savefig(PLOTS/(name+'.png'),dpi=180,bbox_inches='tight',facecolor='white')
    plt.close(fig)


def heatmap_micro(frame,level,name,title,top=None,fold=False):
    f=frame[(frame.cell_type=='Microglia')&(frame.level==level)&frame.repClass.isin(PRIMARY)].copy()
    rank=f.groupby('category_id',observed=True).overlap_fraction_descriptive.mean().sort_values(ascending=False)
    ids=list(rank.index[:top] if top else sorted(rank.index,key=lambda k: (PRIMARY.index(CAT[k]['class']),CAT[k]['label'])))
    if level=='class':ids=[c for cl in PRIMARY for c in ids if CAT[c]['class']==cl]
    mat=np.array([[mean_available(f.loc[(f.category_id==cid)&(f.condition==c),'overlap_fraction_descriptive']) for c in CONDS] for cid in ids],float)*100
    fig,ax=plt.subplots(figsize=(9.7,max(5,0.32*len(ids)+2.5)))
    cmap=plt.get_cmap('viridis').copy();cmap.set_bad('#e5e7eb')
    im=ax.imshow(np.ma.masked_invalid(mat),cmap=cmap,aspect='auto',vmin=0)
    labels=[CAT[c]['label'] if level=='class' else CAT[c]['label']+' ['+CAT[c]['class']+']' for c in ids]
    ax.set_yticks(range(len(ids)),labels)
    ax.set_xticks(range(5),[CLABEL[c]+'\nn=4' for c in CONDS],rotation=25,ha='right')
    ax.set_title(title+'\nEqual-animal mean % of callable peak-union bp',loc='left',pad=14,fontweight='bold')
    if len(ids)<=6:
        for i in range(len(ids)):
            for j in range(5):
                v=mat[i,j];ax.text(j,i,'NA' if not math.isfinite(v) else ('0' if v==0 else '<0.01' if v<.01 else f'{v:.2f}'),ha='center',va='center',fontsize=11,color='white' if math.isfinite(v) and v<mat.max()*.55 else '#172433')
    fig.colorbar(im,ax=ax,label='% callable peak-union bp',shrink=.8)
    footer(fig,'Taxonomy categories can overlap; percentages need not sum to 100%.')
    fig.subplots_adjust(left=.27 if top else .12,right=.9,bottom=.24,top=.86)
    save(fig,name)
    return ids,mat


def micro_boxplots(frame):
    wanted=[c for c in CAT.values() if c['level']=='any_primary_TE']+[c for c in CAT.values() if c['level']=='class' and c['class'] in PRIMARY]
    wanted=sorted(wanted,key=lambda c: -1 if c['level']=='any_primary_TE' else PRIMARY.index(c['class']))
    fig,axes=plt.subplots(2,3,figsize=(14,8.7))
    points=[]
    for ax,cat in zip(axes.flat,wanted):
        f=frame[(frame.cell_type=='Microglia')&(frame.category_id==cat['id'])]
        for j,condition in enumerate(CONDS[:3]):
            q=f[f.condition==condition].sort_values(['sex','animal_id'])
            y=100*q.overlap_fraction_descriptive.to_numpy()
            valid=y[np.isfinite(y)]
            if len(valid):
                bp=ax.boxplot([valid],positions=[j],widths=.46,showfliers=False,patch_artist=True,manage_ticks=False)
                bp['boxes'][0].set(facecolor=PALETTE[condition],alpha=.22,edgecolor=PALETTE[condition])
                for l in bp['medians']:l.set(color='#172433',linewidth=1.8)
            for k,row in enumerate(q.itertuples()):
                if pd.notna(row.overlap_fraction_descriptive):
                    x=j+(-.12+.08*k)
                    ax.scatter(x,100*row.overlap_fraction_descriptive,s=43,marker='o' if row.sex=='female' else '^',facecolor=PALETTE[condition],edgecolor='white',linewidth=.6,zorder=4)
                    points.append({'cell_type':'Microglia','level':cat['level'],'category':cat['label'],'animal_id':row.animal_id,'condition':condition,'sex':row.sex,'n_peaks':int(row.n_peaks),'callable_peak_union_bp':int(row.callable_peak_union_bp),'overlap_fraction_descriptive':row.overlap_fraction_descriptive,'fold_descriptive':opt(row.chromosome_coverage_fold_descriptive)})
            if len(valid):ax.plot([j-.18,j+.18],[valid.mean()]*2,color='#192c3d',linewidth=1,zorder=5)
        ax.set_xticks(range(3),[CLABEL[c].replace(' · ','\n')+'\nn=4' for c in CONDS[:3]],fontsize=9)
        ax.set_title('All primary TEs' if cat['level']=='any_primary_TE' else cat['label'],loc='left',fontweight='bold')
        ax.set_ylabel('% callable peak-union bp');ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True);ax.set_ylim(bottom=0)
    fig.suptitle('Microglia · TE overlap across the three 3-month genotype cohorts',x=.06,ha='left',fontsize=16,fontweight='bold',y=.98)
    fig.legend(handles=[Line2D([],[],marker='o',linestyle='',color='#52657a',label='Female'),Line2D([],[],marker='^',linestyle='',color='#52657a',label='Male'),Line2D([],[],color='#192c3d',label='Mean (short line)')],loc='upper right',bbox_to_anchor=(.97,.97),ncol=3,frameon=False,fontsize=9)
    footer(fig,'Boxes: median/IQR, whiskers 1.5×IQR; dots are individual animals. Older WT cohorts excluded here.')
    fig.subplots_adjust(left=.07,right=.98,bottom=.13,top=.86,hspace=.55,wspace=.3)
    save(fig,'microglia_TE_genotype_animal_boxplots_3mo')
    pd.DataFrame(points).to_csv(PLOTS/'microglia_TE_genotype_animal_points_3mo.tsv',sep='\t',index=False)


def all_types_heatmaps(frame,types):
    ids=[c['id'] for c in CAT.values() if c['level']=='class' and c['class'] in PRIMARY]
    ids.sort(key=lambda x:PRIMARY.index(CAT[x]['class']))
    ids=[next(c['id'] for c in CAT.values() if c['level']=='any_primary_TE')]+ids
    pages=[]
    with PdfPages(PLOTS/'all_cell_types_TE_class_by_condition_heatmaps.pdf') as pdf:
        for cid in ids:
            f=frame[frame.category_id==cid]
            mat=np.array([[mean_available(f.loc[(f.cell_type==t)&(f.condition==c),'overlap_fraction_descriptive']) for c in CONDS] for t in types],float)*100
            ns=np.array([[int(f.loc[(f.cell_type==t)&(f.condition==c),'overlap_fraction_descriptive'].notna().sum()) for c in CONDS] for t in types])
            fig,ax=plt.subplots(figsize=(10.5,12))
            cmap=plt.get_cmap('viridis').copy();cmap.set_bad('#e5e7eb')
            im=ax.imshow(np.ma.masked_invalid(mat),aspect='auto',cmap=cmap,vmin=0)
            ax.set_yticks(range(len(types)),types,fontsize=8.5)
            ax.set_xticks(range(5),[CLABEL[c] for c in CONDS],rotation=25,ha='right',fontsize=10)
            for i in range(len(types)):
                for j in range(5):
                    if ns[i,j]<4:ax.text(j,i,'NA' if ns[i,j]==0 else 'n='+str(ns[i,j]),ha='center',va='center',fontsize=7,color='white' if math.isfinite(mat[i,j]) and mat[i,j]<np.nanmax(mat)*.6 else '#182838')
            label='All primary TEs' if CAT[cid]['level']=='any_primary_TE' else CAT[cid]['label']
            ax.set_title(label+' · peak overlap by initial calibration type and cohort\nEqual-animal mean; each cohort has 4 animals; labels show support where n<4',loc='left',fontsize=12,pad=14,fontweight='bold')
            fig.colorbar(im,ax=ax,label='% callable peak-union bp',shrink=.7)
            footer(fig,'Absent/empty peak groups are NA; color scales are separate on each page.')
            fig.subplots_adjust(left=.36,right=.91,bottom=.14,top=.92)
            pdf.savefig(fig,bbox_inches='tight')
            if len(pages)==0:fig.savefig(PLOTS/'all_cell_types_any_primary_TE_by_condition.png',dpi=180,bbox_inches='tight')
            pages.append(label);plt.close(fig)
    return pages


def main():
    for path in [DATA,PLOTS,WORK]:path.mkdir(parents=True,exist_ok=True)
    fixes=fixture_checks()
    manifest=json.loads((BASE/'download_manifest.actual.json').read_text())
    adoption=json.loads((BASE/'terminal_adoption.actual.json').read_text())
    need(manifest['job_id']=='7471562' and adoption['scope']=='TE_peak_coordinate_overlap_only','Accepted producer scope')
    needed=['annotation/peak_repeat_genomic_coverage_by_group.tsv.gz','annotation/group_coverage_summary.tsv','annotation/available_animal_type_groups.tsv','annotation/reference_taxonomy_rows.tsv','annotation/equal_animal_calibration_type_repeat_coverage.tsv.gz','annotation/coordinate_complete.json','annotation/plots_complete.json']
    verified={}
    for name in needed:
        p=BASE/name;r=manifest['files'][name];h=sha(p)
        need(p.stat().st_size==r['bytes'] and h==r['local_content_sha256'],'Downloaded input changed '+name)
        verified[name]={'bytes':p.stat().st_size,'sha256':h,'remote_identity':r['remote_identity']}
    d=pd.read_csv(ANNOT/'peak_repeat_genomic_coverage_by_group.tsv.gz',sep='\t',keep_default_na=False)
    for n in ['overlap_fraction_descriptive','chromosome_coverage_fold_descriptive','chromosome_weighted_expected_fraction']:
        d[n]=pd.to_numeric(d[n],errors='coerce')
    need(len(d)==536796,'Exact producer table row count')
    need(not d.duplicated(['group_id','level','repClass','repFamily','repName']).any(),'Unique source group/category')
    need(((d.callable_peak_union_bp==0)==d.overlap_fraction_descriptive.isna()).all(),'Zero callable groups stay NA')
    q=d.callable_peak_union_bp>0
    need(np.allclose(d.loc[q,'overlap_union_bp']/d.loc[q,'callable_peak_union_bp'],d.loc[q,'overlap_fraction_descriptive'],rtol=1e-12,atol=1e-15),'Coverage arithmetic')
    need(d.loc[q,'overlap_fraction_descriptive'].between(0,1).all(),'Fraction bounds')
    d=d[d.group_id!='CONSENSUS'].copy()
    d['condition']=d.genotype+'_'+d.age
    cols=['level','repClass','repFamily','repName','repeat_kind']
    taxonomy=d[cols].drop_duplicates().sort_values(cols).to_dict('records')
    global CAT
    CAT={}
    for c in taxonomy:
        cid=catid(c['level'],c['repClass'],c['repFamily'],c['repName'])
        label={'class':c['repClass'],'family':c['repFamily'],'subfamily':c['repName'],'any_primary_TE':'All primary TEs','any_repeat':'All repeats'}[c['level']]
        need(cid not in CAT,'Category id unique')
        CAT[cid]={'id':cid,'level':c['level'],'class':c['repClass'],'family':c['repFamily'],'subfamily':c['repName'],'label':label,'repeat_kind':c['repeat_kind']}
    d['category_id']=[catid(*x) for x in d[['level','repClass','repFamily','repName']].itertuples(index=False,name=None)]
    animal_cols=['animal_id','condition','genotype','age','sex','replicate']
    animals=d[animal_cols].drop_duplicates().sort_values(['condition','sex','animal_id'])
    need(len(animals)==20 and animals.animal_id.is_unique,'20 exact animal metadata records')
    need(set(animals.condition)==set(CONDS),'Five cohort conditions with age')
    for c in CONDS:
        a=animals[animals.condition==c];need(len(a)==4 and dict(a.sex.value_counts())=={'female':2,'male':2},'Animal condition balance '+c)
    animal_records=animals.to_dict('records')
    available=d[['cell_type','animal_id','group_id','callable_peak_union_bp','n_peaks']].drop_duplicates()
    need(len(available)==467,'467 exact produced groups')
    types=sorted(d.cell_type.unique())
    need(len(types)==28,'28 initial calibration types')
    need(int((available.callable_peak_union_bp==0).sum())==40,'40 empty/noncallable groups preserved')
    # Independently match complete producer means, including absent-vs-zero semantics.
    saved=pd.read_csv(ANNOT/'equal_animal_calibration_type_repeat_coverage.tsv.gz',sep='\t',keep_default_na=False)
    saved['equal_animal_mean_fraction']=pd.to_numeric(saved.equal_animal_mean_fraction,errors='coerce')
    check=d.groupby(['cell_type','level','repClass','repFamily','repName'],observed=True,dropna=False).overlap_fraction_descriptive.mean().reset_index()
    z=check.merge(saved,on=['cell_type','level','repClass','repFamily','repName'],validate='one_to_one')
    need(len(z)==len(saved)==len(check),'Exact saved mean join')
    need(np.allclose(z.overlap_fraction_descriptive,z.equal_animal_mean_fraction,equal_nan=True,rtol=1e-12,atol=1e-15),'Equal-animal means reproduce producer')
    condition_table=d.groupby(['cell_type','condition','category_id','level','repClass','repFamily','repName','repeat_kind'],observed=True,dropna=False).agg(mean_fraction=('overlap_fraction_descriptive','mean'),mean_fold=('chromosome_coverage_fold_descriptive','mean'),n_callable=('overlap_fraction_descriptive','count'),n_fold=('chromosome_coverage_fold_descriptive','count'),n_available=('animal_id','nunique')).reset_index()
    condition_table['n_expected']=4
    condition_table.to_csv(PLOTS/'all_types_taxonomy_by_condition_equal_animal_summary.tsv.gz',sep='\t',index=False)
    d[d.cell_type=='Microglia'].to_csv(PLOTS/'microglia_all_taxonomy_animal_details.tsv.gz',sep='\t',index=False)
    cell_types=[]
    for t in types:
        f=d[d.cell_type==t];a=available[available.cell_type==t]
        rows=[]
        keys=['animal_id','category_id','group_id','n_peaks','callable_peak_union_bp','overlap_union_bp','overlap_fraction_descriptive','chromosome_coverage_fold_descriptive']
        for values in f[keys].itertuples(index=False,name=None):
            animal,cid,gid,npk,callablebp,overlap,frac,fold=values
            rows.append({'animal_id':animal,'category_id':cid,'group_id':gid,'n_peaks':int(npk),'callable_peak_union_bp':int(callablebp),'overlap_union_bp':int(overlap),'overlap_fraction_descriptive':opt(frac),'fold_descriptive':opt(fold)})
        summary=[]
        for x in condition_table[condition_table.cell_type==t].to_dict('records'):
            summary.append({k:(opt(x[k]) if k in ['mean_fraction','mean_fold'] else int(x[k]) if k.startswith('n_') else x[k]) for k in ['condition','category_id','mean_fraction','mean_fold','n_callable','n_fold','n_available','n_expected']})
        payload={'schema':'te_overlap_cell_type_v1','producer_job_id':'7471562','cell_type':t,'label_basis':'initial_calibration','animals':animal_records,'categories':list(CAT.values()),'rows':rows,'condition_summary':summary,'missing_group_policy':'No source group means unavailable, not zero. The 20 animal metadata rows define all denominators. Empty groups have explicit null coverage/fold.','n_expected_animals':20}
        path=DATA/'cell_types'/(slug(t)+'.json');write_json(path,payload)
        cell_types.append({'id':slug(t),'label':t,'path':'cell_types/'+path.name,'n_available':len(a),'n_callable':int((a.callable_peak_union_bp>0).sum()),'bytes':path.stat().st_size,'sha256':sha(path)})
    heatmap_micro(d,'class','microglia_TE_class_by_condition_heatmap','Microglia · TE classes across genotype and age cohorts')
    familyids,_=heatmap_micro(d,'family','microglia_TE_family_top20_by_condition_heatmap','Microglia · top 20 TE families across cohorts',20)
    subids,_=heatmap_micro(d,'subfamily','microglia_TE_subfamily_top20_by_condition_heatmap','Microglia · top 20 TE subfamilies across cohorts',20)
    micro_boxplots(d)
    pages=all_types_heatmaps(d,types)
    pdfnames=[('Microglia · TE classes by genotype and age','microglia_TE_class_by_condition_heatmap'),('Microglia · 3-month genotype animal boxplots','microglia_TE_genotype_animal_boxplots_3mo'),('Microglia · top 20 TE families','microglia_TE_family_top20_by_condition_heatmap'),('Microglia · top 20 TE subfamilies','microglia_TE_subfamily_top20_by_condition_heatmap'),('All 28 calibration cell types · TE classes by cohort','all_cell_types_TE_class_by_condition_heatmaps')]
    downloads=[{'title':label,'pdf_path':'/ATAC_peak_TE_annotation_20261015/job-7471562/genotype_visualizations/'+name+'.pdf'} for label,name in pdfnames]
    result={'schema':'te_overlap_v1','producer_job_id':'7471562','source_manifest_sha256':'7841253b0eb43c487b128d3f0249e3cf3ce64bf5fab8624909022285f41e1028','label_basis':'initial_calibration','scope':'TE_peak_coordinate_overlap_only','units':{'overlap_fraction_descriptive':'union overlap bp / blacklist-excluded callable peak-union bp; fraction 0–1','fold_descriptive':'observed coverage fraction / chromosome-weighted callable nuclear genomic reference fraction; descriptive ratio, not a statistical enrichment test'},'limitations':['Initial published calibration labels; independent final cell-type labels pending.','No TE expression, per-cell accessibility count or differential genotype test.','Each animal receives equal weight; nuclei and peaks are not biological replicates.','Absent or empty peak-call groups are unavailable (null), not zero.','Class/family/subfamily categories are nonexclusive; percentages need not sum to 100%.','Peak sets, widths, peak counts and fragment depth differ by animal. The chromosome-weighted genomic background is not matched for GC, TSS/gene context or mappability.','repFamily is the native RepeatMasker family; subclass is only a UI alias.','Replicate R1/R2 is the biological animal within genotype/age/sex, not read mates.'],'primary_te_classes_declared':PRIMARY,'primary_te_classes_observed':[x for x in PRIMARY if any(c['level']=='class' and c['class']==x for c in CAT.values())],'conditions':[{'id':c,'label':CLABEL[c],'genotype':animals[animals.condition==c].iloc[0].genotype,'age':animals[animals.condition==c].iloc[0].age,'n_expected':4} for c in CONDS],'animals':animal_records,'cell_types':cell_types,'n_available_groups':467,'n_callable_groups':427,'n_expected_animal_type_pairs':560,'n_empty_noncallable_groups':40,'n_absent_animal_type_pairs':93,'taxonomy_levels':['any_primary_TE','class','family','subfamily','any_repeat'],'repeat_kinds':sorted({c['repeat_kind'] for c in CAT.values()}),'downloads':downloads,'input_provenance':verified,'created_utc':datetime.now(timezone.utc).isoformat(),'new_processing_scope':'Downloaded small coordinate summary tables only; no BAM, fragment, raw count matrix, embedding, peak calling or inference rerun.'}
    write_json(DATA/'manifest.json',result)
    micro=condition_table[(condition_table.cell_type=='Microglia')&(condition_table.level=='any_primary_TE')]
    stats=micro[['condition','mean_fraction','mean_fold','n_callable','n_available','n_expected']].to_dict('records')
    provenance={'status':'verified_coordinate_overlap_adapter_and_descriptive_figures_complete','utc':datetime.now(timezone.utc).isoformat(),'script_sha256':sha(Path(__file__)),'input_hash_checks':verified,'fixture_checks':fixes,'exact_counts':{'source_table_rows':536796,'animal_type_groups_available':467,'animal_type_groups_callable':427,'animal_type_pairs_absent':93,'empty_noncallable_groups':40,'animals':20,'initial_calibration_types':28,'conditions':5,'taxonomy_categories':len(CAT)},'saved_equal_animal_means_reproduced':len(z),'max_saved_mean_error':float(np.nanmax(np.abs(z.overlap_fraction_descriptive-z.equal_animal_mean_fraction))),'microglia_any_primary_TE_by_condition':stats,'top20_selection':'Highest equal-animal mean callable peak-union bp fraction across all 20 Microglia animals, tie order from taxonomy; visualization selection only, full tables and adapter retain all categories.','top20_family_category_ids':familyids,'top20_subfamily_category_ids':subids,'all_type_PDF_pages':pages,'adapter_manifest_sha256':sha(DATA/'manifest.json'),'adapter_total_bytes':sum((DATA/x['path']).stat().st_size for x in cell_types)+(DATA/'manifest.json').stat().st_size,'figures':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(PLOTS.glob('*.pdf'))},'normalization_ready':False,'final_retention_complete':False,'TE_expression_or_fragment_accessibility_measured':False,'inferential_genotype_claim':False}
    write_json(WORK/'data_and_plot_validation.actual.json',provenance)
    (PLOTS/'README.md').write_text('# TE coordinate overlap across genotype and age cohorts\n\nVerified producer job 7471562. These figures describe the fraction of **callable peak-union base pairs** overlapping RepeatMasker TEs, with equal animal weight. They do not measure TE expression or per-cell accessibility and do not test genotype effects. Cell types are the original peak-discovery calibration groups, not final independent annotations.\n\nMicroglia has 20 callable animal groups: five conditions, four animals each (2 female, 2 male). The 3-month genotype boxplot compares WT, 5xFAD and APOE4/TREM2 only; older WT is displayed separately on heatmaps. Point metadata, peak counts and denominator bp are saved in the TSV. NA is retained for absent or empty groups across all cell types. Class/family/subfamily overlap categories can overlap and do not form a composition that must sum to 100%.\n\nThe full family/subfamily tables remain in `all_types_taxonomy_by_condition_equal_animal_summary.tsv.gz` and `microglia_all_taxonomy_animal_details.tsv.gz`; top-20 displays are chosen descriptively by all-animal mean coverage. PDFs are the download format; PNGs are previews only. Native RepeatMasker repFamily is called family; subclass is a display alias.\n')
    print(json.dumps({'status':provenance['status'],'adapter_total_bytes':provenance['adapter_total_bytes'],'manifest':str(DATA/'manifest.json'),'figures':list(provenance['figures']),'microglia':stats},indent=2))

if __name__=='__main__':main()
