import { FormEvent, useEffect, useState } from 'react';
import { api, ApiError } from './api';
import type { AuthenticatedUser, Treatment } from './types';

export function TreatmentCatalog({user}:{user:AuthenticatedUser}){
  const [items,setItems]=useState<Treatment[]>([]);const [error,setError]=useState('');const [busy,setBusy]=useState(false);const isAdmin=user.roles.includes('admin');
  useEffect(()=>{api.treatments().then(setItems).catch((reason)=>setError(reason instanceof ApiError?reason.message:'No fue posible cargar tratamientos.'));},[]);
  async function submit(event:FormEvent<HTMLFormElement>){event.preventDefault();setBusy(true);setError('');const form=event.currentTarget;const data=new FormData(form);try{const created=await api.createTreatment({code:String(data.get('code')).trim(),name:String(data.get('name')).trim(),category:String(data.get('category')).trim(),default_price:String(data.get('default_price'))});setItems((current)=>[...current,created].sort((a,b)=>a.name.localeCompare(b.name)));form.reset();}catch(reason){setError(reason instanceof ApiError?reason.message:'No fue posible crear el tratamiento.');}finally{setBusy(false);}}
  return <section aria-labelledby="treatments-title"><div className="section-heading"><div><p className="eyebrow">Configuración clínica</p><h1 id="treatments-title">Tratamientos</h1></div><span>{items.length} activos</span></div>{error&&<div className="notice notice--error" role="alert">{error}</div>}
    {isAdmin&&<form className="card form-grid" onSubmit={submit}><h2>Nuevo tratamiento</h2><label>Código<input name="code" pattern="[A-Za-z0-9._-]+" maxLength={40} required/></label><label>Nombre<input name="name" maxLength={160} required/></label><label>Categoría<input name="category" maxLength={100} required/></label><label>Precio de referencia en guaraníes<input name="default_price" type="number" min="0" step="1" required/></label><button disabled={busy}>{busy?'Guardando…':'Crear tratamiento'}</button></form>}
    <div className="card table-wrap"><table><caption>Catálogo de tratamientos</caption><thead><tr><th>Código</th><th>Tratamiento</th><th>Categoría</th><th>Precio referencial</th></tr></thead><tbody>{items.length?items.map((item)=><tr key={item.id}><td>{item.code}</td><th scope="row">{item.name}</th><td>{item.category}</td><td>{new Intl.NumberFormat('es-PY',{style:'currency',currency:'PYG',maximumFractionDigits:0}).format(Number(item.default_price))}</td></tr>):<tr><td colSpan={4}>Todavía no hay tratamientos.</td></tr>}</tbody></table></div>
  </section>;
}
