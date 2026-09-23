import { FormEvent, useEffect, useState } from 'react';
import { api, ApiError } from './api';
import type { AuditEvent, InvoiceStatus, ReportSummary } from './types';
import { invoiceStatusLabels } from './Billing';

const iso=(date:Date)=>date.toISOString().slice(0,10);
export function defaultReportRange(){const to=new Date();const from=new Date();from.setDate(from.getDate()-30);return {from:iso(from),to:iso(to)};}
const money=(value:string)=>new Intl.NumberFormat('es-PY',{style:'currency',currency:'PYG',maximumFractionDigits:0}).format(Number(value));

export function AdminDashboard(){
  const [range,setRange]=useState(defaultReportRange);const [summary,setSummary]=useState<ReportSummary|null>(null);const [events,setEvents]=useState<AuditEvent[]>([]);const [error,setError]=useState('');
  useEffect(()=>{setError('');Promise.all([api.reportSummary(range.from,range.to),api.auditEvents(25)]).then(([report,audit])=>{setSummary(report);setEvents(audit);}).catch((reason)=>setError(reason instanceof ApiError?reason.message:'No fue posible cargar el reporte.'));},[range]);
  function filter(event:FormEvent<HTMLFormElement>){event.preventDefault();const data=new FormData(event.currentTarget);setRange({from:String(data.get('from')),to:String(data.get('to'))});}
  return <section aria-labelledby="dashboard-title"><div className="section-heading"><div><p className="eyebrow">Administración</p><h1 id="dashboard-title">Panel y reportería</h1></div><span>Datos operativos agregados</span></div>
    <form className="range" onSubmit={filter} aria-label="Filtrar reporte"><label>Desde<input name="from" type="date" defaultValue={range.from} required/></label><label>Hasta<input name="to" type="date" defaultValue={range.to} required/></label><button>Actualizar</button></form>
    {error&&<div className="notice notice--error" role="alert">{error}</div>}{summary&&<><div className="metrics" aria-label="Indicadores principales"><article className="card"><span>Pacientes activos</span><strong>{summary.active_patients}</strong></article><article className="card"><span>Citas del período</span><strong>{summary.appointments_in_range}</strong></article><article className="card"><span>Próximas citas</span><strong>{summary.upcoming_appointments}</strong></article><article className="card"><span>Ingresos cobrados</span><strong>{money(summary.collected_amount)}</strong></article><article className="card"><span>Saldo pendiente</span><strong>{money(summary.outstanding_balance)}</strong></article></div>
      <section className="card report-card"><h2>Comprobantes por estado</h2><dl className="detail-grid">{(Object.entries(summary.invoices_by_status) as [InvoiceStatus,number][]).map(([status,total])=><div key={status}><dt>{invoiceStatusLabels[status]}</dt><dd>{total}</dd></div>)}</dl><p className="hint">Período: {summary.from_date} al {summary.to_date}. No incluye datos clínicos identificables.</p></section></>}
    <section className="card table-wrap"><h2>Actividad reciente</h2><table><caption>Últimos eventos de auditoría</caption><thead><tr><th>Fecha</th><th>Acción</th><th>Recurso</th><th>Resultado</th></tr></thead><tbody>{events.length?events.map((event)=><tr key={event.id}><td>{new Intl.DateTimeFormat('es-PY',{dateStyle:'short',timeStyle:'short'}).format(new Date(event.occurred_at))}</td><td>{event.action}</td><td>{event.resource_type}</td><td>{event.outcome}</td></tr>):<tr><td colSpan={4}>No hay eventos disponibles.</td></tr>}</tbody></table></section>
  </section>;
}
