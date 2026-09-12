export type DevIdentity = { user: string; role: 'admin' | 'recepcion' };

export type Patient = {
  id: string;
  first_name: string;
  last_name: string;
  document_type: string;
  document_number: string;
  birth_date?: string | null;
  email?: string | null;
  phone?: string | null;
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
