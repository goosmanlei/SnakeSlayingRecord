/* Additional real-browser regression; use only independent write snapshot copies.
 * The main ABAB observation/endpoint is reused without modification.
 */
export const historicalRevision='404dbabd1fd78d8b937dae27c0631913806115213cf94747805053197fb3a0e5';
export const currentRevision='22283c0e6836ce7ae8e7256eed749e05f6212b2442db9f5fdeb653779584dd20';
export const historicalUrl='/?workspace=settings.workspace&production_tab=entities&entity_page=1&entity_rows=10&production_object=entity-a-he&production_entity=entity-a-he&entity_state=form-a-he-base&production_revision='+historicalRevision;
const oldText='第六集父亲回忆中被押走并回头叫父亲';
const newText='该画面没有阿禾台词';
function spec(label,revision,condition,iteration){
  return {label,condition,iteration,root:'dialog.unified-card-dialog .unified-card',text:revision===historicalRevision?oldText:newText,
    selector:'.entity-review-basics [data-production-blocks="'+revision+'"]'};
}
export function createSupplement({runner,tab,iterations=10,start=0,history=true}){
  let next=start;
  const plan=[];
  for(let iteration=0;history&&iteration<iterations;iteration++){
    plan.push({spec:spec('card.history.open',historicalRevision,'first',iteration),action:{url:historicalUrl}});
    plan.push({spec:spec('card.history.current',currentRevision,'repeat',iteration),action:{selector:'.entity-review-identity [data-choice-id="'+currentRevision+'"]'}});
    plan.push({spec:spec('card.history.select',historicalRevision,'repeat',iteration),action:{selector:'.entity-review-identity [data-choice-id="'+historicalRevision+'"]'}});
  }
  plan.push({setup:true});
  for(let iteration=0;iteration<iterations;iteration++)plan.push({comment:iteration});
  async function run(limit=20){
    const values=[],started=Date.now();
    while(next<plan.length&&values.length<limit&&Date.now()-started<25000){
      const step=plan[next];
      if(step.setup){
        await runner.click('.entity-review-identity [data-choice-id="'+currentRevision+'"]');
        await tab.playwright.locator('.entity-review-basics [data-production-blocks="'+currentRevision+'"]').waitFor({state:'visible'});
        values.push({setup:true});
      }else if(step.comment!==undefined){
        const body='性能回归隔离评论 '+String(step.comment+1).padStart(2,'0');
        await tab.playwright.getByRole('button',{name:'评论整图',exact:true}).click();
        const target=JSON.parse(await tab.playwright.locator('.comment-editor').getAttribute('data-draft-target'));
        if(target.target_object_id!=='asset-fg3-a-he-base-image-01'||target.target_revision_id!=='d71d936487d92793f28f793c7d6e0eca5051138762a7ee99ebb976959f793561')throw Error('comment target changed');
        await tab.playwright.locator('#comment-editor-text').fill(body);
        values.push(await runner.measure({label:'comments.save',condition:'repeat',iteration:step.comment,root:'#comment-panel',
          text:body,selector:'#comment-panel .comment-card',cards:'.comment-card',count:step.comment+1,target},
          {selector:'[data-comment-submit]'}));
        if(await tab.playwright.locator('#comment-editor-text').count())throw Error('saved comment draft was not cleared');
      }else{
        values.push(await runner.measure(step.spec,step.action));
        const enabled=await tab.playwright.locator('dialog[open] .entity-review-accept').isEnabled();
        if(step.spec.selector.includes(historicalRevision)&&enabled)throw Error('historical acceptance must remain disabled');
      }
      next++;
    }
    return {next,total:plan.length,values};
  }
  return {run,position:()=>({next,total:plan.length}),remaining:()=>plan.length-next};
}

export async function verifyLateComments({tab,cdp,base,first,second,expectedOpen}){
  const methods=['Fetch.requestPaused'];
  const pending=events=>{
    const items=events.events.filter(e=>e.params.request.method==='GET');
    if(items.length!==1)throw Error('Expected one controlled comment refresh');
    return items[0];
  };
  await cdp.send('Fetch.enable',{patterns:[{urlPattern:base+'/api/comments',resourceType:'Fetch',requestStage:'Response'}]});
  try{
    const cursor=await cdp.readEvents({methods});
    await tab.playwright.locator('#comment-panel .comment-card').filter({hasText:first}).getByRole('button',{name:'关闭评论',exact:true}).click();
    const oldEvents=await cdp.readEvents({afterSequence:cursor.cursor,methods,timeoutMs:1500}),old=pending(oldEvents);
    await tab.playwright.locator('#comment-panel .comment-card').filter({hasText:second}).getByRole('button',{name:'关闭评论',exact:true}).click();
    const latestEvents=await cdp.readEvents({afterSequence:oldEvents.cursor,methods,timeoutMs:1500}),latest=pending(latestEvents);
    await cdp.send('Fetch.continueResponse',{requestId:latest.params.requestId});
    await tab.playwright.getByRole('heading',{name:'未关闭评论 · '+expectedOpen,exact:true}).waitFor({state:'visible'});
    const fresh=await tab.playwright.locator('#comment-panel').innerText();
    await cdp.send('Fetch.continueResponse',{requestId:old.params.requestId});
    await tab.playwright.waitForLoadState({state:'networkidle'});
    const late=await tab.playwright.locator('#comment-panel').innerText();
    if(late!==fresh)throw Error('A delayed response replaced the newer comment list');
    return {old,latest,fresh,late};
  }finally{await cdp.send('Fetch.enable',{patterns:[]})}
}
