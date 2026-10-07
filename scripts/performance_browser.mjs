/* Invoke through cua_repl with the connected Chrome tab and its CDP capability.
 * UI actions use the supported locator API. The injected probe only observes
 * trusted action events, DOM readiness, resource timing and two paint frames.
 */
import fs from 'node:fs/promises';
import crypto from 'node:crypto';

function probe(initial) {
  if(initial){localStorage.clear();sessionStorage.clear()}
  const p={armed:null,result:null,images:[],longTasks:[]};
  window.__productionPerformance=p;
  performance.setResourceTimingBufferSize(3000);
  document.addEventListener('load',e=>{if(e.target instanceof HTMLImageElement)p.images.push({src:e.target.currentSrc,at:performance.now(),width:e.target.naturalWidth})},true);
  try{new PerformanceObserver(list=>p.longTasks.push(...list.getEntries().map(e=>({start:e.startTime,duration:e.duration})))).observe({type:'longtask',buffered:true})}catch{}
  const visible=node=>!!node&&node.getClientRects().length>0;
  function ready(spec){
    const root=document.querySelector(spec.root);if(!visible(root))return false;
    if(document.querySelector('.breakdown-loading'))return false;
    if(spec.scene&&document.querySelector('.breakdown-body')?.dataset.sceneId!==spec.scene)return false;
    if(spec.shot&&!document.querySelector(`.breakdown-scene-list .active[data-object-id="${spec.shot}"]`))return false;
    if(spec.episode&&new URL(location.href).searchParams.get('breakdown_episode')!==spec.episode)return false;
    if(spec.text&&!root.textContent.includes(spec.text))return false;
    if(spec.absent&&root.textContent.includes(spec.absent))return false;
    if(spec.selector&&!document.querySelector(spec.selector))return false;
    if(spec.count!==undefined&&root.querySelectorAll(spec.cards||'.material-small-card').length!==spec.count)return false;
    if(spec.summary&&!document.querySelector('.production-filter-summary')?.textContent.includes(spec.summary))return false;
    if(spec.url){const params=new URL(location.href).searchParams;for(const [key,value] of Object.entries(spec.url))if((params.get(key)||'')!==value)return false}
    return true;
  }
  function finish(a){
    if(p.armed!==a||a.start===null||!ready(a.spec))return;
    requestAnimationFrame(()=>requestAnimationFrame(()=>{
      if(p.armed!==a||!ready(a.spec))return schedule(a);
      const root=document.querySelector(a.spec.root),end=performance.now();
      p.result={label:a.spec.label,time_origin:performance.timeOrigin,start:a.start,end,ms:end-a.start,url:location.href,
        text:root.innerText,controls:[...root.querySelectorAll('button,select,input,textarea')].map(n=>({tag:n.tagName,text:n.textContent,disabled:n.disabled,value:n.value,pressed:n.getAttribute('aria-pressed')})),
        images:p.images.filter(i=>i.at>=a.start),longTasks:p.longTasks.filter(i=>i.start>=a.start),
        resources:performance.getEntriesByType('resource').filter(e=>e.startTime>=a.start).map(e=>({url:e.name,start:e.startTime,end:e.responseEnd,duration:e.duration,transfer:e.transferSize,encoded:e.encodedBodySize,decoded:e.decodedBodySize,initiator:e.initiatorType})),
        viewport:[innerWidth,innerHeight],heap:performance.memory?{used:performance.memory.usedJSHeapSize,total:performance.memory.totalJSHeapSize}:null};
      p.armed=null;a.resolve(p.result);
    }));
  }
  function schedule(a){if(p.armed!==a)return;requestAnimationFrame(()=>{if(ready(a.spec)&&a.start!==null)finish(a);else schedule(a)})}
  p.arm=(spec,start=null)=>{
    p.result=null;p.images=[];p.longTasks=[];performance.clearResourceTimings();const a={spec,start};p.armed=a;p.done=new Promise(resolve=>a.resolve=resolve);schedule(a);return true;
  };
  for(const type of ['click','input','change'])document.addEventListener(type,e=>{const a=p.armed;if(a&&a.start===null&&e.isTrusted&&(!a.spec.action||e.target.closest(a.spec.action)))a.start=performance.now()},true);
  if(initial)p.arm(initial,0);
}

export const probeSource=`(${probe.toString()})(JSON.parse(new URL(location.href).searchParams.get('perf_case')||'null'));`;

function value(result){if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));return result.result?.value}
export function createRunner({tab,cdp,output,side,round,port,startIndex=0}){
  let index=startIndex;
  const base=`http://127.0.0.1:${port}`;
  const evaluate=async(expression,awaitPromise=false)=>value(await cdp.send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise},{timeoutMs:55000}));
  async function state(){
    try{return {text:await tab.getAXState({emit:false}),fallback:null}}
    catch(error){return {text:await tab.playwright.domSnapshot(),fallback:String(error)}}
  }
  async function install(initial=null){
    await cdp.send('Performance.enable');await cdp.send('Network.enable');
  }
  async function save(spec,id,before){
    let result;
    try{result=await evaluate('Promise.race([window.__productionPerformance.done,new Promise(resolve=>setTimeout(()=>resolve({failed:"readiness timeout (20 s)",url:location.href}),20000))])',true)}
    catch(error){result={failed:String(error)}}
    let networkError=null;try{await tab.playwright.waitForLoadState({state:'networkidle',timeoutMs:15000})}catch(error){networkError=String(error)}
    await evaluate(`Promise.race([Promise.all([...document.querySelectorAll(${JSON.stringify(spec.root+' img')})].filter(n=>{const r=n.getBoundingClientRect();return r.width&&r.height&&r.bottom>0&&r.top<innerHeight}).map(n=>n.decode().catch(()=>null))),new Promise(resolve=>setTimeout(resolve,10000))])`,true);
    const media=await evaluate(`(()=>{const p=window.__productionPerformance;return {at:performance.now(),images:p.images,resources:performance.getEntriesByType('resource').map(e=>({url:e.name,start:e.startTime,end:e.responseEnd,duration:e.duration,transfer:e.transferSize,encoded:e.encodedBodySize,initiator:e.initiatorType})),visible:[...document.querySelectorAll(${JSON.stringify(spec.root+' img')})].filter(n=>{const r=n.getBoundingClientRect();return r.width&&r.height&&r.bottom>0&&r.top<innerHeight}).map(n=>({src:n.currentSrc,complete:n.complete,width:n.naturalWidth}))}})()`);
    const after=await cdp.send('Performance.getMetrics');
    const observed=await state(),ax=observed.text;
    const text=result.text||'';delete result.text;
    const row={id,side,round,index:index++,condition:spec.condition||'repeat',path:spec.label,expected:spec,...result,
      content_sha256:crypto.createHash('sha256').update(JSON.stringify([text,result.controls])).digest('hex'),
      visible_text:text.slice(0,1200),media,networkError,observationFallback:observed.fallback,metrics_before:before,metrics_after:after,observed_at:new Date().toISOString()};
    await fs.appendFile(output,JSON.stringify(row)+'\n');
    if(row.failed){await evaluate('window.__productionPerformance.armed=null');throw Error(`${id}: ${row.failed}\n${String(ax).slice(0,1500)}`)}
    return {id,ms:row.ms,requests:row.resources.length,bytes:row.resources.reduce((n,r)=>n+r.encoded,0),content:row.content_sha256};
  }
  async function measure(spec,{url,selector,input,select}={}){
    const id=`${round}-${side}-${index}-${spec.label}-${spec.condition||'repeat'}`;
    let before=null;
    if(url){
      await install(spec);const target=base+url+(url.includes('?')?'&':'?')+'perf_case='+encodeURIComponent(JSON.stringify({...spec,id}));
      if(await tab.url()===target)await tab.reload();else await tab.goto(target);
    }else{
      await evaluate(`window.__productionPerformance.arm(${JSON.stringify({...spec,action:selector})})`);
      before=await cdp.send('Performance.getMetrics');
      if(input!==undefined){
        if(await tab.playwright.locator(selector).evaluate(n=>n.value))throw Error('Measured search must begin empty');
        await tab.playwright.locator(selector).pressSequentially(input);
      }
      else if(select!==undefined)await tab.playwright.locator(selector).selectOption(select);
      else await tab.playwright.locator(selector).click();
    }
    return save(spec,id,before);
  }
  async function navigate(url){await install();if(await tab.url()===base+url)await tab.reload();else await tab.goto(base+url);return state()}
  async function click(selector){await tab.playwright.locator(selector).click();return state()}
  async function recover(spec,id){return save(spec,id,null)}
  async function close(){await cdp.send('Performance.disable')}
  return {measure,navigate,click,evaluate,install,close,recover,base};
}

export function journeySteps(kind,iteration){
  const steps=[],add=(spec,action)=>steps.push({spec:{...spec,iteration},action});
  const E1='screenplay-04-lantern-home-e01',E2='screenplay-04-lantern-home-e02';
  const list=(name,condition='repeat')=>({label:name+'.load',condition,root:'.management-card-list',count:40,
    summary:name==='entities'?'133 个实体':'素材数 2073',text:name==='entities'?'阿禾':'三道滩',selector:'[aria-label="每页行数"]'});
  const close=()=>steps.push({click:'dialog[open] > .review-dialog-header .review-dialog-close'});
  const card=(name,selector,entity,condition,text='生成内容')=>{add({label:name,condition,root:'dialog.unified-card-dialog .unified-card',text,
    selector:'dialog[open] .entity-review-accept',url:['card.materials','card.shots'].includes(name)?{material_id:'need-form-a-heng-blue-overall',material_version:'1'}:{production_entity:entity}},{selector});close()};
  if(kind==='entities'){
    add(list(kind,'first'),{url:'/?workspace=settings.workspace&production_tab=entities'});
    for(const [size,id,text] of [['large','entity-li-ji','生成内容'],['small','entity-a-he','阿禾'],['medium','entity-a-heng','生成内容']])
      for(const condition of ['first','repeat'])card('card.entities.'+size,`.entity-small-card[data-object-id="${id}"]`,id,condition,text);
    add({...list('materials'),label:'_setup.materials',condition:'setup'},{selector:'#production-tab-materials'});
    add(list(kind),{selector:'#production-tab-entities'});
  }else if(kind==='breakdown'||kind==='shots'){
    const view=(label,scene,condition='repeat',extra={})=>({label,condition,root:'.breakdown-body',scene,
      text:kind==='shots'?'Prompt':'SH',selector:'.breakdown-scene-list .source-button',...extra});
    add(view(kind+'.load','preparation-s001','first'),{url:`/?workspace=${kind==='shots'?'production':'settings'}.workspace&production_tab=${kind}`});
    add(view(kind+'.shot','preparation-s001','first',{shot:'shot-e01-002'}),{selector:'.breakdown-scene-list [data-object-id="shot-e01-002"]'});
    add(view('_setup.shot','preparation-s001','setup',{shot:'shot-e01-001'}),{selector:'.breakdown-scene-list [data-object-id="shot-e01-001"]'});
    add(view(kind+'.shot','preparation-s001','repeat',{shot:'shot-e01-002'}),{selector:'.breakdown-scene-list [data-object-id="shot-e01-002"]'});
    add(view(kind+'.scene','preparation-s002','first'),{selector:'.breakdown-scene-list [data-object-id="preparation-s002"]'});
    add(view(kind+'.scene','preparation-s001'),{selector:'.breakdown-scene-list [data-object-id="preparation-s001"]'});
    add(view(kind+'.episode','preparation-s003','first',{episode:E2}),{selector:`.breakdown-episode-tabs [data-episode-id="${E2}"]`});
    add(view(kind+'.episode','preparation-s001','repeat',{episode:E1}),{selector:`.breakdown-episode-tabs [data-episode-id="${E1}"]`});
    for(const condition of ['first','repeat'])card('card.'+kind,`.breakdown-shot[data-shot-id="shot-e01-001"] [data-material-id="need-form-a-heng-blue-overall"]`,'entity-a-heng',condition);
    if(kind==='breakdown'){
      add({...list('materials'),label:'_setup.materials',condition:'setup'},{selector:'#production-tab-materials'});
      add(view(kind+'.load','preparation-s001'),{selector:'#production-tab-breakdown'});
    }else{
      steps.push({click:'#production-tab-history'});
      add(view(kind+'.load','preparation-s001'),{selector:'#production-tab-shots'});
    }
  }else if(kind==='materials'){
    add(list(kind,'first'),{url:'/?workspace=materials.workspace&production_tab=materials'});
    for(const condition of ['first','repeat'])card('card.materials','.management-card-list [data-material-id="need-form-a-heng-blue-overall"]','entity-a-heng',condition);
    add({label:'materials.page',condition:'first',root:'.management-card-list',url:{material_page:'2'},selector:'.review-pagination'},{selector:'.review-pagination button:nth-of-type(3)'});
    add({label:'materials.page',condition:'repeat',root:'.management-card-list',url:{material_page:'1'},selector:'.review-pagination'},{selector:'.review-pagination button:nth-of-type(1)'});
    for(const condition of ['first','repeat']){
      const f={};
      const filter=(name,key,value)=>{f['material_'+key]=value;if(key==='episode')f.material_scene='';add({label:'materials.filter.'+name,condition,root:'.management-card-list',url:{...f},selector:`[data-filter-key="${key}"][data-filter-value="${value}"][aria-pressed="true"]`},{selector:`[data-filter-key="${key}"][data-filter-value="${value}"]`})};
      filter('image','media','image');filter('audio','media','audio');filter('video','media','video');filter('all_media','media','');
      filter('episode','episode',E1);filter('scene','scene','s001');filter('scene_image','media','image');filter('ungenerated','status','ungenerated');filter('generated','status','generated');
      f.material_search='李寄';add({label:'materials.filter.combination',condition,root:'.management-card-list',count:1,summary:'素材数 1 ·',url:{...f}},{selector:'input[aria-label="搜索素材"]',input:'李寄'});
      add({...list(kind),label:'_setup.clear',condition:'setup',url:{material_search:'',material_episode:'',material_scene:'',material_media:'',material_status:''}},{selector:'.production-toolbar button'});
    }
    add({...list('entities'),label:'_setup.entities',condition:'setup'},{selector:'#production-tab-entities'});
    add(list(kind),{selector:'#production-tab-materials'});
  }else throw Error('Unknown journey');
  return steps;
}

export function createBatch(runner,{iterations=10,kinds=['entities','breakdown','materials','shots'],start=0}={}){
  const plan=kinds.flatMap(kind=>Array.from({length:iterations},(_,i)=>journeySteps(kind,i)).flat());let next=start;
  return {remaining:()=>plan.length-next,position:()=>({next,total:plan.length,step:plan[next]}),
    async run(count=5){const values=[],started=Date.now();while(next<plan.length&&values.length<count&&Date.now()-started<25000){const step=plan[next];
      if(step.click){await runner.click(step.click);values.push({setup:step.click})}
      else values.push(await runner.measure(step.spec,step.action));next++;}
      return {position:next,total:plan.length,values};}};
}
