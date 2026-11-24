/* Load the downloadable count tables off the UI thread, retaining the original model precision. */
self.onmessage = async function () {
  try {
    const source = await fetch('downloads/BDE_sources.json');
    if (!source.ok) throw Error('Source manifest unavailable');
    const {shards} = await source.json();
    const length = shards.reduce((a, item) => a + item.rows, 0);
    const group = new Uint8Array(length);
    const control = new Uint8Array(length);
    const values = Array.from({length: 6}, () => new Float64Array(length));
    let offset = 0;
    for (const shard of shards) {
      const res = await fetch('downloads/' + shard.name);
      if (!res.ok) throw Error(shard.name + ' unavailable');
      // Some static hosts serve gzip as HTTP content-encoding, which fetch decodes first.
      const bytes = new Uint8Array(await res.arrayBuffer());
      const compressed = bytes[0] === 31 && bytes[1] === 139;
      const body = compressed
        ? await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).text()
        : new TextDecoder().decode(bytes);
      const lines = body.trimEnd().split('\n');
      const header = lines.shift().split('\t');
      const fields = ['WT_21mo','5xFAD_3mo'].flatMap(target => ['logFC','PValue','padj'].map(key => header.indexOf(target + '_vs_WT_3mo_' + key)));
      const cluster = header.indexOf('Figure_C_cluster'), wt = header.indexOf('WT_3mo_positive_mice');
      if (lines.length !== shard.rows || [cluster,wt,...fields].includes(-1)) throw Error('Unexpected count table layout');
      for (const line of lines) {
        const cols = line.split('\t');
        group[offset] = /^C[1-5]$/.test(cols[cluster]) ? +cols[cluster][1] : 0;
        control[offset] = +cols[wt] > 0;
        for (let j=0; j<fields.length; j++) values[j][offset] = Number(cols[fields[j]]);
        offset++;
      }
      self.postMessage({progress: Math.round(100*offset/length)});
    }
    self.postMessage({group, control, values}, [group.buffer,control.buffer,...values.map(v => v.buffer)]);
  } catch (err) { self.postMessage({error: String(err.message || err)}); }
};
