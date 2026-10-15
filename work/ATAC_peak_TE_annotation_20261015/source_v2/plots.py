"""Animal-level descriptive peak/RepeatMasker overlap plots; no genotype test."""
import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def main(directory):
    d=pd.read_csv(directory/'peak_repeat_genomic_coverage_by_group.tsv.gz',sep='\t',keep_default_na=False)
    d=d[d.group_id.ne('CONSENSUS')].copy()
    for n in ['overlap_fraction_descriptive','chromosome_coverage_fold_descriptive','callable_peak_union_bp']:
        d[n]=pd.to_numeric(d[n],errors='coerce')
    if d.duplicated(['group_id','level','repClass','repFamily','repName']).any():raise RuntimeError('Duplicate group/category statistic')
    d['condition']=d.genotype+'_'+d.age
    d['category']=d.repClass.astype(str)+'|'+d.repFamily.astype(str)+'|'+d.repName.astype(str)
    # Each producer group is one animal×calibration-type; missing group!=zero.
    means=d.groupby(['cell_type','level','category','repClass','repFamily','repName'],dropna=False,observed=True).agg(
        equal_animal_mean_fraction=('overlap_fraction_descriptive','mean'),
        equal_animal_mean_descriptive_fold=('chromosome_coverage_fold_descriptive','mean'),
        n_animals_available=('animal_id','nunique'),n_callable_animals=('overlap_fraction_descriptive','count')).reset_index()
    means.to_csv(directory/'equal_animal_calibration_type_repeat_coverage.tsv.gz',sep='\t',index=False)
    pd.DataFrame(d[['cell_type','animal_id','condition','genotype','age','sex','replicate']].drop_duplicates()).to_csv(directory/'available_animal_type_groups.tsv',sep='\t',index=False)
    def heatmap(frame,value,name,title,limit=None):
        if frame.empty:return
        matrix=frame.pivot(index='cell_type',columns='category',values=value).sort_index()
        if limit and matrix.shape[1]>limit:
            # Visualization selection only; complete unselected table is saved.
            selected=matrix.mean().sort_values(ascending=False).head(limit).index
            micro=[x for x in matrix.index if 'microgl' in x.lower()]
            if micro:
                selected=selected.union(matrix.loc[micro].mean().sort_values(ascending=False).head(min(20,limit)).index)
            matrix=matrix[selected]
        display=100*matrix if 'fraction' in value else matrix
        fig,ax=plt.subplots(figsize=(max(11,.18*len(display.columns)),max(6,.27*len(display))))
        img=ax.imshow(np.ma.masked_invalid(display.to_numpy()),aspect='auto',interpolation='nearest',cmap='viridis')
        ax.set_yticks(range(len(display)),display.index,fontsize=7)
        ax.set_xticks(range(len(display.columns)),display.columns,rotation=90,fontsize=6)
        ax.set_title(title+'\nPublished calibration labels; equal-animal mean; missing groups remain NA',fontsize=10)
        fig.colorbar(img,ax=ax,label=('% callable peak-union bp' if 'fraction' in value else 'Descriptive observed/chromosome-weighted expected coverage'))
        fig.tight_layout();fig.savefig(directory/(name+'.png'),dpi=170);fig.savefig(directory/(name+'.pdf'));plt.close(fig)
    for level,limit in [('class',None),('family',45),('subfamily',65)]:
        f=means[(means.level==level)&means.repClass.isin(['DNA','LINE','LTR','RC','Retroposon','SINE'])]
        heatmap(f,'equal_animal_mean_fraction','TE_'+level+'_coverage_heatmap','TE '+level+': genomic overlap coverage',limit)
        if level=='class':heatmap(f,'equal_animal_mean_descriptive_fold','TE_class_chromosome_coverage_fold','TE class: descriptive chromosome coverage fold')
    classes=d[(d.level=='class')&d.repClass.isin(['DNA','LINE','LTR','RC','Retroposon','SINE'])]
    with PdfPages(directory/'TE_class_animal_boxplots_all_calibration_types.pdf') as pdf:
        for cell_type,frame in classes.groupby('cell_type',sort=True):
            fig,axes=plt.subplots(2,3,figsize=(15,9))
            for ax,cl in zip(axes.flat,['DNA','LINE','LTR','RC','Retroposon','SINE']):
                f=frame[frame.repClass==cl];conditions=sorted(f.condition.unique());arrays=[];positions=[]
                for i,c in enumerate(conditions):
                    v=100*f.loc[f.condition==c,'overlap_fraction_descriptive'].dropna().to_numpy()
                    if len(v):
                        arrays.append(v);positions.append(i);ax.scatter(i+np.linspace(-.1,.1,len(v)),v,s=17,color='#1c6986',zorder=3)
                if arrays:ax.boxplot(arrays,positions=positions,showfliers=False,widths=.5)
                ax.set_xticks(range(len(conditions)),conditions,rotation=35,ha='right',fontsize=8);ax.set_title(cl)
                ax.set_ylabel('% callable peak-union bp');ax.grid(axis='y',alpha=.2)
            fig.suptitle(cell_type+' — each point is one animal; descriptive overlap, no genotype p-value\nGroups not produced/empty retain NA; classes may overlap',fontsize=11)
            fig.tight_layout();pdf.savefig(fig);plt.close(fig)
    micro=d[d.cell_type.str.contains('microgl',case=False,na=False)]
    micro.to_csv(directory/'microglia_all_repeat_coverage_animal_details.tsv.gz',sep='\t',index=False)
    micro_means=means[means.cell_type.str.contains('microgl',case=False,na=False)]
    for level in ['family','subfamily']:
        heatmap(micro_means[(micro_means.level==level)&micro_means.repClass.isin(['DNA','LINE','LTR','RC','Retroposon','SINE'])],
            'equal_animal_mean_fraction','microglia_TE_'+level+'_coverage','Microglia: TE '+level+' overlap',65)
    (directory/'plots_complete.json').write_text(json.dumps(dict(status='descriptive_animal_level_peak_repeat_plots_complete',
        all_cell_types_preserved=True,microglia_extra_view=True,replicates='animals; no nuclei treated as biological replicates',
        heatmap_selection='all classes; top45families/top65subfamilies plus microglia top20; full tables preserve all categories',
        category_fractions_nonexclusive=True,missing_or_empty_groups_imputed_as_zero=False,
        inferential_genotype_effect_claim=False,TE_expression_claim=False,normalization_ready=False),indent=2)+'\n')


if __name__=='__main__':main(Path(sys.argv[1]))
