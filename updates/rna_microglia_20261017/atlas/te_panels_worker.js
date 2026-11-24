/* Keep the compressed source parts for exports. The plot gets only typed numerical columns. */
let sources = [];
async function linesOf(bytes) {
  const compressed = bytes[0] === 31 && bytes[1] === 139;
  const body = compressed
    ? await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).text()
    : new TextDecoder().decode(bytes);
  return body.trimEnd().split('\n');
}
async function loadTables() {
  const response = await fetch('downloads/BDE_sources.json');
  if (!response.ok) throw Error('Source manifest unavailable');
  const {shards} = await response.json();
  const length = shards.reduce((a, item) => a + item.rows, 0);
  const group = new Uint8Array(length), control = new Uint8Array(length);
  const values = Array.from({length:6}, () => new Float64Array(length));
  let offset = 0;
  for (const shard of shards) {
    const res = await fetch('downloads/' + shard.name);
    if (!res.ok) throw Error(shard.name + ' unavailable');
    const bytes = new Uint8Array(await res.arrayBuffer());
    const lines = await linesOf(bytes), header = lines.shift().split('\t');
    const fields = ['WT_21mo','5xFAD_3mo'].flatMap(t => ['logFC','PValue','padj'].map(k => header.indexOf(t+'_vs_WT_3mo_'+k)));
    const cluster=header.indexOf('Figure_C_cluster'), wt=header.indexOf('WT_3mo_positive_mice');
    if (lines.length!==shard.rows || [cluster,wt,...fields].includes(-1)) throw Error('Unexpected count table layout');
    sources.push({bytes, start:offset, end:offset+shard.rows, header});
    for (const line of lines) {
      const cols=line.split('\t');
      group[offset]=/^C[1-5]$/.test(cols[cluster]) ? +cols[cluster][1] : 0;
      control[offset]=+cols[wt]>0;
      for(let j=0;j<fields.length;j++) values[j][offset]=Number(cols[fields[j]]);
      offset++;
    }
    self.postMessage({progress:Math.round(100*offset/length)});
  }
  self.postMessage({group, control, values}, [group.buffer,control.buffer,...values.map(v=>v.buffer)]);
}

async function exportHits({indices,settings}) {
  const {target, format, scope, metric, cutoff, extent, direction, distribution, xMax, yMax}=settings;
  const targets=target==='both'?['WT_21mo','5xFAD_3mo']:[target];
  const header=sources[0].header;
  const fields=header.filter(k=>!k.includes('_vs_WT_3mo_') || targets.some(t=>k.startsWith(t+'_vs_WT_3mo_')));
  const keep=fields.map(k=>header.indexOf(k));
  const directionCols=targets.map(t=>header.indexOf(t+'_vs_WT_3mo_logFC'));
  const idx=Object.fromEntries(header.map((v,i)=>[v,i]));
  const bed=format==='bed', sep=format==='csv'?',':'\t', chunks=[];
  const write=fields=>fields.map(x=>{
    const s=String(x);
    return format==='csv' && /[",\r\n]/.test(s)?'"'+s.replaceAll('"','""')+'"':s;
  }).join(sep)+'\n';
  if(!bed) chunks.push(write([...fields,...targets.map(t=>t+'_direction'),'selection_scope','significance_measure','threshold','direction_filter','export_extent','display_mode','x_limit','y_limit']));
  let cursor=0;
  for(const part of sources) {
    if(cursor===indices.length) break;
    if(indices[cursor]>=part.end) continue;
    const lines=await linesOf(part.bytes), buffer=[];
    while(cursor<indices.length && indices[cursor]<part.end) {
      const cols=lines[indices[cursor++]-part.start+1].split('\t');
      if(bed) buffer.push([cols[idx.chr],cols[idx.start],cols[idx.end],cols[idx.TE_locus],0,cols[idx.strand]].join('\t')+'\n');
      else buffer.push(write([...keep.map(i=>cols[i]),...directionCols.map(i=>+cols[i]>0?'up':'down'),scope,metric,cutoff,direction,extent,distribution,xMax,yMax]));
      if(buffer.length===4096){chunks.push(buffer.join(''));buffer.length=0;}
    }
    if(buffer.length) chunks.push(buffer.join(''));
  }
  if(cursor!==indices.length) throw Error('Locus selection and source rows disagree');
  const mime=format==='csv'?'text/csv':bed?'text/plain':'text/tab-separated-values';
  self.postMessage({exported:new Blob(chunks,{type:mime+';charset=utf-8'}), count:cursor,
    filename:[target==='both'?'WT21_and_5xFAD_shared':target+'_vs_WT_3mo',scope,metric,String(cutoff),direction,extent,distribution].join('_')+'.'+format});
}
self.onmessage=async ({data})=>{
  try {
    if(data.indices) await exportHits(data);
    else await loadTables();
  } catch(error) {
    self.postMessage(data.indices?{exportError:error.message}:{error:error.message});
  }
};
