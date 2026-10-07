/* Repeat affected first-document and comment paths after the comment-order fix.
 * All fixtures and primary endpoint definitions come from the frozen harness.
 */
import {journeySteps} from './performance_browser.mjs';
import {createSupplement} from './performance_supplement.mjs';
export function createImpactBatch({runner,tab,iterations=10}){
  const plan=['entities','breakdown','materials','shots'].flatMap(kind=>
    Array.from({length:iterations},(_,i)=>journeySteps(kind,i)[0]));
  const entity=journeySteps('entities',0)[0];
  plan.push({spec:{...entity.spec,label:'_setup.entities',condition:'setup'},action:entity.action});
  plan.push({spec:{label:'_setup.card',condition:'setup',root:'dialog.unified-card-dialog .unified-card',
    text:'阿禾',selector:'.entity-review-accept'},action:{selector:'.entity-small-card[data-object-id="entity-a-he"]'}});
  const comments=createSupplement({runner,tab,iterations,history:false});let next=0;
  const position=()=>({next:next+comments.position().next,total:plan.length+comments.position().total});
  return {position,remaining:()=>position().total-position().next,async run(limit=80){
    const values=[],started=Date.now();
    while(next<plan.length&&values.length<limit&&Date.now()-started<25000){
      values.push(await runner.measure(plan[next].spec,plan[next].action));next++;
    }
    if(next===plan.length&&values.length<limit&&Date.now()-started<25000){
      const result=await comments.run(limit-values.length);values.push(...result.values);
    }
    return {...position(),values};
  }};
}
