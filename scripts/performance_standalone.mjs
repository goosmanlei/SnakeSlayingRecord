/* Scoped real-browser comparison for a material without an owning entity. */
export function createStandaloneBatch(runner,{iterations=10}={}){
  const plan=[{spec:{label:'_setup.materials.audio',condition:'setup',root:'.management-card-list',
    text:'声音参考选段',summary:'素材数 368',url:{material_page:'2',material_media:'audio'}},
    action:{url:'/?workspace=materials.workspace&production_tab=materials&material_media=audio&material_page=2'}}];
  for(let i=-1;i<iterations;i++){
    plan.push({spec:{label:'card.materials.standalone',condition:i<0?'setup':'repeat',iteration:i,
      root:'dialog[open] .unified-card',text:'本镜准确声音选段方案',
      selector:'dialog[open] [role="group"][aria-label="素材版本"]',
      url:{production_object:'need-shot-e01-021-sound-reference',material_version:'1'}},
      action:{selector:'.management-card-list [data-material-id="need-shot-e01-021-sound-reference"]'}});
    plan.push({click:'dialog[open] > .review-dialog-header .review-dialog-close'});
  }
  let next=0;
  return {position:()=>({next,total:plan.length}),async run(limit=30){
    const values=[],start=Date.now();
    while(next<plan.length&&values.length<limit&&Date.now()-start<25000){
      const step=plan[next];
      values.push(step.click?await runner.click(step.click):await runner.measure(step.spec,step.action));next++;
    }
    return {next,total:plan.length,values:values.filter(v=>v.id)};
  }};
}
