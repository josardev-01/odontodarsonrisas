import type { Appointment, AppointmentInput, AuditEvent, AuthenticatedUser, BillablePlan, ClinicalEntry, ClinicalEntryInput, ClinicalProfile, ClinicalProfileInput, ConsentInput, ConsentRecord, Invoice, LoginResponse, NotificationChannel, NotificationConsent, OdontogramEvent, OdontogramEventInput, Patient, PatientInput, PatientNotification, PatientUpdate, PaymentInput, Professional, ProfessionalInput, ProfessionalUpdate, ReportSummary, StaffUser, StaffUserInput, Treatment, TreatmentInput, TreatmentPlan, TreatmentPlanInput, TreatmentPlanItemInput, TreatmentPlanStatus } from './types';

const API_BASE = '/api/v1';

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export function messageForStatus(status: number): string {
  if (status === 401) return 'El correo o la contraseña no son válidos, o la sesión venció.';
  if (status === 403) return 'No tenés permiso para realizar esta acción.';
  if (status === 409) return 'La operación entra en conflicto con datos existentes. Revisá la fecha o los datos.';
  return 'Ocurrió un error inesperado. Intentá nuevamente.';
}

export function csrfTokenFromCookie(cookie = document.cookie): string | null {
  const item = cookie.split(';').map((part) => part.trim()).find((part) => part.startsWith('ds_csrf='));
  return item ? decodeURIComponent(item.slice('ds_csrf='.length)) : null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const method = (init?.method ?? 'GET').toUpperCase();
  const mutating = !['GET', 'HEAD', 'OPTIONS'].includes(method);
  const csrfToken = mutating && path !== '/auth/login' && path !== '/auth/bootstrap' ? csrfTokenFromCookie() : null;
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) throw new ApiError(response.status, messageForStatus(response.status));
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) => request<LoginResponse>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  me: () => request<AuthenticatedUser>('/auth/me'),
  logout: () => request<void>('/auth/logout', { method: 'POST' }),
  patients: (query='') => request<Patient[]>(`/patients${query?`?${new URLSearchParams({query})}`:''}`),
  createPatient: (input: PatientInput) => request<Patient>('/patients', { method: 'POST', body: JSON.stringify(input) }),
  updatePatient: (id:string,input:PatientUpdate) => request<Patient>(`/patients/${id}`,{method:'PUT',body:JSON.stringify(input)}),
  patient: (id: string) => request<Patient>(`/patients/${id}`),
  clinicalProfile: (id: string) => request<ClinicalProfile|null>(`/patients/${id}/clinical-profile`),
  saveClinicalProfile: (id: string, input: ClinicalProfileInput) => request<ClinicalProfile>(`/patients/${id}/clinical-profile`, { method:'PUT', body:JSON.stringify(input) }),
  clinicalEntries: (id: string) => request<ClinicalEntry[]>(`/patients/${id}/clinical-entries`),
  createClinicalEntry: (id:string,input:ClinicalEntryInput) => request<ClinicalEntry>(`/patients/${id}/clinical-entries`,{method:'POST',body:JSON.stringify(input)}),
  consents: (id:string) => request<ConsentRecord[]>(`/patients/${id}/consents`),
  createConsent: (id:string,input:ConsentInput) => request<ConsentRecord>(`/patients/${id}/consents`,{method:'POST',body:JSON.stringify(input)}),
  odontogramCurrent: (id:string) => request<OdontogramEvent[]>(`/patients/${id}/odontogram/current`),
  odontogramHistory: (id:string) => request<OdontogramEvent[]>(`/patients/${id}/odontogram/history`),
  recordOdontogramEvent: (id:string,input:OdontogramEventInput) => request<OdontogramEvent>(`/patients/${id}/odontogram/events`,{method:'POST',body:JSON.stringify(input)}),
  treatments: () => request<Treatment[]>('/treatments'),
  createTreatment: (input:TreatmentInput) => request<Treatment>('/treatments',{method:'POST',body:JSON.stringify(input)}),
  treatmentPlans: (patientId:string) => request<TreatmentPlan[]>(`/patients/${patientId}/treatment-plans`),
  createTreatmentPlan: (patientId:string,input:TreatmentPlanInput) => request<TreatmentPlan>(`/patients/${patientId}/treatment-plans`,{method:'POST',body:JSON.stringify(input)}),
  addTreatmentPlanItem: (patientId:string,planId:string,input:TreatmentPlanItemInput) => request<TreatmentPlan>(`/patients/${patientId}/treatment-plans/${planId}/items`,{method:'POST',body:JSON.stringify(input)}),
  changeTreatmentPlanStatus: (patientId:string,planId:string,status:TreatmentPlanStatus) => request<TreatmentPlan>(`/patients/${patientId}/treatment-plans/${planId}/status`,{method:'PATCH',body:JSON.stringify({status})}),
  invoices: (patientId:string) => request<Invoice[]>(`/patients/${patientId}/invoices`),
  billablePlans: (patientId:string) => request<BillablePlan[]>(`/patients/${patientId}/invoices/billable-plans`),
  createInvoice: (patientId:string,treatmentPlanId:string,dueDate:string|null) => request<Invoice>(`/patients/${patientId}/invoices`,{method:'POST',body:JSON.stringify({treatment_plan_id:treatmentPlanId,due_date:dueDate})}),
  addPayment: (patientId:string,invoiceId:string,input:PaymentInput) => request<Invoice>(`/patients/${patientId}/invoices/${invoiceId}/payments`,{method:'POST',body:JSON.stringify(input)}),
  cancelInvoice: (patientId:string,invoiceId:string) => request<Invoice>(`/patients/${patientId}/invoices/${invoiceId}/cancel`,{method:'POST'}),
  reportSummary: (from:string,to:string) => request<ReportSummary>(`/admin/reports/summary?${new URLSearchParams({from,to})}`),
  notificationConsents: (patientId:string) => request<NotificationConsent[]>(`/patients/${patientId}/notification-consents`),
  grantNotificationConsent: (patientId:string,channel:NotificationChannel,grantedAt:string,evidenceLocation:string) => request<NotificationConsent>(`/patients/${patientId}/notification-consents`,{method:'POST',body:JSON.stringify({channel,granted_at:grantedAt,evidence_location:evidenceLocation})}),
  revokeNotificationConsent: (patientId:string,channel:NotificationChannel) => request<NotificationConsent>(`/patients/${patientId}/notification-consents/${channel}/revoke`,{method:'POST'}),
  notifications: (patientId:string) => request<PatientNotification[]>(`/patients/${patientId}/notifications`),
  createNotification: (patientId:string,channel:NotificationChannel,message:string) => request<PatientNotification>(`/patients/${patientId}/notifications`,{method:'POST',body:JSON.stringify({channel,message})}),
  cancelNotification: (patientId:string,notificationId:string) => request<PatientNotification>(`/patients/${patientId}/notifications/${notificationId}/cancel`,{method:'POST'}),
  professionals: (includeInactive=false) => request<Professional[]>(`/professionals${includeInactive?'?include_inactive=true':''}`),
  createProfessional: (input:ProfessionalInput) => request<Professional>('/professionals',{method:'POST',body:JSON.stringify(input)}),
  updateProfessional: (id:string,input:ProfessionalUpdate) => request<Professional>(`/professionals/${id}`,{method:'PATCH',body:JSON.stringify(input)}),
  appointments: (from: string, to: string) => {
    const query = new URLSearchParams({ from: `${from}T00:00:00Z`, to: `${to}T23:59:59.999Z` });
    return request<Appointment[]>(`/appointments?${query}`);
  },
  createAppointment: (input: AppointmentInput) => request<Appointment>('/appointments', { method: 'POST', body: JSON.stringify(input) }),
  rescheduleAppointment: (id:string,startsAt:string,endsAt:string) => request<Appointment>(`/appointments/${id}/schedule`,{method:'PATCH',body:JSON.stringify({starts_at:startsAt,ends_at:endsAt})}),
  changeAppointmentStatus: (id:string,status:'cancelled'|'completed') => request<Appointment>(`/appointments/${id}/status`,{method:'PATCH',body:JSON.stringify({status})}),
  staffUsers: () => request<StaffUser[]>('/auth/users'),
  createStaffUser: (input:StaffUserInput) => request<AuthenticatedUser>('/auth/users',{method:'POST',body:JSON.stringify(input)}),
  updateStaffUser: (id:string,input:Partial<Pick<StaffUser,'display_name'|'role'|'active'>>) => request<StaffUser>(`/auth/users/${id}`,{method:'PATCH',body:JSON.stringify(input)}),
  resetStaffPassword: (id:string,password:string) => request<void>(`/auth/users/${id}/password`,{method:'POST',body:JSON.stringify({password})}),
  auditEvents: (limit=50) => request<AuditEvent[]>(`/admin/audit-events?${new URLSearchParams({limit:String(limit)})}`),
};
