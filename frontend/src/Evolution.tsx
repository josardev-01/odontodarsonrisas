import { FormEvent, useEffect, useState } from 'react';
import { api, ApiError } from './api';
import type { EvolutionEntry, OdontogramWorkItem, ToothSurface, TreatmentPlan } from './types';

const legacySteps:Record<string,string>={preparation:'Preparación',procedure:'Procedimiento',final_control:'Control final'};
const legacyAnswers:Record<string,string>={yes:'Sí',no:'No',observation:'Observación'};
const surfaceLabels:Record<ToothSurface,string>={whole:'Pieza completa',mesial:'Mesial',distal:'Distal',buccal:'Vestibular',lingual:'Lingual/palatina',occlusal:'Oclusal',incisal:'Incisal'};

function ControlForm({busy,onSubmit}:{busy:boolean;onSubmit:(completed:boolean,notes:string|null)=>Promise<boolean>}){
  const [completed,setCompleted]=useState(false);
  async function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();
    const form=event.currentTarget;const data=new FormData(form);
    if(await onSubmit(completed,completed?null:String(data.get('notes')??'').trim()||null)){
      form.reset();setCompleted(false);
    }
  }
  return <form className="evolution-form" onSubmit={(event)=>void submit(event)}>
    <h4>Nuevo registro de evolución</h4>
    <label className="evolution-control"><input type="checkbox" name="control_completed" checked={completed} onChange={(event)=>setCompleted(event.target.checked)}/>Control realizado — finalizar tratamiento</label>
    {!completed&&<label>Notas de sesión<textarea name="notes" maxLength={4000} required placeholder="Registrá el avance de esta sesión"/></label>}
    <button disabled={busy}>{completed?'Guardar y finalizar tratamiento':'Guardar notas de sesión'}</button>
  </form>;
}

export function Evolution({patientId}:{patientId:string}){
  const [workItems,setWorkItems]=useState<OdontogramWorkItem[]>([]);
  const [plans,setPlans]=useState<TreatmentPlan[]>([]);
  const [entries,setEntries]=useState<EvolutionEntry[]>([]);
  const [error,setError]=useState('');const [busy,setBusy]=useState(false);
  const load=()=>Promise.all([api.odontogramWorkItems(patientId),api.treatmentPlans(patientId),api.evolutionEntries(patientId)]).then(([work,planList,entryList])=>{setWorkItems(work);setPlans(planList);setEntries(entryList);}).catch((reason)=>setError(reason instanceof ApiError?reason.message:'No fue posible cargar la evolución.'));
  useEffect(()=>{void load();},[patientId]);
  async function record(workId:string,completed:boolean,notes:string|null):Promise<boolean>{setBusy(true);setError('');try{await api.recordEvolution(patientId,workId,completed,notes);await load();return true;}catch(reason){setError(reason instanceof ApiError?reason.message:'No fue posible guardar la evolución.');return false;}finally{setBusy(false);}}
  const planned=workItems.filter((work)=>work.current_plan_id);
  return <section className="card" aria-labelledby="evolution-title"><h2 id="evolution-title">Registro de evolución</h2><p>Dejá «Control realizado» sin marcar para guardar notas de una sesión en curso. Marcá el control cuando el tratamiento haya finalizado.</p>{error&&<div className="notice notice--error" role="alert">{error}</div>}
    {planned.length?planned.map((work)=>{
      const plan=plans.find((item)=>item.id===work.current_plan_id);
      const history=entries.filter((entry)=>entry.work_item_id===work.id);
      const canRecord=!work.completed_at&&(plan?.status==='accepted'||plan?.status==='in_progress');
      return <article className="clinical-entry" key={work.id}><h3>Pieza {work.tooth_code} · {surfaceLabels[work.surface]} · {work.treatment_name}</h3><p><strong>Presupuesto:</strong> {plan?.title??'No disponible'} · <strong>Estado:</strong> {work.completed_at?'Finalizado':'Activo'}</p>
        {canRecord&&<ControlForm key={`${work.id}-${history.length}`} busy={busy} onSubmit={(completed,notes)=>record(work.id,completed,notes)}/>}
        {!work.completed_at&&!canRecord&&<p>El presupuesto debe estar aceptado para registrar la evolución.</p>}
        {history.length>0&&<details><summary>Registros anteriores ({history.length})</summary>{history.map((entry)=><div className="evolution-history" key={entry.id}><time dateTime={entry.created_at}>{new Intl.DateTimeFormat('es-PY',{dateStyle:'medium',timeStyle:'short'}).format(new Date(entry.created_at))}</time><p>{entry.control_completed===true?'Control realizado · tratamiento finalizado':entry.control_completed===false?'Sesión en curso':'Registro anterior'}</p>{entry.answers.length>0&&<ul>{entry.answers.map((answer)=><li key={answer.step}>{legacySteps[answer.step]}: {legacyAnswers[answer.response]}{answer.observation?` · ${answer.observation}`:''}</li>)}</ul>}{entry.notes&&<p>{entry.notes}</p>}</div>)}</details>}
      </article>;
    }):<p>Los procedimientos aparecerán aquí cuando se carguen en un presupuesto desde el odontograma.</p>}
  </section>;
}
