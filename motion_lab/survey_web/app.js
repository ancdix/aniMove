import * as THREE from './vendor/three.module.min.js';
const $=s=>document.querySelector(s);let index,ratings={},views=[],selection=0,playing=true,frame=0,clock=performance.now(),yaw=.72,pitch=.40,zoom=1,initialized=false;
const assetCache=new Map(),clipCache=new Map();
async function get(url){const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw Error(`${url}: ${r.status}`);return r.json()}
async function cached(cache,url){if(!cache.has(url))cache.set(url,get(url).catch(e=>{cache.delete(url);throw e}));return cache.get(url)}
async function post(url,data){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json','X-Motion-Lab':'review'},body:JSON.stringify(data)});const d=await r.json();if(!r.ok)throw Error(d.error||r.status);return d}
function option(value,text){const o=document.createElement('option');o.value=value;o.textContent=text;return o}
function makeView(seed){
 const card=document.createElement('article');card.className='card';card.innerHTML=`<h2><span>Seed ${seed}</span><span class="saved"></span></h2><div class="viewport"><div class="badge">Pending</div></div><div class="ratings"></div><div class="actions"><button class="blender">Open in Blender</button><small class="job"></small></div>`;$('#cards').append(card);
 const scene=new THREE.Scene();scene.background=new THREE.Color('#19252e');scene.add(new THREE.HemisphereLight(0xe4f0ff,0x475055,2.2));const light=new THREE.DirectionalLight(0xffffff,2.3);light.position.set(3,6,4);scene.add(light);
 const grid=new THREE.GridHelper(40,80,0x57717f,0x314753);scene.add(grid);
 const camera=new THREE.PerspectiveCamera(38,1,.01,1000);const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.7));renderer.outputColorSpace=THREE.SRGBColorSpace;const viewport=card.querySelector('.viewport');viewport.append(renderer.domElement);
 const view={card,seed,scene,camera,renderer,viewport,clip:null,entry:null,asset:null,mesh:null,line:null};
 new ResizeObserver(()=>{const w=viewport.clientWidth,h=viewport.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}).observe(viewport);
 let drag=null;renderer.domElement.onpointerdown=e=>{drag=[e.clientX,e.clientY];renderer.domElement.setPointerCapture(e.pointerId)};renderer.domElement.onpointermove=e=>{if(drag){yaw-=(e.clientX-drag[0])*.008;pitch=Math.max(-.1,Math.min(1.35,pitch+(e.clientY-drag[1])*.008));drag=[e.clientX,e.clientY]}};renderer.domElement.onpointerup=()=>drag=null;renderer.domElement.onwheel=e=>{e.preventDefault();zoom=Math.max(.35,Math.min(3.5,zoom*Math.exp(e.deltaY*.001)));};
 const controls=card.querySelector('.ratings');
 for(const [key,label,values] of [['action','Action match',[['','Unrated'],['clear','Clear'],['partial','Partial'],['miss','Miss']]],['plausibility','Physical plausibility',[['','Unrated'],['convincing','Convincing'],['cleanup','Needs cleanup'],['broken','Broken']]],['decision','Decision',[['','Unrated'],['keep','Keep'],['cleanup','Needs cleanup'],['reject','Reject']]]]){
  const l=document.createElement('label');l.textContent=label;const s=document.createElement('select');s.dataset.rating=key;for(const [v,t] of values)s.append(option(v,t));s.onchange=()=>saveRating(view);l.append(s);controls.append(l);
 }
 const notes=document.createElement('input');notes.className='notes';notes.placeholder='Notes — contact, sliding, balance, useful frames…';notes.maxLength=2000;notes.dataset.rating='notes';notes.onchange=()=>saveRating(view);controls.append(notes);
 card.querySelector('.blender').onclick=async()=>{try{await post('/api/blender',{entry:view.entry.id});$('#notice').textContent='Loaded in Blender.'}catch(e){$('#notice').textContent=e.message}};
 return view;
}
async function saveRating(v){if(!v.entry)return;const entryId=v.entry.id;const value=Object.fromEntries([...v.card.querySelectorAll('[data-rating]')].map(el=>[el.dataset.rating,el.value]));ratings[entryId]=value;try{await post('/api/ratings',{entry:entryId,rating:value});v.card.querySelector('.saved').textContent='Saved'}catch(e){v.card.querySelector('.saved').textContent='Save failed';$('#notice').textContent=e.message}}
function setAsset(v,a){
 if(v.mesh){v.scene.remove(v.mesh);v.mesh.geometry.dispose();v.mesh.material.dispose()};if(v.line){v.scene.remove(v.line);v.line.geometry.dispose();v.line.material.dispose()}
 v.asset=a;const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(new Float32Array(a.offsets.length),3));g.setAttribute('color',new THREE.Float32BufferAttribute(a.colors,3));g.setIndex(a.triangles);const m=new THREE.MeshStandardMaterial({vertexColors:true,roughness:.85,metalness:.12,flatShading:true,side:THREE.DoubleSide});v.mesh=new THREE.Mesh(g,m);v.mesh.frustumCulled=false;v.scene.add(v.mesh);
 const lg=new THREE.BufferGeometry();lg.setAttribute('position',new THREE.Float32BufferAttribute(new Float32Array((a.parents.length-1)*6),3));v.line=new THREE.LineSegments(lg,new THREE.LineBasicMaterial({color:0xffe59a,depthTest:false}));v.line.renderOrder=10;v.line.frustumCulled=false;v.scene.add(v.line);v.lastFrame=-1;
 const xs=a.rest.map(p=>p[0]),ys=a.rest.map(p=>p[1]),zs=a.rest.map(p=>p[2]);v.span=Math.max(1.7,Math.max(...xs)-Math.min(...xs),Math.max(...ys)-Math.min(...ys),Math.max(...zs)-Math.min(...zs));v.centerY=(Math.max(...ys)+Math.min(...ys))/2;
}
async function show(){
 const token=++selection,key=$('#target').value,pid=$('#prompt').value,p=index.prompts.find(p=>p.id===pid);$('#caption').textContent=p.text;$('#category').textContent=p.family+(p.intended_targets.includes(key)?' · intended anatomy':' · experimental cross-anatomy prompt');frame=0;clock=performance.now();
 const asset=await cached(assetCache,`/models/${key}.json`);if(token!==selection)return;
 for(const v of views){
  v.entry=index.entries.find(e=>e.target===key&&e.prompt_id===pid&&e.seed===v.seed);v.clip=null;setAsset(v,asset);const e=v.entry;v.card.querySelector('.badge').textContent=e.status==='complete'?'Raw · 2 seconds':e.status.replaceAll('_',' ');v.card.querySelector('.job').textContent=e.job||'';v.card.querySelector('.blender').disabled=e.status!=='complete';v.card.querySelector('.saved').textContent='';
  for(const el of v.card.querySelectorAll('[data-rating]')){el.value=(ratings[e.id]||{})[el.dataset.rating]||'';el.disabled=e.status!=='complete'}
  if(e.status==='complete')cached(clipCache,'/'+e.clip).then(c=>{if(token===selection){v.clip=c;v.lastFrame=-1}}).catch(e=>$('#notice').textContent=e.message);
 }
}
function animate(now){
 requestAnimationFrame(animate);if(playing)frame=Math.floor((now-clock)/1000*30)%60;$('#scrub').value=frame;$('#frame').textContent=`${frame+1} / 60`;
 for(const v of views){if(!v.asset)continue;const a=v.asset,x=v.clip?v.clip.positions[frame]:a.rest,q=v.clip?v.clip.quaternions[frame]:null;
  if(v.lastFrame!==frame){const arr=v.mesh.geometry.attributes.position.array;for(let i=0;i<a.joints.length;i++){const j=a.joints[i],k=i*3,ox=a.offsets[k],oy=a.offsets[k+1],oz=a.offsets[k+2];let rx=ox,ry=oy,rz=oz;if(q){const [w,u,t,z]=q[j];const tx=2*(t*oz-z*oy),ty=2*(z*ox-u*oz),tz=2*(u*oy-t*ox);rx+=w*tx+t*tz-z*ty;ry+=w*ty+z*tx-u*tz;rz+=w*tz+u*ty-t*tx}arr[k]=x[j][0]+rx;arr[k+1]=x[j][1]+ry;arr[k+2]=x[j][2]+rz}v.mesh.geometry.attributes.position.needsUpdate=true;v.mesh.geometry.computeVertexNormals();
   const lp=v.line.geometry.attributes.position.array;let k=0;for(let j=1;j<a.parents.length;j++)for(const p of [x[a.parents[j]],x[j]])for(const c of p)lp[k++]=c;v.line.geometry.attributes.position.needsUpdate=true;v.lastFrame=frame;
  }
  v.line.visible=$('#skeleton').checked;const follow=$('#follow').checked,center=new THREE.Vector3(follow?x[0][0]:a.rest[0][0],v.centerY,follow?x[0][2]:a.rest[0][2]);const dist=v.span*2.05*zoom;v.camera.position.set(center.x+Math.sin(yaw)*Math.cos(pitch)*dist,center.y+Math.sin(pitch)*dist,center.z+Math.cos(yaw)*Math.cos(pitch)*dist);v.camera.lookAt(center);v.renderer.render(v.scene,v.camera);
 }
}
async function refresh(){
 const next=await get('/api/index');const signature=d=>JSON.stringify(d?.entries.filter(e=>e.target===$('#target').value&&e.prompt_id===$('#prompt').value).map(e=>[e.id,e.status,e.job]));const changed=!index||signature(next)!==signature(index);index=next;const eta=index.eta_seconds==null?'':` · estimated ${Math.ceil(index.eta_seconds/60)} minutes remaining`;
 $('#progress').textContent=`${index.completed.toLocaleString()} / ${index.total.toLocaleString()} complete · ${index.failed} failed · ${index.status.replaceAll('_',' ')}${eta}`;
 if(index.error)$('#notice').textContent=index.error;
 if(!initialized){ratings=await get('/api/ratings');for(const t of index.targets)$('#target').append(option(t.id,t.title));for(const p of index.prompts)$('#prompt').append(option(p.id,p.id+' · '+p.text));views=index.seeds.map(makeView);initialized=true;await show()}else if(changed)await show();
}
$('#target').onchange=()=>show().catch(e=>$('#notice').textContent=e.message);$('#prompt').onchange=$('#target').onchange;
for(const [id,delta] of [['prev',-1],['next',1]])$('#'+id).onclick=()=>{const s=$('#prompt');s.selectedIndex=(s.selectedIndex+delta+s.options.length)%s.options.length;show()};
$('#play').onclick=()=>{playing=!playing;clock=performance.now()-frame/30*1000;$('#play').textContent=playing?'Pause':'Play'};$('#scrub').oninput=e=>{frame=+e.target.value;playing=false;$('#play').textContent='Play';clock=performance.now()-frame/30*1000};$('#reset').onclick=()=>{yaw=.72;pitch=.40;zoom=1};
$('#export').onclick=async()=>{const blob=new Blob([JSON.stringify(await get('/api/ratings'),null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='essential-motion-ratings.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};
refresh().then(()=>{requestAnimationFrame(animate);setInterval(()=>refresh().catch(e=>$('#notice').textContent=e.message),15000)}).catch(e=>$('#notice').textContent=e.message);
