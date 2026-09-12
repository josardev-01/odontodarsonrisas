import type { Appointment, AppointmentInput, DevIdentity, Patient, PatientInput, Professional } from './types';

const API_BASE = '/api/v1';

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export function messageForStatus(status: number): string {
  if (status === 401) return 'La identidad de desarrollo no es válida. Ingresá nuevamente.';
  if (status === 403) return 'No tenés permiso para realizar esta acción.';
  if (status === 409) return 'La operación entra en conflicto con datos existentes. Revisá la fecha o los datos.';
  return 'Ocurrió un error inesperado. Intentá nuevamente.';
}

async function request<T>(path: string, identity: DevIdentity, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      'X-Dev-User': identity.user,
      'X-Dev-Role': identity.role,
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) throw new ApiError(response.status, messageForStatus(response.status));
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  me: (identity: DevIdentity) => request<unknown>('/auth/me', identity),
  patients: (identity: DevIdentity) => request<Patient[]>('/patients', identity),
  createPatient: (identity: DevIdentity, input: PatientInput) => request<Patient>('/patients', identity, { method: 'POST', body: JSON.stringify(input) }),
  professionals: (identity: DevIdentity) => request<Professional[]>('/professionals', identity),
  appointments: (identity: DevIdentity, from: string, to: string) => {
    const query = new URLSearchParams({ from: `${from}T00:00:00Z`, to: `${to}T23:59:59.999Z` });
    return request<Appointment[]>(`/appointments?${query}`, identity);
  },
  createAppointment: (identity: DevIdentity, input: AppointmentInput) => request<Appointment>('/appointments', identity, { method: 'POST', body: JSON.stringify(input) }),
};
