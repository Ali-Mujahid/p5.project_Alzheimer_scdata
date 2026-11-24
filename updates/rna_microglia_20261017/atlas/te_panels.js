(() => {
  const root = document.getElementById('te-panels-bde');
  if (!root) return;
  const clusterNames = ['WT 21 mo-specific','5xFAD-specific','Higher in WT 21 mo only','Higher in 5xFAD only','Higher in both targets'];
  const countFmt = n => n.toLocaleString('en-US');
  const el = id => root.querySelector('#bde-'+id);
  const text = (x,y,s,attrs='') => '<text x="'+x+'" y="'+y+'" '+attrs+'>'+s+'</text>';
  const rect = (x,y,w,h,fill) => '<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" fill="'+fill+'"/>';
  const line = (x,y,xx,yy,opt='') => '<line x1="'+x+'" y1="'+y+'" x2="'+xx+'" y2="'+yy+'" stroke="#58686c" '+opt+'/>';
  const wrap = (w,h,title,body) => '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+w+' '+h+'" width="'+w+'" height="'+h+'" role="img" aria-label="'+title+'" font-family="Arial, sans-serif" font-size="13" fill="#1f363c"><title>'+title+'</title>'+rect(0,0,w,h,'white')+body+'</svg>';
  const rgb = c => [1,3,5].map(n => parseInt(c.slice(n,n+2),16));
  function mix(a,b,t) {
    const start=rgb(a),end=rgb(b);
    return '#'+start.map((x,i)=>Math.round(x+Math.min(1,Math.max(0,t))*(end[i]-x)).toString(16).padStart(2,'0')).join('');
  }
  function drawScale(x,y,w,colors,labels,id) {
    let s='<defs><linearGradient id="'+id+'">'+colors.map((c,i)=>'<stop offset="'+100*i/(colors.length-1)+'%" stop-color="'+c+'"/>').join('')+'</linearGradient></defs>';
    s+=rect(x,y,w,9,'url(#'+id+')');
    labels.forEach((v,i)=>{s+=text(x+w*i/(labels.length-1),y+24,v,'text-anchor="middle" font-size="11"');});
    return s;
  }
  function saveSvg(container,filename) {
    const svg=el(container).querySelector('svg');
    if (!svg) return;
    const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml'}));
    const link=document.createElement('a');link.href=url;link.download=filename+'.svg';link.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  const tsv = async name => {
    const r=await fetch('downloads/'+name);
    if (!r.ok) throw Error('Cannot load '+name);
    const lines=(await r.text()).trimEnd().split(/\r?\n/), head=lines.shift().split('\t');
    return lines.map(l=>Object.fromEntries(l.split('\t').map((v,i)=>[head[i],v])));
  };
  const data={};
  function heat(panel) {
    const isD=panel==='d', low=el(panel+'-low').value, high=el(panel+'-high').value;
    const cap=el(panel+'-cap').valueAsNumber;
    if (!(cap>0 && Number.isFinite(cap))) {el(panel+'-status').textContent='Enter a positive scale limit.';return;}
    const middle=isD?null:el('e-mid').value;
    const cols=isD?['Promoter',el('d-reference').value,'H3K27me3','H3K9me3','No signal']:['hypo','hyper'];
    const x0=207, y0=104, cw=isD?119:165, rh=36, w=x0+cw*cols.length+24, h=360;
    const title=isD?'D   Reference chromatin at microglial TE copies':'E   Age-related methylation at microglial TE copies';
    let svg=text(15,26,title,'font-size="19" font-weight="bold"');
    svg+=text(15,49,isD?'Zhu adult mouse microglia  ·  Percentage of eligible TE midpoints':'18 mo versus 8 wk  ·  log₂(observed / matched expected overlap)','font-size="12"');
    cols.forEach((s,j)=>{svg+=text(x0+(j+.5)*cw,y0-12,isD?s:(j?'Hypermethylated':'Hypomethylated'),'text-anchor="middle" font-weight="bold"');});
    clusterNames.forEach((name,i)=>{
      const id='C'+(i+1),y=y0+i*rh;
      svg+=text(15,y+23,id,'font-weight="bold"')+text(42,y+23,name);
      cols.forEach((s,j)=>{
        const record=data[panel].find(r=>isD?r.cluster===id&&r.feature===s:r.cluster_id===id&&r.age_change===s);
        const val=Number(isD?record.value:record.log2_observed_expected);
        const color=isD?mix(low,high,val/cap):val<0?mix(middle,low,-val/cap):mix(middle,high,val/cap);
        const luminance=rgb(color).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
        const light=.2126*luminance[0]+.7152*luminance[1]+.0722*luminance[2];
        const label=isD?val.toFixed(1)+'%':(val>0?'+':'')+val.toFixed(2);
        const tip=isD?countFmt(+record.copies)+' of '+countFmt(+record.total)+' eligible copies; '+countFmt(+record.unmeasured)+' unmeasured':record.observed+' observed, '+(+record.matched_expected).toFixed(1)+' expected, '+countFmt(+record.callable)+' callable';
        svg+='<g><title>'+id+' · '+s+' · '+tip+'</title>'+rect(x0+j*cw,y,cw-1,rh-1,color)+text(x0+(j+.5)*cw,y+23,label,'text-anchor="middle" fill="'+(light>.18?'#132629':'#ffffff')+'"')+'</g>';
      });
    });
    svg+=drawScale(x0,304,Math.min(cw*cols.length-4,280),isD?[low,high]:[low,middle,high],isD?['0%',cap+'%']:[String(-cap),'0','+'+cap],'bde-key-'+panel);
    el(panel+'-plot').innerHTML=wrap(w,h,title,svg);
    el(panel+'-status').textContent='';
  }
  for (const p of ['d','e']) {
    const update=()=>{if(data[p])heat(p);};
    el(p+'-fields').addEventListener('input',update);
    el(p+'-export').onclick=()=>saveSvg(p+'-plot','Panel_'+p.toUpperCase()+'_C1-C5');
    tsv(p==='d'?'Panel_D_values.tsv?v=zhu2':'Panel_E_values.tsv').then(rows=>{data[p]=rows;update();}).catch(e=>{el(p+'-status').textContent=e.message;});
  }

  let genome,worker;
  let distribution='exact', current=null, exporting=false;
  function inScope(scope,i) {
    if(scope==='WT3') return genome.control[i]!==0;
    if(scope==='clusters') return genome.group[i]!==0;
    if(scope[0]==='C') return genome.group[i]===Number(scope[1]);
    return true;
  }
  function hitClass(x,p,cutoff) {return p<cutoff ? (x>0?1:x<0?2:0) : 0;}
  function inAxes(x,p,xMax,yMax) {return Math.abs(x)<=xMax && -Math.log10(p)<=yMax;}
  function download(blob,name) {
    const link=document.createElement('a'),url=URL.createObjectURL(blob);
    link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),5000);
  }
  async function exportList(target) {
    if(!current||!genome||exporting) return;
    const settings={...current,target,format:el('format').value,direction:el('dir').value,extent:el('extent').value};
    const panels=target==='both'?[0,1]:[target==='WT_21mo'?0:1];
    const source=panels.map(j=>[genome.values[3*j],genome.values[3*j+(settings.metric==='raw'?1:2)]]);
    const keep=[];
    for(let i=0;i<genome.group.length;i++) {
      if(!inScope(settings.scope,i)) continue;
      const ok=source.every(([f,ps])=>{
        const x=f[i],p=ps[i],kind=hitClass(x,p,settings.cutoff);
        return kind && (settings.direction==='any'||kind===(settings.direction==='up'?1:2))
          && (settings.extent==='all'||inAxes(x,p,settings.xMax,settings.yMax));
      });
      if(ok) keep.push(i);
    }
    if(!keep.length && settings.format==='bed') {
      el('list-status').textContent='Zero qualifying TE copies. A BED file would contain no intervals.';return;
    }
    const indices=Uint32Array.from(keep);
    el('list-status').textContent='Preparing '+countFmt(keep.length)+' TE copies…';
    exporting=true;el('list-fields').disabled=true;
    worker.postMessage({indices,settings},[indices.buffer]);
  }
  el('list-fields').querySelectorAll('[data-list]').forEach(b=>{b.onclick=()=>exportList(b.dataset.list);});
  el('modes').querySelectorAll('[data-mode]').forEach(b=>{b.onclick=()=>{
    distribution=b.dataset.mode;
    el('modes').querySelectorAll('[data-mode]').forEach(a=>a.setAttribute('aria-pressed',String(a===b)));
    if(genome) volcano(); else if(!worker) el('load').click();
  };});
  const scopes={WT3:'Detected in WT 3 mo',either:'Detected in either group',clusters:'C1–C5 combined'};
  for(let i=1;i<=5;i++) scopes['C'+i]='C'+i+' · '+clusterNames[i-1];
  for(const [key,name] of Object.entries(scopes)) el('scope').add(new Option(name,key));
  function volcano() {
    if (!genome) return;
    const scope=el('scope').value, metric=el('metric').value, cut=el('cut').valueAsNumber;
    const radius=el('radius').valueAsNumber, xMax=el('x').valueAsNumber, yMax=el('y').valueAsNumber;
    const density=distribution==='density', color=['ns','up','down'].map(k=>el(k).value);
    if (!(cut>0&&cut<1&&radius>0&&xMax>0&&yMax>0&&[cut,radius,xMax,yMax].every(Number.isFinite))){
      current=null;el('list-fields').disabled=true;el('v-export').disabled=true;el('v-status').textContent='Enter a cutoff between zero and one and positive sizes and axis limits.';return;
    }
    current={scope,metric,cutoff:cut,xMax,yMax,distribution};
    el('v-export').disabled=false;el('list-fields').disabled=exporting;
    el('list-status').textContent='';
    const w=915,h=444,left=65,top=106,pw=362,ph=231;
    const title='B   Microglial TE RNA relative to WT 3 mo';
    const mLabel=metric==='raw'?'raw P':'BH-adjusted P';
    let svg=text(16,28,title,'font-size="20" font-weight="bold"')+text(16,51,scopes[scope]+'  ·  '+mLabel+' &lt; '+cut+'  ·  '+(density?'Binned density':distribution==='spread'?'Spread overlapping dots':'Observed coordinates'),'font-size="13"');
    let clipped=0;
    const totals=[];
    const {values}=genome;
    for (let panel=0;panel<2;panel++) {
      const start=left+panel*440, fc=values[3*panel], p=values[3*panel+(metric==='raw'?1:2)];
      const maps=[new Map(),new Map(),new Map()];
      const n=[0,0,0], occupied=distribution==='spread'?new Set():null;
      let offscreen=0;
      // Round display coordinates to 0.02 SVG units. Opaque coincident points share the same ink.
      const step=density?3:.02, stride=Math.ceil(pw/step)+2;
      for(let i=0;i<p.length;i++){
        if(!inScope(scope,i)||!Number.isFinite(p[i])) continue;
        const x=fc[i],y=-Math.log10(p[i]),c=hitClass(x,p[i],cut);
        n[c]++;
        if(!inAxes(x,p[i],xMax,yMax)){offscreen++;continue;}
        let displayX=(x+xMax)*pw/(2*xMax);
        const displayY=(1-y/yMax)*ph;
        if(occupied) {
          const pixel=Math.round(displayY)*(pw+1)+Math.round(displayX);
          if(occupied.has(pixel) && x!==0) {
            let hash=Math.imul(i+1,0x9e3779b1)>>>0; hash=(hash^(hash>>>16))>>>0;
            const shifted=displayX+((hash/4294967295)*2-1)*3;
            displayX=x<0?Math.max(0,Math.min(pw/2-.001,shifted)):Math.min(pw,Math.max(pw/2+.001,shifted));
          }
          occupied.add(pixel);
        }
        const xx=Math.round(displayX/step),yy=Math.round(displayY/step);
        const key=yy*stride+xx, map=maps[c];
        map.set(key,density?(map.get(key)||0)+1:1);
      }
      clipped+=offscreen;totals.push(n);
      svg+=text(start,76,panel?'5xFAD 3 mo vs WT 3 mo':'WT 21 mo vs WT 3 mo','font-size="16" font-weight="bold"');
      svg+=text(start,96,countFmt(n.reduce((a,b)=>a+b,0))+' tested   ·   '+countFmt(n[1])+' up   ·   '+countFmt(n[2])+' down','font-size="12"');
      svg+='<defs><clipPath id="bde-clip'+panel+'">'+rect(start,top,pw,ph,'white')+'</clipPath></defs><g clip-path="url(#bde-clip'+panel+')">';
      for(let c=0;c<3;c++) {
        const paths=new Map();
        for(const [key,qty] of maps[c]){
          const x=(start+(key%stride)*step).toFixed(2),y=(top+Math.floor(key/stride)*step).toFixed(2);
          const level=density?Math.min(7,Math.floor(Math.log2(qty))):0;
          if(!paths.has(level)) paths.set(level,[]);
          paths.get(level).push('M'+x+' '+y+(density?'h3v3h-3z':'h.001'));
        }
        for(const [level,parts] of paths) {
          svg+=density?'<path fill="'+mix('#ffffff',color[c],.28+.1*level)+'" d="'+parts.join('')+'"/>':
            '<path fill="none" stroke="'+color[c]+'" stroke-linecap="round" stroke-width="'+2*radius+'" d="'+parts.join('')+'"/>';
        }
      }
      if(n[0]+n[1]+n[2]===0) svg+=text(start+pw/2,top+ph/2,'No testable RNA in this comparison','text-anchor="middle" fill="#58686c"');
      const thresholdY=top+ph*(1+Math.log10(cut)/yMax);
      svg+=line(start+pw/2,top,start+pw/2,top+ph,'stroke-opacity=".4"');
      svg+=line(start,thresholdY,start+pw,thresholdY,'stroke-dasharray="4 4"')+'</g>';
      svg+=line(start,top,start,top+ph)+line(start,top+ph,start+pw,top+ph);
      for(let j=0;j<=4;j++){
        const x=start+j*pw/4;
        svg+=text(x,top+ph+20,Number((-xMax+j*xMax/2).toFixed(2)),'text-anchor="middle"');
      }
      for(let j=0;j<=5;j++){
        const y=top+ph-j*ph/5;
        svg+=line(start-3,y,start,y)+text(start-6,y+4,Number((j*yMax/5).toFixed(2)),'text-anchor="end" font-size="11"');
      }
    }
    svg+=text(17,225,'−log₁₀('+mLabel+')','text-anchor="middle" transform="rotate(-90 17 225)"');
    svg+=text(w/2,382,'TE RNA log₂ fold change (target / WT 3 mo)','text-anchor="middle"');
    [['Increase',1],['Decrease',2],[mLabel+' ≥ '+cut,0]].forEach(([label,i],j)=>{
      const x=190+165*j;svg+='<circle cx="'+x+'" cy="407" r="4" fill="'+color[i]+'"/>'+text(x+10,411,label);
    });
    const note=(density?'Density uses 3-unit bins. Color darkens with each doubling, up to 128+ copies per class and bin.  ':distribution==='spread'?'Overlapping dots are spread up to 3 SVG units horizontally. Downloads retain measured coordinates.  ':'')+(clipped?countFmt(clipped)+' points outside the displayed range.':'');
    svg+=text(16,436,note,'font-size="11"');
    el('v-plot').innerHTML=wrap(w,h,title,svg);
    el('v-plot').dataset.totals=JSON.stringify(totals);
    el('v-status').textContent=clipped?countFmt(clipped)+' points outside the displayed range. Totals include all tested copies.':'All tested copies in the selected set are within the displayed range.';
    el('radius').disabled=density;
  }
  el('v-fields').addEventListener('change',volcano);
  el('v-export').onclick=()=>saveSvg('v-plot','Panel_B_'+el('scope').value+'_'+el('metric').value+'_'+distribution);
  el('load').onclick=()=>{
    if (worker||genome) return;
    el('load').disabled=true;el('v-status').textContent='Loading count tables…';
    worker=new Worker('te_panels_worker.js?v=zhu2');
    const fail=message=>{worker.terminate();worker=null;el('load').disabled=false;el('v-status').textContent=message+' · Try loading the tables again.';};
    worker.onerror=event=>fail(event.message);
    worker.onmessage=({data})=>{
      if(data.exported || data.exportError) {
        exporting=false;el('list-fields').disabled=!current;
        if(data.exportError){el('list-status').textContent=data.exportError;return;}
        download(data.exported,data.filename);
        el('list-status').textContent='Downloaded '+countFmt(data.count)+' TE copies · '+data.filename;
        return;
      }
      if(data.error) return fail(data.error);
      if(data.progress!==undefined){el('v-status').textContent='Reading full-precision count tables · '+data.progress+'%';return;}
      genome=data;el('load').hidden=true;el('v-fields').disabled=false;el('v-export').disabled=false;volcano();
    };
    worker.postMessage({load:true});
  };
})();
