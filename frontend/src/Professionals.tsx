import { FormEvent, useState } from 'react';
import type { Professional, ProfessionalInput, ProfessionalUpdate } from './types';

export function Professionals({items,onCreate,onUpdate}:{items:Professional[];onCreate:(input:ProfessionalInput)=>Promise<void>;onUpdate:(id:string,input:ProfessionalUpdate)=>Promise<void>}){
  const [busy,setBusy]=useState(false);
  const [editing,setEditing]=useState<Professional|null>(null);
  async function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();setBusy(true);const form=event.currentTarget;const data=new FormData(form);
    try{await onCreate({display_name:String(data.get('display_name')).trim(),specialty:String(data.get('specialty')).trim()});form.reset();}finally{setBusy(false);}
  }
  async function toggle(item:Professional){setBusy(true);try{await onUpdate(item.id,{active:!item.active});}finally{setBusy(false);}}
  async function saveEdit(event:FormEvent<HTMLFormElement>){event.preventDefault();if(!editing)return;setBusy(true);const data=new FormData(event.currentTarget);try{await onUpdate(editing.id,{display_name:String(data.get('display_name')).trim(),specialty:String(data.get('specialty')).trim()});setEditing(null);}finally{setBusy(false);}}
  return <section aria-labelledby="professionals-title"><div className="section-heading"><div><p className="eyebrow">Equipo clínico</p><h1 id="professionals-title">Profesionales</h1></div><span>{items.filter((item)=>item.active).length} activos</span></div>
    <form className="card form-grid" onSubmit={submit}><h2>Agregar odontólogo</h2><label>Nombre para mostrar<input name="display_name" placeholder="Dra. Nombre Apellido" minLength={2} maxLength={160} required/></label><label>Especialidad<input name="specialty" placeholder="Odontología general" minLength={2} maxLength={120} required/></label><button disabled={busy}>{busy?'Guardando…':'Guardar profesional'}</button></form>
    {editing&&<form className="card form-grid" onSubmit={saveEdit}><h2>Editar profesional</h2><label>Nombre para mostrar<input name="display_name" defaultValue={editing.display_name} minLength={2} maxLength={160} required/></label><label>Especialidad<input name="specialty" defaultValue={editing.specialty} minLength={2} maxLength={120} required/></label><button disabled={busy}>Guardar cambios</button><button type="button" className="button-secondary" onClick={()=>setEditing(null)}>Cancelar</button></form>}
    <div className="card table-wrap"><table><caption>Equipo profesional</caption><thead><tr><th scope="col">Profesional</th><th scope="col">Especialidad</th><th scope="col">Estado</th><th scope="col">Acciones</th></tr></thead><tbody>{items.length?items.map((item)=><tr key={item.id}><th scope="row">{item.display_name}</th><td>{item.specialty}</td><td><span className={`status ${item.active?'status--active':'status--inactive'}`}>{item.active?'Activo':'Inactivo'}</span></td><td><div className="table-actions"><button type="button" className="button-secondary" disabled={busy} onClick={()=>setEditing(item)}>Editar</button><button type="button" className="button-secondary" disabled={busy} onClick={()=>toggle(item)}>{item.active?'Desactivar':'Reactivar'}</button></div></td></tr>):<tr><td colSpan={4}>Todavía no hay profesionales.</td></tr>}</tbody></table></div>
  </section>;
}
