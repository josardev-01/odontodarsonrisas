import { FormEvent, useEffect, useState } from 'react';
import { api, ApiError } from './api';
import type { DentalCondition, EvolutionAnswer, EvolutionEntry, EvolutionResponse, EvolutionStep, OdontogramWorkItem, ToothSurface, TreatmentPlan } from './types';

const steps:{id:EvolutionStep;label:string}[]=[
  {id:'preparation',label:'Preparación realizada'},
  {id:'procedure',label:'Procedimiento realizado'},
  {id:'final_control',label:'Control final realizado'},
];
const answerLabels:Record<EvolutionResponse,string>={yes:'Sí',no:'No',observation:'Observación'};
const surfaceLabels:Record<ToothSurface,string>={whole:'Pieza completa',mesial:'Mesial',distal:'Distal',buccal:'Vestibular',lingual:'Lingual/palatina',occlusal:'Oclusal',incisal:'Incisal'};
const resultConditions:{value:DentalCondition;label:string}[]=[
  {value:'healthy',label:'Sano'}, {value:'restoration',label:'Restauración'},
  {value:'crown',label:'Corona'}, {value:'implant',label:'Implante'},
  {value:'root_canal',label:'Endodoncia'}, {value:'missing',label:'Ausente'},
  {value:'caries',label:'Caries'}, {value:'extraction_indicated',label:'Extracción indicada'},
];

function ChecklistForm({busy,onSubmit}:{busy:boolean;onSubmit:(answers:EvolutionAnswer[],notes:string|null)=>Promise<boolean>}){
  const [choices,setChoices]=useState<Partial<Record<EvolutionStep,EvolutionResponse>>>({});
  async function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();
    const form=event.currentTarget;const data=new FormData(form);
    const answers=steps.map(({id})=>({step:id,response:String(data.get(id)) as EvolutionResponse,observation:String(data.get(`${id}_observation`)??'').trim()||null}));
    if(await onSubmit(answers,String(data.get('notes')??'').trim()||null)){
      form.reset();setChoices({});
    }
  }
  return <form className="evolution-form" onSubmit={(event)=>void submit(event)}>
    <h4>Nuevo registro de evolución</h4>
    {steps.map(({id,label})=><fieldset className="checklist-row" key={id}><legend>{label}</legend><div className="checklist-options">{(['yes','no','observation'] as EvolutionResponse[]).map((response)=><label key={response}><input type="radio" name={id} value={response} checked={choices[id]===response} onChange={()=>setChoices((previous)=>({...previous,[id]:response}))} required/>{answerLabels[response]}</label>)}</div>{choices[id]==='observation'&&<label>Detalle de la observación<input name={`${id}_observation`} maxLength={1000} required/></label>}</fieldset>)}
    <label>Notas de la sesión (opcional)<textarea name="notes" maxLength={4000}/></label>
    <button disabled={busy}>Guardar evolución</button>
  </form>;
}

export function Evolution({patientId}:{patientId:string}){
  const [workItems,setWorkItems]=useState<OdontogramWorkItem[]>([]);
  const [plans,setPlans]=useState<TreatmentPlan[]>([]);
  const [entries,setEntries]=useState<EvolutionEntry[]>([]);
  const [error,setError]=useState('');const [busy,setBusy]=useState(false);
  const load=()=>Promise.all([api.odontogramWorkItems(patientId),api.treatmentPlans(patientId),api.evolutionEntries(patientId)]).then(([work,planList,entryList])=>{setWorkItems(work);setPlans(planList);setEntries(entryList);}).catch((reason)=>setError(reason instanceof ApiError?reason.message:'No fue posible cargar la evolución.'));
  useEffect(()=>{void load();},[patientId]);
  async function record(workId:string,answers:EvolutionAnswer[],notes:string|null):Promise<boolean>{setBusy(true);setError('');try{await api.recordEvolution(patientId,workId,answers,notes);await load();return true;}catch(reason){setError(reason instanceof ApiError?reason.message:'No fue posible guardar la evolución.');return false;}finally{setBusy(false);}}
  async function complete(event:FormEvent<HTMLFormElement>,workId:string){event.preventDefault();setBusy(true);setError('');const data=new FormData(event.currentTarget);try{await api.completeProcedure(patientId,workId,String(data.get('result_condition')) as DentalCondition,String(data.get('result_note')??'').trim()||null);await load();}catch(reason){setError(reason instanceof ApiError?reason.message:'No fue posible finalizar el procedimiento.');}finally{setBusy(false);}}
  const planned=workItems.filter((work)=>work.current_plan_id);
  return <section className="card" aria-labelledby="evolution-title"><h2 id="evolution-title">Registro de evolución</h2><p>Registrá el avance por procedimiento. «Observación» permite describir una situación que no corresponde a Sí o No. El trabajo permanece activo hasta finalizarlo.</p>{error&&<div className="notice notice--error" role="alert">{error}</div>}
    {planned.length?planned.map((work)=>{
      const plan=plans.find((item)=>item.id===work.current_plan_id);
      const history=entries.filter((entry)=>entry.work_item_id===work.id);
      const latest=history[0];const canRecord=!work.completed_at&&(plan?.status==='accepted'||plan?.status==='in_progress');
      const canComplete=canRecord&&latest?.answers.every((answer)=>answer.response==='yes');
      return <article className="clinical-entry" key={work.id}><h3>Pieza {work.tooth_code} · {surfaceLabels[work.surface]} · {work.treatment_name}</h3><p><strong>Presupuesto:</strong> {plan?.title??'No disponible'} · <strong>Estado:</strong> {work.completed_at?'Finalizado':'Activo'}</p>
        {canRecord&&<ChecklistForm key={`${work.id}-${history.length}`} busy={busy} onSubmit={(answers,notes)=>record(work.id,answers,notes)}/>}
        {canComplete&&<form className="form-grid" onSubmit={(event)=>void complete(event,work.id)}><h4>Finalizar procedimiento</h4><label>Estado final en el odontograma<select name="result_condition" defaultValue="" required><option value="" disabled>Seleccione el resultado</option>{resultConditions.map((option)=><option key={option.value} value={option.value}>{option.label}</option>)}</select></label><label>Nota del resultado<textarea name="result_note" maxLength={2000}/></label><button disabled={busy}>Finalizar procedimiento y actualizar odontograma</button></form>}
        {!work.completed_at&&!canRecord&&<p>El presupuesto debe estar aceptado para registrar la evolución.</p>}
        {history.length>0&&<details><summary>Registros anteriores ({history.length})</summary>{history.map((entry)=><div className="evolution-history" key={entry.id}><time dateTime={entry.created_at}>{new Intl.DateTimeFormat('es-PY',{dateStyle:'medium',timeStyle:'short'}).format(new Date(entry.created_at))}</time><ul>{entry.answers.map((answer)=><li key={answer.step}>{steps.find((step)=>step.id===answer.step)?.label}: {answerLabels[answer.response]}{answer.observation?` · ${answer.observation}`:''}</li>)}</ul>{entry.notes&&<p>{entry.notes}</p>}</div>)}</details>}
      </article>;
    }):<p>Los procedimientos aparecerán aquí cuando se carguen en un presupuesto desde el odontograma.</p>}
  </section>;
}
