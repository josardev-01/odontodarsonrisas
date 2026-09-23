import { FormEvent, useCallback, useEffect, useState } from 'react';
import { api, ApiError } from './api';
import type { Appointment, AppointmentInput, AuthenticatedUser, Patient, PatientInput, PatientUpdate, Professional, ProfessionalInput, ProfessionalUpdate } from './types';
import { PatientDetail } from './PatientDetail';
import { TreatmentCatalog } from './TreatmentCatalog';
import { AdminDashboard } from './AdminDashboard';
import { PublicSite } from './PublicSite';
import { Professionals } from './Professionals';
import { StaffUsers } from './StaffUsers';

type View = 'patients' | 'appointments' | 'treatments' | 'professionals' | 'users' | 'dashboard';
const toDateInput = (date: Date) => date.toISOString().slice(0, 10);
export function initialRange() {
  const from = new Date(); from.setDate(from.getDate() - 7);
  const to = new Date(); to.setDate(to.getDate() + 90);
  return { from: toDateInput(from), to: toDateInput(to) };
}
export function canManageClinic(user: AuthenticatedUser) {
  return user.roles.some((role) => role === 'admin' || role === 'recepcion' || role === 'profesional');
}

function ErrorNotice({ message }: { message: string }) {
  return message ? <div className="notice notice--error" role="alert">{message}</div> : null;
}

function Login({ error, onLogin, onBack }: { error: string; onLogin: (email: string, password: string) => Promise<void>; onBack:()=>void }) {
  const [localError, setLocalError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setLocalError('');
    const data = new FormData(event.currentTarget);
    try { await onLogin(String(data.get('email')).trim(), String(data.get('password'))); }
    catch (reason) { setLocalError(reason instanceof ApiError ? reason.message : 'No fue posible conectar con el servicio.'); }
    finally { setBusy(false); }
  }
  return <main id="contenido" className="login-shell"><section className="card login-card" aria-labelledby="login-title"><button type="button" className="login-back" onClick={onBack}>← Volver al sitio público</button>
    <p className="eyebrow">Acceso para personal</p><h1 id="login-title">Dar Sonrisas</h1>
    <p>Ingresá con la cuenta asignada por la clínica.</p><ErrorNotice message={localError || error} />
    <form onSubmit={submit} className="form-stack">
      <label>Correo electrónico<input name="email" type="email" autoComplete="username" required /></label>
      <label>Contraseña<input name="password" type="password" autoComplete="current-password" required /></label>
      <button disabled={busy}>{busy ? 'Ingresando…' : 'Ingresar'}</button>
    </form>
  </section></main>;
}

function PatientForm({ onCreate }: { onCreate: (input: PatientInput) => Promise<void> }) {
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); const form = event.currentTarget; const data = new FormData(form);
    try { await onCreate({ first_name: String(data.get('first_name')).trim(), last_name: String(data.get('last_name')).trim(), document_type: String(data.get('document_type')).trim(), document_number: String(data.get('document_number')).trim(), birth_date: String(data.get('birth_date')) || null, email: String(data.get('email')).trim() || null, phone: String(data.get('phone')).trim() || null, address:String(data.get('address')).trim()||null,city:String(data.get('city')).trim()||null,occupation:String(data.get('occupation')).trim()||null,emergency_contact_name:String(data.get('emergency_contact_name')).trim()||null,emergency_contact_phone:String(data.get('emergency_contact_phone')).trim()||null }); form.reset(); }
    finally { setBusy(false); }
  }
  return <form className="card form-grid" onSubmit={submit} aria-labelledby="new-patient-title"><h2 id="new-patient-title">Nuevo paciente</h2>
    <label>Nombre<input name="first_name" autoComplete="given-name" required /></label><label>Apellido<input name="last_name" autoComplete="family-name" required /></label>
    <label>Tipo de documento<input name="document_type" defaultValue="CI" maxLength={30} required /></label><label>Número de documento<input name="document_number" maxLength={80} required /></label>
    <label>Fecha de nacimiento<input name="birth_date" type="date" /></label>
    <label>Correo<input name="email" type="email" autoComplete="email" /></label><label>Teléfono<input name="phone" type="tel" autoComplete="tel" /></label>
    <label>Dirección<input name="address" autoComplete="street-address"/></label><label>Ciudad<input name="city" autoComplete="address-level2"/></label><label>Ocupación<input name="occupation"/></label><label>Contacto de emergencia<input name="emergency_contact_name"/></label><label>Teléfono de emergencia<input name="emergency_contact_phone" type="tel"/></label>
    <button disabled={busy}>{busy ? 'Guardando…' : 'Guardar paciente'}</button></form>;
}

function Patients({ items, onCreate, onOpen, onSearch, canCreate }: { items: Patient[]; onCreate: (input: PatientInput) => Promise<void>; onOpen:(patient:Patient)=>void; onSearch:(query:string)=>Promise<void>; canCreate:boolean }) {
  return <section aria-labelledby="patients-title"><div className="section-heading"><div><p className="eyebrow">Personas</p><h1 id="patients-title">Pacientes</h1></div><span>{items.length} registrados</span></div>
    <form className="range" role="search" onSubmit={(event)=>{event.preventDefault();void onSearch(String(new FormData(event.currentTarget).get('query')).trim());}}><label>Buscar por nombre o documento<input name="query" type="search" maxLength={100}/></label><button>Buscar</button></form>
    {canCreate&&<PatientForm onCreate={onCreate} />}<div className="card table-wrap"><table><caption>Listado de pacientes</caption><thead><tr><th scope="col">Nombre</th><th scope="col">Correo</th><th scope="col">Teléfono</th><th scope="col">Estado</th></tr></thead><tbody>
      {items.length ? items.map((item) => <tr key={item.id}><th scope="row"><button className="link-button" onClick={()=>onOpen(item)}>{item.first_name} {item.last_name}</button></th><td>{item.email || '—'}</td><td>{item.phone || '—'}</td><td>{item.active?'Activo':'Inactivo'}</td></tr>) : <tr><td colSpan={4}>No se encontraron pacientes.</td></tr>}
    </tbody></table></div></section>;
}

function AppointmentForm({ patients, professionals, onCreate }: { patients: Patient[]; professionals: Professional[]; onCreate: (input: AppointmentInput) => Promise<void> }) {
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); const form = event.currentTarget; const data = new FormData(form);
    try { await onCreate({ patient_id: String(data.get('patient_id')), professional_id: String(data.get('professional_id')), starts_at: new Date(String(data.get('starts_at'))).toISOString(), ends_at: new Date(String(data.get('ends_at'))).toISOString(), reason: String(data.get('reason')).trim() || null }); form.reset(); }
    finally { setBusy(false); }
  }
  const availableProfessionals=professionals.filter((item)=>item.active);
  const unavailable = !patients.some((item)=>item.active) || !availableProfessionals.length;
  return <form className="card form-grid" onSubmit={submit} aria-labelledby="new-appointment-title"><h2 id="new-appointment-title">Nueva cita</h2>
    <label>Paciente<select name="patient_id" required defaultValue=""><option value="" disabled>Seleccionar</option>{patients.filter((item)=>item.active).map((item) => <option key={item.id} value={item.id}>{item.first_name} {item.last_name}</option>)}</select></label>
    <label>Profesional<select name="professional_id" required defaultValue=""><option value="" disabled>Seleccionar</option>{availableProfessionals.map((item) => <option key={item.id} value={item.id}>{item.display_name} — {item.specialty}</option>)}</select></label>
    <label>Inicio<input name="starts_at" type="datetime-local" required /></label><label>Fin<input name="ends_at" type="datetime-local" required /></label>
    <label>Motivo<input name="reason" maxLength={160} /></label><button disabled={busy || unavailable}>{busy ? 'Guardando…' : 'Agendar cita'}</button>
    {unavailable && <p className="hint">Se necesita al menos un paciente y un profesional.</p>}
  </form>;
}

const appointmentStatusLabels:Record<Appointment['status'],string>={scheduled:'Agendada',cancelled:'Cancelada',completed:'Completada'};
const datetimeLocal=(value:string)=>{const date=new Date(value);const offset=date.getTimezoneOffset()*60000;return new Date(date.getTime()-offset).toISOString().slice(0,16);};
function Appointments({ items, patients, professionals, range, onRange, onCreate, onReschedule, onStatus }: { items: Appointment[]; patients: Patient[]; professionals: Professional[]; range: {from:string;to:string}; onRange:(range:{from:string;to:string})=>void; onCreate:(input:AppointmentInput)=>Promise<void>;onReschedule:(id:string,startsAt:string,endsAt:string)=>Promise<void>;onStatus:(id:string,status:'cancelled'|'completed')=>Promise<void> }) {
  const [editing,setEditing]=useState<Appointment|null>(null);const [busy,setBusy]=useState(false);
  const patientName = (id:string) => { const item=patients.find((p)=>p.id===id); return item ? `${item.first_name} ${item.last_name}` : 'Paciente no disponible'; };
  const professionalName = (id:string) => { const item=professionals.find((p)=>p.id===id); return item ? item.display_name : 'Profesional no disponible'; };
  return <section aria-labelledby="appointments-title"><div className="section-heading"><div><p className="eyebrow">Agenda</p><h1 id="appointments-title">Citas</h1></div><span>{items.length} en el rango</span></div>
    <form className="range" onSubmit={(event)=>{event.preventDefault();const data=new FormData(event.currentTarget);onRange({from:String(data.get('from')),to:String(data.get('to'))});}} aria-label="Filtrar agenda"><label>Desde<input name="from" type="date" defaultValue={range.from} required /></label><label>Hasta<input name="to" type="date" defaultValue={range.to} required /></label><button>Aplicar</button></form>
    <AppointmentForm patients={patients} professionals={professionals} onCreate={onCreate}/>{editing&&<form className="card form-grid" onSubmit={async(event)=>{event.preventDefault();setBusy(true);const data=new FormData(event.currentTarget);try{await onReschedule(editing.id,new Date(String(data.get('starts_at'))).toISOString(),new Date(String(data.get('ends_at'))).toISOString());setEditing(null);}finally{setBusy(false);}}}><h2>Reprogramar cita</h2><label>Nuevo inicio<input name="starts_at" type="datetime-local" defaultValue={datetimeLocal(editing.starts_at)} required/></label><label>Nuevo fin<input name="ends_at" type="datetime-local" defaultValue={datetimeLocal(editing.ends_at)} required/></label><button disabled={busy}>Guardar horario</button><button type="button" className="button-secondary" onClick={()=>setEditing(null)}>Cancelar edición</button></form>}<div className="card appointment-list" aria-label="Listado de citas">
      {items.length ? items.map((item)=><article key={item.id}><time dateTime={item.starts_at}>{new Intl.DateTimeFormat('es-PY',{dateStyle:'medium',timeStyle:'short'}).format(new Date(item.starts_at))}</time><h2>{patientName(item.patient_id)}</h2><p>{professionalName(item.professional_id)} · {item.reason || 'Sin motivo informado'}</p><span className={`status status--${item.status==='scheduled'?'active':'inactive'}`}>{appointmentStatusLabels[item.status]}</span>{item.status==='scheduled'&&<div className="table-actions"><button type="button" className="button-secondary" onClick={()=>setEditing(item)}>Reprogramar</button><button type="button" className="button-secondary" onClick={()=>void onStatus(item.id,'completed')}>Completar</button><button type="button" className="button-secondary" onClick={()=>void onStatus(item.id,'cancelled')}>Cancelar cita</button></div>}</article>) : <p>Todavía no hay citas en este rango.</p>}
    </div></section>;
}

export function App() {
  const [siteView,setSiteView]=useState<'public'|'staff'>('public');
  const [user,setUser]=useState<AuthenticatedUser|null>(null); const [checking,setChecking]=useState(true); const [loginError,setLoginError]=useState('');
  const [view,setView]=useState<View>('patients'); const [patients,setPatients]=useState<Patient[]>([]); const [professionals,setProfessionals]=useState<Professional[]>([]); const [appointments,setAppointments]=useState<Appointment[]>([]);
  const [selectedPatient,setSelectedPatient]=useState<Patient|null>(null);
  const [range,setRange]=useState(initialRange); const [error,setError]=useState('');
  const handleError=useCallback((reason:unknown)=>{setError(reason instanceof ApiError?reason.message:'No fue posible conectar con el servicio.');if(reason instanceof ApiError&&reason.status===401){setUser(null);setLoginError('La sesión venció. Ingresá nuevamente.');}},[]);
  useEffect(()=>{api.me().then(setUser).catch((reason)=>{if(!(reason instanceof ApiError&&reason.status===401))setLoginError('No fue posible verificar la sesión.');}).finally(()=>setChecking(false));},[]);
  useEffect(()=>{if(!user||!canManageClinic(user))return;setError('');if(user.roles.includes('profesional')){api.patients().then(setPatients).catch(handleError);return;}Promise.all([api.patients(),api.professionals(user.roles.includes('admin')),api.appointments(range.from,range.to)]).then(([p,pro,a])=>{setPatients(p);setProfessionals(pro);setAppointments(a);}).catch(handleError);},[user,range,handleError]);
  async function login(email:string,password:string){const result=await api.login(email,password);setLoginError('');setUser(result.user);}
  async function logout(){try{await api.logout();}catch(reason){if(!(reason instanceof ApiError&&reason.status===401)){handleError(reason);return;}}setUser(null);setLoginError('');setError('');}
  if(siteView==='public')return <PublicSite onStaffAccess={()=>setSiteView('staff')}/>;
  if(checking)return <main id="contenido" className="login-shell" aria-busy="true"><p>Verificando sesión…</p></main>;
  if(!user)return <Login error={loginError} onLogin={login} onBack={()=>setSiteView('public')}/>;
  if(!canManageClinic(user))return <div className="app-shell"><header className="topbar"><span className="brand">Dar Sonrisas</span><button className="button-secondary" onClick={logout}>Cerrar sesión</button></header><main id="contenido" className="restricted"><h1>Acceso limitado</h1><p>Tu rol no tiene funciones habilitadas en este incremento.</p></main></div>;
  async function createPatient(input:PatientInput){setError('');try{const result=await api.createPatient(input);setPatients((items)=>[...items,result]);}catch(reason){handleError(reason);throw reason;}}
  async function searchPatients(query:string){setError('');try{setPatients(await api.patients(query));}catch(reason){handleError(reason);throw reason;}}
  async function updatePatient(id:string,input:PatientUpdate){setError('');try{const result=await api.updatePatient(id,input);setPatients((items)=>items.map((item)=>item.id===id?result:item));setSelectedPatient(result);}catch(reason){handleError(reason);throw reason;}}
  async function createAppointment(input:AppointmentInput){setError('');try{const result=await api.createAppointment(input);setAppointments((items)=>[...items,result]);}catch(reason){handleError(reason);throw reason;}}
  async function rescheduleAppointment(id:string,startsAt:string,endsAt:string){setError('');try{const result=await api.rescheduleAppointment(id,startsAt,endsAt);setAppointments((items)=>items.map((item)=>item.id===id?result:item));}catch(reason){handleError(reason);throw reason;}}
  async function changeAppointmentStatus(id:string,status:'cancelled'|'completed'){setError('');try{const result=await api.changeAppointmentStatus(id,status);setAppointments((items)=>items.map((item)=>item.id===id?result:item));}catch(reason){handleError(reason);throw reason;}}
  async function createProfessional(input:ProfessionalInput){setError('');try{const result=await api.createProfessional(input);setProfessionals((items)=>[...items,result].sort((a,b)=>a.display_name.localeCompare(b.display_name,'es')));}catch(reason){handleError(reason);throw reason;}}
  async function updateProfessional(id:string,input:ProfessionalUpdate){setError('');try{const result=await api.updateProfessional(id,input);setProfessionals((items)=>items.map((item)=>item.id===id?result:item));}catch(reason){handleError(reason);throw reason;}}
  return <div className="app-shell"><a className="skip-link" href="#contenido">Saltar al contenido</a><header className="topbar"><a className="brand" href="#contenido">Dar Sonrisas</a><button className="button-secondary" onClick={()=>setSiteView('public')}>Sitio público</button><span className="identity">{user.display_name} · {user.roles.join(', ')}</span><button className="button-secondary" onClick={logout}>Cerrar sesión</button></header>
    <div className="workspace"><nav aria-label="Secciones principales"><button aria-current={view==='patients'?'page':undefined} onClick={()=>{setView('patients');setSelectedPatient(null);}}>Pacientes</button>{!user.roles.includes('profesional')&&<button aria-current={view==='appointments'?'page':undefined} onClick={()=>{setView('appointments');setSelectedPatient(null);}}>Agenda</button>}<button aria-current={view==='treatments'?'page':undefined} onClick={()=>{setView('treatments');setSelectedPatient(null);}}>Tratamientos</button>{user.roles.includes('admin')&&<button aria-current={view==='professionals'?'page':undefined} onClick={()=>{setView('professionals');setSelectedPatient(null);}}>Profesionales</button>}{user.roles.includes('admin')&&<button aria-current={view==='users'?'page':undefined} onClick={()=>{setView('users');setSelectedPatient(null);}}>Usuarios</button>}{user.roles.includes('admin')&&<button aria-current={view==='dashboard'?'page':undefined} onClick={()=>{setView('dashboard');setSelectedPatient(null);}}>Panel administrativo</button>}</nav>
      <main id="contenido"><ErrorNotice message={error}/>{selectedPatient?<PatientDetail patient={selectedPatient} user={user} onBack={()=>setSelectedPatient(null)} onUpdate={updatePatient}/>:view==='patients'?<Patients items={patients} onCreate={createPatient} onOpen={setSelectedPatient} onSearch={searchPatients} canCreate={!user.roles.includes('profesional')}/>:view==='treatments'?<TreatmentCatalog user={user}/>:view==='professionals'?<Professionals items={professionals} onCreate={createProfessional} onUpdate={updateProfessional}/>:view==='users'?<StaffUsers currentUserId={user.id}/>:view==='dashboard'?<AdminDashboard/>:<Appointments items={appointments} patients={patients} professionals={professionals} range={range} onRange={setRange} onCreate={createAppointment} onReschedule={rescheduleAppointment} onStatus={changeAppointmentStatus}/>}</main></div></div>;
}
