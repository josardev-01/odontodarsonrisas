export type StaffRole = 'admin' | 'profesional' | 'recepcion';
export type AuthenticatedUser = { id: string; display_name: string; email: string; roles: StaffRole[] };
export type LoginResponse = { user: AuthenticatedUser; csrf_token: string };

export type Patient = {
  id: string;
  first_name: string;
  last_name: string;
  document_type: string;
  document_number: string;
  birth_date?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  city?: string | null;
  occupation?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
};
export type PatientInput = Omit<Patient, 'id'>;

export type Professional = { id: string; display_name: string; specialty: string };

export type Appointment = {
  id: string;
  patient_id: string;
  professional_id: string;
  starts_at: string;
  ends_at: string;
  reason?: string | null;
};
export type AppointmentInput = Omit<Appointment, 'id'>;

export type ClinicalProfile = {
  id: string;
  patient_id: string;
  blood_type?: string | null;
  allergies: string[];
  medications: string[];
  medical_conditions: string[];
  observations?: string | null;
  updated_at: string;
  updated_by: string;
};
export type ClinicalProfileInput = Pick<ClinicalProfile, 'blood_type'|'allergies'|'medications'|'medical_conditions'|'observations'>;
export type ClinicalEntry = { id:string; patient_id:string; author_id:string; entry_type:'consultation'|'evolution'|'diagnosis'|'procedure'; occurred_at:string; summary:string; notes:string; created_at:string };
export type ClinicalEntryInput = Pick<ClinicalEntry,'entry_type'|'occurred_at'|'summary'|'notes'>;
export type ConsentRecord = { id:string; patient_id:string; consent_type:string; document_version:string; purpose:string; signed_at:string; signer_name:string; signer_relationship?:string|null; evidence_location:string; status:'active'|'revoked'; revoked_at?:string|null; created_at:string };
export type ConsentInput = Pick<ConsentRecord,'consent_type'|'document_version'|'purpose'|'signed_at'|'signer_name'|'signer_relationship'|'evidence_location'>;
