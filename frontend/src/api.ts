import type { Appointment, AppointmentInput, AuthenticatedUser, ClinicalEntry, ClinicalEntryInput, ClinicalProfile, ClinicalProfileInput, ConsentInput, ConsentRecord, LoginResponse, OdontogramEvent, OdontogramEventInput, Patient, PatientInput, Professional, Treatment, TreatmentInput } from './types';

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
  patients: () => request<Patient[]>('/patients'),
  createPatient: (input: PatientInput) => request<Patient>('/patients', { method: 'POST', body: JSON.stringify(input) }),
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
  professionals: () => request<Professional[]>('/professionals'),
  appointments: (from: string, to: string) => {
    const query = new URLSearchParams({ from: `${from}T00:00:00Z`, to: `${to}T23:59:59.999Z` });
    return request<Appointment[]>(`/appointments?${query}`);
  },
  createAppointment: (input: AppointmentInput) => request<Appointment>('/appointments', { method: 'POST', body: JSON.stringify(input) }),
};
