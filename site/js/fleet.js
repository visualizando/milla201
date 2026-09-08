/* Public derived data only. MMSI are not asserted to be unique physical ships. */
(() => {
 const $=id=>document.getElementById(id), number=new Intl.NumberFormat('es-AR');
 const flags={CHN:'China',ESP:'España',ARG:'Argentina',KOR:'Corea del Sur',TWN:'Taiwán',URY:'Uruguay',BRA:'Brasil',FLK:'Malvinas (FLK en GFW)',BLZ:'Belice',UNKNOWN:'Sin bandera identificada'};
 let data, chosen;
 const text=(tag,value)=>{const el=document.createElement(tag);el.textContent=value;return el;};
 function charts(){
  const root=$('fleet-returning'), width=root.clientWidth;
  const rows=data.transitions.flatMap(d=>[{year:String(d.year)+(d.partial_year?'*':''),kind:'Ya había aparecido',count:d.seen_in_earlier_year},{year:String(d.year)+(d.partial_year?'*':''),kind:'Primera vez en la serie',count:d.first_seen_with_gap}]);
  root.replaceChildren(Plot.plot({width,height:280,marginLeft:48,style:{fontFamily:'Montserrat, system-ui'},x:{type:'band',label:null},y:{label:'MMSI con gaps',grid:true},color:{domain:['Ya había aparecido','Primera vez en la serie'],range:['#286b8b','#c7cdd1'],legend:true},marks:[Plot.barY(rows,{x:'year',y:'count',fill:'kind',title:d=>`${d.year} · ${d.kind}: ${d.count}`}),Plot.ruleY([0])]}));
  const top=data.vessels.slice(0,20), lookup=new Map(data.annual.map(r=>[r.mmsi+'/'+r.year,r.gaps]));
  const cells=top.flatMap(v=>Array.from({length:10},(_,i)=>({mmsi:v.mmsi,name:v.name||v.mmsi,year:String(2017+i)+(i===9?'*':''),gaps:lookup.get(v.mmsi+'/'+(2017+i))||0})));
  $('fleet-heatmap').replaceChildren(Plot.plot({width:Math.max(740,width),height:620,marginLeft:200,marginRight:24,marginTop:40,style:{fontFamily:'Montserrat, system-ui'},x:{type:'band',label:null,axis:'top'},y:{domain:top.map(v=>v.mmsi),label:null,tickFormat:m=>top.find(v=>v.mmsi===m).name||m},color:{type:'sqrt',scheme:'Blues',domain:[0,Math.max(...cells.map(c=>c.gaps))],legend:false,label:'Gaps'},marks:[Plot.cell(cells,{x:'year',y:'mmsi',fill:'gaps',inset:1,title:d=>`${d.name} · ${d.mmsi}\n${d.year}: ${d.gaps} gaps`}),Plot.text(cells,{x:'year',y:'mmsi',text:'gaps',fill:d=>d.gaps>40?'white':'#201314',fontSize:10})]}));
  const f=data.flags.slice(0,8).map(r=>({...r,label:flags[r.flag]||r.flag}));
  $('fleet-flags').replaceChildren(Plot.plot({width,height:300,marginLeft:width<600?120:175,marginRight:55,style:{fontFamily:'Montserrat, system-ui'},x:{label:'Gaps · 2017–2026 parcial',grid:true},y:{domain:f.map(r=>r.label),label:null},marks:[Plot.barX(f,{y:'label',x:'gaps',fill:'#286b8b',title:r=>`${r.label}: ${number.format(r.gaps)} gaps · ${r.mmsi} MMSI`}),Plot.text(f,{y:'label',x:'gaps',text:r=>number.format(r.gaps),textAnchor:'start',dx:5})]}));
 }
 function details(v){
  chosen=v; const root=$('fleet-detail'); root.replaceChildren(text('h3',`${v.name||'Sin nombre'} · ${v.mmsi}`));
  root.append(text('p',`Nombres en los eventos: ${v.names||'sin dato'}. Bandera(s): ${v.flags}. Identificadores GFW asociados: ${v.vessel_ids.split(' | ').length}.`));
  if(v.identity_search_entries!=='')root.append(text('p',`Consulta de identidad: ${v.identity_search_entries} resultados. Arte(s) de registro: ${v.registry_geartypes.replaceAll('TRAWLERS','arrastre')||'sin dato'}. Eslora(s): ${v.registry_lengths_m||'sin dato'}${v.registry_lengths_m?' m':''}. IMO candidato(s): ${v.registry_imos||'sin dato'}. Estos datos no resuelven por sí solos las identidades históricas.`));
  const table=document.createElement('table'), head=document.createElement('thead'), tr=document.createElement('tr');
  for(const label of ['Año','Gaps regionales','Bandera en gaps','Meses con presencia en ZEE'])tr.append(text('th',label)); head.append(tr);table.append(head);
  const body=document.createElement('tbody');
  for(let year=2017;year<=2026;year++){const a=data.annual.find(r=>r.mmsi===v.mmsi&&r.year===year),p=data.presence_by_vessel_year.find(r=>r.mmsi===v.mmsi&&r.year===year), row=document.createElement('tr');for(const value of [year===2026?'2026*':year,a?.gaps||0,a?.flags||'—',p?.months||0])row.append(text('td',value));body.append(row);}
  table.append(body);const wrap=document.createElement('div');wrap.className='table-wrap';wrap.append(table);root.append(wrap,text('p','* 2026: gaps hasta el 3 de septiembre; presencia hasta agosto. Los meses no son visitas. Cero es ausencia de registros en estas consultas.'));
 }
 function table(){
  const query=$('fleet-search').value.trim().toUpperCase(), filter=$('fleet-filter').value;
  let rows=data.vessels.filter(v=>(v.names+' '+v.mmsi+' '+v.flags).toUpperCase().includes(query));
  if(filter==='repeat')rows=rows.filter(v=>v.years_with_gaps>1);
  if(filter==='inside')rows=rows.filter(v=>v.either_endpoint_inside_eez>0).sort((a,b)=>b.either_endpoint_inside_eez-a.either_endpoint_inside_eez);
  if(filter==='foreign')rows=rows.filter(v=>!v.flags.includes('ARG')&&v.flags!=='UNKNOWN'&&v.eez_presence_years>1).sort((a,b)=>b.eez_presence_years-a.eez_presence_years||b.eez_presence_months-a.eez_presence_months);
  $('fleet-table-count').textContent=`${number.format(rows.length)} MMSI coinciden. Mostramos los primeros ${Math.min(rows.length,100)}; el CSV incluye todos.`;
  const body=$('fleet-table').querySelector('tbody');body.replaceChildren();
  for(const v of rows.slice(0,100)){const tr=document.createElement('tr'),td=document.createElement('td'),button=text('button',`${v.name||'Sin nombre'} · ${v.mmsi}`);button.type='button';button.addEventListener('click',()=>details(v));td.append(button);tr.append(td);for(const value of [v.flags,v.gaps,v.years_with_gaps,v.either_endpoint_inside_eez,v.eez_presence_years])tr.append(text('td',value));body.append(tr);}
 }
 async function start(){try{const response=await fetch('data/fleet-analysis.json');if(!response.ok)throw Error('Fleet data unavailable');data=await response.json();await document.fonts.ready;charts();table();details(data.vessels[0]);$('fleet-search').addEventListener('input',table);$('fleet-filter').addEventListener('change',table);let timer;window.addEventListener('resize',()=>{clearTimeout(timer);timer=setTimeout(charts,150);});}catch(e){$('fleet-error').hidden=false;$('fleet-error').textContent='No se pudo cargar el análisis por barco. Podés descargar los CSV de esta sección.';console.error(e);}}
 start();
})();
