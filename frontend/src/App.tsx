import { FormEvent, useCallback, useEffect, useState } from 'react';
import { api, ApiError } from './api';
import type { Appointment, AppointmentInput, DevIdentity, Patient, PatientInput, Professional } from './types';

type View = 'patients' | 'appointments';
const toDateInput = (date: Date) => date.toISOString().slice(0, 10);
export function initialRange() {
  const from = new Date(); from.setDate(from.getDate() - 7);
  const to = new Date(); to.setDate(to.getDate() + 90);
  return { from: toDateInput(from), to: toDateInput(to) };
}

function ErrorNotice({ message }: { message: string }) {
  return message ? <div className="notice notice--error" role="alert">{message}</div> : null;
}

function Login({ onLogin }: { onLogin: (identity: DevIdentity) => Promise<void> }) {
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError('');
    const data = new FormData(event.currentTarget);
    try { await onLogin({ user: String(data.get('user')).trim(), role: String(data.get('role')) as DevIdentity['role'] }); }
    catch (reason) { setError(reason instanceof ApiError ? reason.message : 'No fue posible conectar con el servicio.'); }
    finally { setBusy(false); }
  }
  return <main id="contenido" className="login-shell"><section className="card login-card" aria-labelledby="login-title">
    <p className="eyebrow">Acceso provisional de desarrollo</p><h1 id="login-title">Dar Sonrisas</h1>
    <p>Esta identificación no es un mecanismo de autenticación para producción.</p><ErrorNotice message={error} />
    <form onSubmit={submit} className="form-stack">
      <label>Nombre de desarrollo<input name="user" autoComplete="off" required /></label>
      <label>Rol<select name="role" defaultValue="recepcion"><option value="recepcion">Recepción</option><option value="admin">Administración</option></select></label>
      <button disabled={busy}>{busy ? 'Verificando…' : 'Ingresar'}</button>
    </form>
  </section></main>;
}

function PatientForm({ onCreate }: { onCreate: (input: PatientInput) => Promise<void> }) {
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); const form = event.currentTarget; const data = new FormData(form);
    try { await onCreate({ first_name: String(data.get('first_name')).trim(), last_name: String(data.get('last_name')).trim(), document_type: String(data.get('document_type')).trim(), document_number: String(data.get('document_number')).trim(), birth_date: String(data.get('birth_date')) || null, email: String(data.get('email')).trim() || null, phone: String(data.get('phone')).trim() || null }); form.reset(); }
    finally { setBusy(false); }
  }
  return <form className="card form-grid" onSubmit={submit} aria-labelledby="new-patient-title"><h2 id="new-patient-title">Nuevo paciente</h2>
    <label>Nombre<input name="first_name" autoComplete="given-name" required /></label><label>Apellido<input name="last_name" autoComplete="family-name" required /></label>
    <label>Tipo de documento<input name="document_type" defaultValue="CI" maxLength={30} required /></label><label>Número de documento<input name="document_number" maxLength={80} required /></label>
    <label>Fecha de nacimiento<input name="birth_date" type="date" /></label>
    <label>Correo<input name="email" type="email" autoComplete="email" /></label><label>Teléfono<input name="phone" type="tel" autoComplete="tel" /></label>
    <button disabled={busy}>{busy ? 'Guardando…' : 'Guardar paciente'}</button></form>;
}

function Patients({ items, onCreate }: { items: Patient[]; onCreate: (input: PatientInput) => Promise<void> }) {
  return <section aria-labelledby="patients-title"><div className="section-heading"><div><p className="eyebrow">Personas</p><h1 id="patients-title">Pacientes</h1></div><span>{items.length} registrados</span></div>
    <PatientForm onCreate={onCreate} /><div className="card table-wrap"><table><caption>Listado de pacientes</caption><thead><tr><th scope="col">Nombre</th><th scope="col">Correo</th><th scope="col">Teléfono</th></tr></thead><tbody>
      {items.length ? items.map((item) => <tr key={item.id}><th scope="row">{item.first_name} {item.last_name}</th><td>{item.email || '—'}</td><td>{item.phone || '—'}</td></tr>) : <tr><td colSpan={3}>Todavía no hay pacientes.</td></tr>}
    </tbody></table></div></section>;
}

function AppointmentForm({ patients, professionals, onCreate }: { patients: Patient[]; professionals: Professional[]; onCreate: (input: AppointmentInput) => Promise<void> }) {
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); const form = event.currentTarget; const data = new FormData(form);
    try { await onCreate({ patient_id: String(data.get('patient_id')), professional_id: String(data.get('professional_id')), starts_at: new Date(String(data.get('starts_at'))).toISOString(), ends_at: new Date(String(data.get('ends_at'))).toISOString(), reason: String(data.get('reason')).trim() || null }); form.reset(); }
    finally { setBusy(false); }
  }
  const unavailable = !patients.length || !professionals.length;
  return <form className="card form-grid" onSubmit={submit} aria-labelledby="new-appointment-title"><h2 id="new-appointment-title">Nueva cita</h2>
    <label>Paciente<select name="patient_id" required defaultValue=""><option value="" disabled>Seleccionar</option>{patients.map((item) => <option key={item.id} value={item.id}>{item.first_name} {item.last_name}</option>)}</select></label>
    <label>Profesional<select name="professional_id" required defaultValue=""><option value="" disabled>Seleccionar</option>{professionals.map((item) => <option key={item.id} value={item.id}>{item.display_name} — {item.specialty}</option>)}</select></label>
    <label>Inicio<input name="starts_at" type="datetime-local" required /></label><label>Fin<input name="ends_at" type="datetime-local" required /></label>
    <label>Motivo<input name="reason" maxLength={160} /></label><button disabled={busy || unavailable}>{busy ? 'Guardando…' : 'Agendar cita'}</button>
    {unavailable && <p className="hint">Se necesita al menos un paciente y un profesional.</p>}
  </form>;
}

function Appointments({ items, patients, professionals, range, onRange, onCreate }: { items: Appointment[]; patients: Patient[]; professionals: Professional[]; range: {from:string;to:string}; onRange:(range:{from:string;to:string})=>void; onCreate:(input:AppointmentInput)=>Promise<void> }) {
  const patientName = (id:string) => { const item=patients.find((p)=>p.id===id); return item ? `${item.first_name} ${item.last_name}` : 'Paciente no disponible'; };
  const professionalName = (id:string) => { const item=professionals.find((p)=>p.id===id); return item ? item.display_name : 'Profesional no disponible'; };
  return <section aria-labelledby="appointments-title"><div className="section-heading"><div><p className="eyebrow">Agenda</p><h1 id="appointments-title">Citas</h1></div><span>{items.length} en el rango</span></div>
    <form className="range" onSubmit={(event)=>{event.preventDefault();const data=new FormData(event.currentTarget);onRange({from:String(data.get('from')),to:String(data.get('to'))});}} aria-label="Filtrar agenda"><label>Desde<input name="from" type="date" defaultValue={range.from} required /></label><label>Hasta<input name="to" type="date" defaultValue={range.to} required /></label><button>Aplicar</button></form>
    <AppointmentForm patients={patients} professionals={professionals} onCreate={onCreate}/><div className="card appointment-list" aria-label="Listado de citas">
      {items.length ? items.map((item)=><article key={item.id}><time dateTime={item.starts_at}>{new Intl.DateTimeFormat('es-PY',{dateStyle:'medium',timeStyle:'short'}).format(new Date(item.starts_at))}</time><h2>{patientName(item.patient_id)}</h2><p>{professionalName(item.professional_id)} · {item.reason || 'Sin motivo informado'}</p></article>) : <p>Todavía no hay citas en este rango.</p>}
    </div></section>;
}

export function App() {
  const [identity,setIdentity]=useState<DevIdentity|null>(null); const [view,setView]=useState<View>('patients');
  const [patients,setPatients]=useState<Patient[]>([]); const [professionals,setProfessionals]=useState<Professional[]>([]); const [appointments,setAppointments]=useState<Appointment[]>([]);
  const [range,setRange]=useState(initialRange); const [error,setError]=useState('');
  const handleError=useCallback((reason:unknown)=>{setError(reason instanceof ApiError?reason.message:'No fue posible conectar con el servicio.');if(reason instanceof ApiError&&reason.status===401)setIdentity(null);},[]);
  async function login(candidate:DevIdentity){await api.me(candidate);setIdentity(candidate);}
  useEffect(()=>{if(!identity)return;setError('');Promise.all([api.patients(identity),api.professionals(identity),api.appointments(identity,range.from,range.to)]).then(([p,pro,a])=>{setPatients(p);setProfessionals(pro);setAppointments(a);}).catch(handleError);},[identity,range,handleError]);
  if(!identity)return <Login onLogin={login}/>;
  async function createPatient(input:PatientInput){setError('');try{const result=await api.createPatient(identity!,input);setPatients((items)=>[...items,result]);}catch(reason){handleError(reason);throw reason;}}
  async function createAppointment(input:AppointmentInput){setError('');try{const result=await api.createAppointment(identity!,input);setAppointments((items)=>[...items,result]);}catch(reason){handleError(reason);throw reason;}}
  return <div className="app-shell"><header className="topbar"><a className="brand" href="#contenido">Dar Sonrisas</a><span className="identity">{identity.user} · {identity.role}</span><button className="button-secondary" onClick={()=>setIdentity(null)}>Cerrar sesión</button></header>
    <div className="workspace"><nav aria-label="Secciones principales"><button aria-current={view==='patients'?'page':undefined} onClick={()=>setView('patients')}>Pacientes</button><button aria-current={view==='appointments'?'page':undefined} onClick={()=>setView('appointments')}>Agenda</button></nav>
      <main id="contenido"><ErrorNotice message={error}/>{view==='patients'?<Patients items={patients} onCreate={createPatient}/>:<Appointments items={appointments} patients={patients} professionals={professionals} range={range} onRange={setRange} onCreate={createAppointment}/>}</main></div></div>;
}
