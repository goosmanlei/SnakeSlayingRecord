/* Bounded Node replay of the exact browser grouping and worker algorithm.
 * Browser interaction, painting and decoder evidence are measured separately.
 * Usage: node frontend_probe.cjs DESK_DIR EVIDENCE_DIR
 */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {Worker}=require('node:worker_threads'),{execFileSync}=require('node:child_process');
const {performance}=require('node:perf_hooks');
const [desk,evidence]=process.argv.slice(2);
const graph=JSON.parse(fs.readFileSync(path.join(evidence,'graph-current.json')));
const materials=JSON.parse(fs.readFileSync(path.join(evidence,'material-current.json')));
const read=(version,file)=>version==='before'?execFileSync('git',['show','254d509cbe644f75e90344bc1ae40b7279aa418f:'+file],{cwd:desk,encoding:'utf8'}):fs.readFileSync(path.join(desk,file),'utf8');
const report={node:process.version,boundary:'Node VM executes exact before/current grouping; Node worker executes unchanged bundled Graphviz/routing. Worker CPU is threadCpuUsage when supported, otherwise null. This is not browser paint or browser Worker CPU.',groups:[],graphs:[]};
function context(version,workerClass){
  const c={URL,AbortController,DOMException,setTimeout,clearTimeout,reviewURL:x=>x,businessCode:r=>r.business_code||r.object_id,Worker:workerClass,
    document:{addEventListener(){}},window:{addEventListener(){}}};
  vm.createContext(c);
  for(const file of ['review_desk/static/review-ui.js','review_desk/static/entity-relations.js','review_desk/static/management-cards.js'])vm.runInContext(read(version,file),c);
  return c;
}
function median(values){const x=[...values].sort((a,b)=>a-b);return (x[(x.length-1)>>1]+x[x.length>>1])/2;}
function time(fn){const start=performance.now(),cpu=process.cpuUsage();const value=fn();const used=process.cpuUsage(cpu);return {value,wall_ms:performance.now()-start,cpu_ms:(used.user+used.system)/1000};}
function expanded(value,factor){return {...value,items:Array.from({length:factor},(_,i)=>value.items.map(item=>({...item,canonical_material_id:item.canonical_material_id+'-probe-'+i,object_id:item.object_id+'-probe-'+i}))).flat()};}
async function run(){
 for(const version of ['before','after']){
  const c=context(version);
  for(const factor of [1,10]){
   const value=factor===1?materials:expanded(materials,factor);
   const first=time(()=>c.managementMaterialGroups(value));
   const samples=Array.from({length:20},()=>{const r=time(()=>c.managementMaterialGroups(value));return {wall_ms:r.wall_ms,cpu_ms:r.cpu_ms};});
   report.groups.push({version,factor,input_items:value.items.length,unique_items:first.value.reduce((n,g)=>n+g.items.length,0),first_ms:first.wall_ms,first_cpu_ms:first.cpu_ms,
      repeat_median_ms:median(samples.map(s=>s.wall_ms)),samples});
  }
  const workers=[],jobs=[];
  class Adapter {
   constructor(){
    const code=`const {parentPort}=require('node:worker_threads');const {performance}=require('node:perf_hooks');const viz=require(${JSON.stringify(path.join(desk,'review_desk/static/vendor/viz-3.31.0.js'))}).instance();const routing=require(${JSON.stringify(path.join(desk,'review_desk/static/entity-graph-routing.js'))});parentPort.on('message',async ({id,nodes,edges})=>{try{const renderer=await viz,start=performance.now(),cpu=process.threadCpuUsage?.();const geometry=routing.layout(renderer,nodes,edges);const used=cpu&&process.threadCpuUsage(cpu);parentPort.postMessage({id,geometry,measurement:{wall_ms:performance.now()-start,cpu_ms:used?(used.user+used.system)/1000:null}})}catch(e){parentPort.postMessage({id,error:e.message})}});`;
    this.worker=new Worker(code,{eval:true});workers.push(this.worker);
    this.worker.on('message',data=>{if(data.measurement)jobs.push(data.measurement);this.onmessage?.({data})});this.worker.on('error',e=>this.onerror?.(e));
   }
   postMessage(value){this.worker.postMessage(value)}
   terminate(){return this.worker.terminate()}
  }
  const g=context(version,Adapter),edges=graph.entity_graph.edges, nodes=g.managementGraphLayout(graph.records,edges).map(n=>({...n,h:110}));
  try{
   const start=performance.now();const results=await Promise.all([g.managementEdgeGeometry(nodes,edges),g.managementEdgeGeometry(nodes,edges)]);
   const cold=performance.now()-start;const count=jobs.length;const startHit=performance.now();
   for(let i=0;i<20;i++)await g.managementEdgeGeometry(nodes,edges);
   report.graphs.push({version,nodes:nodes.length,edges:edges.length,simultaneous_identical_requests:2,worker_jobs:count,worker_measurements:jobs,cold_two_requests_wall_ms:cold,twenty_cache_hits_wall_ms:performance.now()-startHit,cache_hit_jobs:jobs.length-count,complete_outputs:results.every(r=>r.nodes.length===nodes.length&&r.views.length===edges.length)});
  }finally{await Promise.all(workers.map(w=>w.terminate()));}
 }
 fs.writeFileSync(path.join(evidence,'frontend-replay.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report));
}
run().catch(e=>{console.error(e);process.exitCode=1});
