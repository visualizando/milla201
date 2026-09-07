/* Maps are reimplemented from the notebook's geographic count approach.
   Only derived public files are fetched; no authenticated calls in the browser. */
const {d3,topojson,Plot}=window;
const token=name=>getComputedStyle(document.documentElement).getPropertyValue('--color-'+name).trim();
const palette={ink:token('primary'),mint:token('secondary'),paper:token('neutral'),surface:token('surface'),border:token('border')};
const fmt=new Intl.NumberFormat('es-AR');
const state={data:null,land:null,range:[2017,2026]};
const byId=id=>document.getElementById(id);
const within=y=>y>=state.range[0]&&y<=state.range[1];
const bbox={type:'Polygon',coordinates:[[[-70,-60],[-70,-30],[-40,-30],[-40,-60],[-70,-60]]]};
function canvasMap(id,regional=false){
 const root=byId(id),width=root.clientWidth,height=regional?Math.round(width*1.05):Math.round(width*.48);
 const canvas=document.createElement('canvas');const ratio=Math.min(devicePixelRatio||1,2);
 canvas.width=width*ratio;canvas.height=height*ratio;canvas.style.height=height+'px';
 const ctx=canvas.getContext('2d');ctx.scale(ratio,ratio);
 const projection=regional?d3.geoMercator().fitExtent([[8,8],[width-8,height-8]],bbox):d3.geoEqualEarth().rotate([-10,0]).fitExtent([[10,8],[width-10,height-8]],{type:'Sphere'});
 const path=d3.geoPath(projection,ctx);
 ctx.fillStyle=regional?'#e1edf2':'#112d40';ctx.beginPath();path({type:'Sphere'});ctx.fill();
 ctx.strokeStyle=regional?'#c3d7e1':'#203d50';ctx.lineWidth=.5;ctx.beginPath();path(d3.geoGraticule10());ctx.stroke();
 // Aggregate in projected screen cells. Fixed color domain keeps periods comparable as counts.
 const bins=new Map(),size=regional?4:3;
 if(regional){for(const [year,lon,lat] of state.data.regional){if(!within(year))continue;const p=projection([lon,lat]);if(!p)continue;const key=`${Math.floor(p[0]/size)},${Math.floor(p[1]/size)}`;bins.set(key,(bins.get(key)||0)+1);}}
 else{for(const [year,lon,lat,n] of state.data.cells){if(!within(year))continue;const p=projection([lon,lat]);if(!p)continue;const key=`${Math.floor(p[0]/size)},${Math.floor(p[1]/size)}`;bins.set(key,(bins.get(key)||0)+n);}}
 const color=d3.scaleLog().domain([1,5,25,100]).range(['#527fa9','#d88782','#f7825f','#ffdd76']).clamp(true);
 for(const [key,n]of bins){const[x,y]=key.split(',').map(Number);ctx.fillStyle=color(n);ctx.fillRect(x*size,y*size,size+0.3,size+0.3);}
 ctx.fillStyle=regional?'#fcfdfd':'#284252';ctx.strokeStyle=regional?'#a8bdc9':'#425c6b';ctx.lineWidth=.6;ctx.beginPath();path(state.land);ctx.fill();ctx.stroke();
 if(!regional){ctx.strokeStyle='#f0bd7d';ctx.lineWidth=1;ctx.setLineDash([4,3]);ctx.beginPath();path(bbox);ctx.stroke();ctx.setLineDash([]);}
 else{ctx.fillStyle='#466575';ctx.font='12px Montserrat, system-ui';for(const[label,lon,lat]of[['ARGENTINA',-65,-41],['URUGUAY',-56,-33],['ATLÁNTICO SUR',-49,-46]]){const p=projection([lon,lat]);ctx.fillText(label,p[0],p[1]);}}
 root.replaceChildren(canvas);
}
function drawMaps(){canvasMap('global-map');canvasMap('region-map',true);byId('global-count').textContent=fmt.format(d3.sum(state.data.cells.filter(c=>within(c[0])),c=>c[3]));byId('region-count').textContent=fmt.format(state.data.regional.filter(c=>within(c[0])).length);}
function timeline(area,id){
 const root=byId(id),metric=byId('metric').value,width=root.clientWidth||byId('timeline').clientWidth;
 const labels={events:'Gaps iniciados por mes',vessels:'Barcos distintos con gaps',medianHours:'Duración mediana (horas)'};
 const rows=state.data.monthly.filter(d=>d.area===area&&!d.partial).map(d=>({...d,date:new Date(d.month+'-01T00:00:00Z')}));
 const rules=[{date:new Date('2020-01-01T00:00:00Z'),label:'Fin del período original\n2017–2019',color:'#6d7a81'},{date:new Date('2023-12-10T00:00:00Z'),label:'Asunción de Milei\n10 dic. 2023',color:'#9b5b29'}];
 const plot=Plot.plot({width,height:335,marginLeft:55,marginTop:58,marginRight:25,title:area==='global'?'Global · escala propia':'Atlántico sudoccidental',style:{fontFamily:'Montserrat, system-ui',fontSize:'12px'},
 x:{type:'utc',label:null,ticks:width<600?'2 years':'1 year',tickFormat:'%Y',domain:[new Date('2017-01-01'),new Date('2026-09-01')]},
 y:{label:labels[metric],zero:true,grid:true},marks:[Plot.ruleY([0],{stroke:'#b4c3cc'}),
 ...rules.map(r=>Plot.ruleX([r.date],{stroke:r.color,strokeDasharray:'4,4'})),
 Plot.lineY(rows,{x:'date',y:metric,stroke:'#286b8b',strokeWidth:1.8}),
 Plot.dot(rows,{x:'date',y:metric,fill:'#286b8b',r:2.5,title:d=>`${d.month}: ${fmt.format(d[metric])}`}),
 ...rules.map(r=>Plot.text([r],{x:'date',text:'label',frameAnchor:'top',textAnchor:width<600?'middle':'start',dx:width<600?0:6,dy:-26,fontSize:width<600?9:11,fill:r.color,stroke:palette.paper,strokeWidth:3}))]});
 root.replaceChildren(plot);
}
function drawCharts(){timeline('region','timeline');if(byId('show-global').checked)timeline('global','global-timeline');}
function table(){const body=byId('monthly-table').querySelector('tbody');for(const r of state.data.monthly.filter(r=>r.area==='region'&&!r.partial)){const tr=document.createElement('tr');for(const value of [r.month,fmt.format(r.events),fmt.format(r.vessels),r.medianHours==null?'—':fmt.format(r.medianHours)]){const td=document.createElement('td');td.textContent=value;tr.append(td);}body.append(tr);}}
async function start(){try{const responses=await Promise.all([fetch('data/site-data.json'),fetch('vendor/countries-50m.json')]);if(responses.some(r=>!r.ok))throw new Error('No se pudieron cargar los datos');const[data,world]=await Promise.all(responses.map(r=>r.json()));state.data=data;state.land=topojson.feature(world,world.objects.land);await document.fonts.ready;drawMaps();drawCharts();table();
byId('period').addEventListener('change',e=>{const val=e.target.value;state.range=val==='all'?[2017,2026]:val.includes('-')?val.split('-').map(Number):[+val,+val];drawMaps();});
byId('metric').addEventListener('change',drawCharts);byId('show-global').addEventListener('change',e=>{byId('global-timeline').hidden=!e.target.checked;drawCharts();});
let timer;window.addEventListener('resize',()=>{clearTimeout(timer);timer=setTimeout(()=>{drawMaps();drawCharts();},150);});
}catch(error){byId('error').hidden=false;byId('error').textContent='No pudimos cargar las visualizaciones. Revisá tu conexión y recargá la página. Los archivos de datos siguen disponibles al pie.';console.error(error);}}
start();
