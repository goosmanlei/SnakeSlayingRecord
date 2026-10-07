(function probe(initial) {
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
})(JSON.parse(new URL(location.href).searchParams.get('perf_case')||'null'));