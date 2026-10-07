/* Browser-only regression and paired measurements for the final navigation fix.
 * Actions use the connected Chrome tab. CDP holds only known app fetch responses.
 */
import {journeySteps} from './performance_browser.mjs';
export function createNavigationBatch(runner,{iterations=10}={}){
  const plan=[];
  for(const kind of ['entities','breakdown','materials','shots'])for(let i=0;i<iterations;i++){
    const steps=journeySteps(kind,i);
    plan.push(steps[0]);
    if(kind==='breakdown'||kind==='shots')plan.push(...steps.filter(step=>step.spec?.label===kind+'.episode'));
  }
  let next=0;
  return {position:()=>({next,total:plan.length}),async run(limit=40){
    const values=[],start=Date.now();
    while(next<plan.length&&values.length<limit&&Date.now()-start<25000){
      const step=plan[next];values.push(await runner.measure(step.spec,step.action));next++;
    }
    return {next,total:plan.length,values};
  }};
}
export async function verifyRapidNavigation({tab,cdp,base,kind}){
  const E1='screenplay-04-lantern-home-e01',E2='screenplay-04-lantern-home-e02';
  const route=`/?workspace=${kind==='shots'?'production':'settings'}.workspace&production_tab=${kind}`;
  await tab.goto(base+route);
  await tab.playwright.locator('.breakdown-body[data-scene-id="preparation-s001"]').waitFor({state:'visible'});
  await tab.playwright.locator('.breakdown-loading').waitFor({state:'hidden'});
  const results=[];
  for(const mode of ['episode','scene']){
    const pattern=base+(mode==='episode'?'/api/production/breakdown?episode='+E2+'*':'/api/production/scene?object_id=preparation-s002*');
    await cdp.send('Fetch.enable',{patterns:[{urlPattern:pattern,resourceType:'Fetch',requestStage:'Response'}]});
    try{
      const methods=['Fetch.requestPaused'],cursor=await cdp.readEvents({methods});
      const selector=id=>mode==='episode'?`.breakdown-episode-tabs [data-episode-id="${id}"]`:`.breakdown-scene-list [data-object-id="${id}"]`;
      await tab.playwright.locator(selector(mode==='episode'?E2:'preparation-s002')).click();
      const paused=await cdp.readEvents({methods,afterSequence:cursor.cursor,timeoutMs:1500});
      if(paused.events.length!==1)throw Error('Expected one delayed '+mode+' response');
      await tab.playwright.locator(selector(mode==='episode'?E1:'preparation-s001')).click();
      const requested=await tab.url();
      if(new URL(requested).searchParams.get('breakdown_episode')!==E1)throw Error('Last episode click ignored');
      await cdp.send('Fetch.continueResponse',{requestId:paused.events[0].params.requestId});
      await tab.playwright.locator('.breakdown-loading').waitFor({state:'hidden'});
      const result=await tab.playwright.evaluate(()=>({url:location.href,scene:document.querySelector('.breakdown-body')?.dataset.sceneId,loading:!!document.querySelector('.breakdown-loading')}));
      if(result.scene!=='preparation-s001'||new URL(result.url).searchParams.get('breakdown_episode')!==E1)throw Error('Late response replaced last navigation');
      results.push({mode,requested,paused:paused.events[0],result});
    }finally{await cdp.send('Fetch.enable',{patterns:[]})}
  }
  return {kind,results,dom:await tab.playwright.domSnapshot()};
}
