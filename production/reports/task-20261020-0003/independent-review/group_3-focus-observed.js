let productionFocusState=null;
function productionFocusContext(row){return [row.id,state.workspace,state.productionEntityId,state.productionChildDetail?.record?.id,state.unifiedCardRoot,state.entityReview,state.materialReview,state.reviewWork,state.materialCommentCard?.material_id,state.materialCommentCard?.number,state.reviewReferenceContext,state.reviewCommentScope,state.anchor,state.editing,state.selected,location.href]}
function focusProductionReview(detail,paint=true){
  const r=detail.record;
  const context=productionFocusContext(r);
  if(state.productionSelected?.id===r.id&&productionFocusState?.every((value,index)=>value===context[index])){state.productionDetail=detail;return}
  if(state.productionSelected?.id!==r.id){if(typeof rememberProductionDraft==='function')rememberProductionDraft();state.reviewCommentScope=null;state.anchor=null;state.editing=null;state.selected=null;state.drawMode=null}
  state.productionSelected=r;state.productionDetail=detail;
  const url=new URL(location.href);url.searchParams.set('production_object',r.object_id);url.searchParams.set('production_revision',r.id);
  if(typeof isEntityReview==='function'&&isEntityReview()){
    if(!['ASSET','REQUIREMENT','CALL'].includes(r.kind)&&r.id===r.current_revision&&!state.entityReview.historical&&!state.entityReview.historicalTarget)url.searchParams.delete('production_revision');
    const context=['ASSET','REQUIREMENT','CALL'].includes(r.kind)?materialCommentContext():null;
    if(context){const round=state.entityReview.material_cards?.[context.material_id]?.find(r=>r.number===context.number);writeMaterialRoute(url.searchParams,context.material_id,round||context);url.searchParams.set('material_target',r.kind==='REQUIREMENT'&&r.current_content?'current':context.candidateTarget||r.id);if(context.candidateTarget){const candidate=round?.results.find(row=>row.id===context.candidateTarget);if(candidate){url.searchParams.set('production_object',candidate.object_id);url.searchParams.set('production_revision',candidate.id)}}}
    else{for(const key of ['material_id','material_round','material_version','material_baseline','material_target'])url.searchParams.delete(key)}
  }
  if((state.workspace==='settings.workspace'||state.unifiedCardRoot&&state.entityReview)&&state.productionEntityId){url.searchParams.set('production_entity',state.productionEntityId);if(state.productionChildDetail?.record)url.searchParams.set('entity_state',state.productionChildDetail.record.object_id);}else url.searchParams.delete('production_entity');
  if(typeof isMaterialReview==='function'&&isMaterialReview()){const context=materialCommentContext();url.searchParams.set('production_object',state.materialReview.record.object_id);url.searchParams.set('production_revision',state.materialReview.record.id);url.searchParams.set('material_target',context?.candidateTarget||r.id)}
  if(url.href!==location.href)history.replaceState(history.state,'',url);
  for(const blocks of document.querySelectorAll('[data-production-blocks]')){if(blocks.dataset.productionBlocks===r.id)blocks.id='production-blocks';else{blocks.removeAttribute('id');for(const para of blocks.querySelectorAll('.comment-flash'))para.classList.remove('comment-flash')}}
  if(typeof restoreProductionDraft==='function')restoreProductionDraft();
  productionFocusState=productionFocusContext(r);
  if(paint){paintProductionReview();renderComments()}
}