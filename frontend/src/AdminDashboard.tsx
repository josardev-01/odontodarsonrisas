import { FormEvent, useEffect, useState } from 'react';
import { api, ApiError } from './api';
import type { InvoiceStatus, ReportSummary } from './types';
import { invoiceStatusLabels } from './Billing';

const iso=(date:Date)=>date.toISOString().slice(0,10);
export function defaultReportRange(){const to=new Date();const from=new Date();from.setDate(from.getDate()-30);return {from:iso(from),to:iso(to)};}
const money=(value:string)=>new Intl.NumberFormat('es-PY',{style:'currency',currency:'PYG',maximumFractionDigits:0}).format(Number(value));

export function AdminDashboard(){
  const [range,setRange]=useState(defaultReportRange);const [summary,setSummary]=useState<ReportSummary|null>(null);const [error,setError]=useState('');
  useEffect(()=>{setError('');api.reportSummary(range.from,range.to).then(setSummary).catch((reason)=>setError(reason instanceof ApiError?reason.message:'No fue posible cargar el reporte.'));},[range]);
  function filter(event:FormEvent<HTMLFormElement>){event.preventDefault();const data=new FormData(event.currentTarget);setRange({from:String(data.get('from')),to:String(data.get('to'))});}
  return <section aria-labelledby="dashboard-title"><div className="section-heading"><div><p className="eyebrow">Administración</p><h1 id="dashboard-title">Panel y reportería</h1></div><span>Datos operativos agregados</span></div>
    <form className="range" onSubmit={filter} aria-label="Filtrar reporte"><label>Desde<input name="from" type="date" defaultValue={range.from} required/></label><label>Hasta<input name="to" type="date" defaultValue={range.to} required/></label><button>Actualizar</button></form>
    {error&&<div className="notice notice--error" role="alert">{error}</div>}{summary&&<><div className="metrics" aria-label="Indicadores principales"><article className="card"><span>Pacientes activos</span><strong>{summary.active_patients}</strong></article><article className="card"><span>Citas del período</span><strong>{summary.appointments_in_range}</strong></article><article className="card"><span>Próximas citas</span><strong>{summary.upcoming_appointments}</strong></article><article className="card"><span>Ingresos cobrados</span><strong>{money(summary.collected_amount)}</strong></article><article className="card"><span>Saldo pendiente</span><strong>{money(summary.outstanding_balance)}</strong></article></div>
      <section className="card report-card"><h2>Comprobantes por estado</h2><dl className="detail-grid">{(Object.entries(summary.invoices_by_status) as [InvoiceStatus,number][]).map(([status,total])=><div key={status}><dt>{invoiceStatusLabels[status]}</dt><dd>{total}</dd></div>)}</dl><p className="hint">Período: {summary.from_date} al {summary.to_date}. No incluye datos clínicos identificables.</p></section></>}
  </section>;
}
