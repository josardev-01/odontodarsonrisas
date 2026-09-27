import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from './api';
import { PatientDetail } from './PatientDetail';
import type { ConsentRecord, Patient } from './types';

afterEach(() => vi.restoreAllMocks());

describe('expediente del paciente',()=>{
  it('adjunta el historial firmado desde Perfil sin mostrar los antecedentes editables',async()=>{
    const patient={id:'patient-id',first_name:'Paciente',last_name:'Sintético',document_type:'TEST',document_number:'1',active:true,created_at:'2026-09-27'} as Patient;
    vi.spyOn(api,'consents').mockResolvedValue([]);
    vi.spyOn(api,'clinicalHistoryDocuments').mockResolvedValue([]);
    const uploaded=vi.spyOn(api,'uploadClinicalHistoryDocument').mockResolvedValue({id:'document-id',patient_id:patient.id,uploaded_by:'staff-id',created_at:'2026-09-27T12:00:00Z',attachment_filename:'historial.pdf',attachment_content_type:'application/pdf',attachment_size:14,attachment_sha256:'abc'});
    render(<PatientDetail patient={patient} user={{id:'staff-id',display_name:'Profesional',email:'test@example.com',roles:['profesional']}} onBack={()=>{}} onUpdate={async()=>{}}/>);
    expect(screen.getByRole('heading',{name:'Historial clínico'})).toBeInTheDocument();
    expect(screen.queryByRole('heading',{name:'Antecedentes médicos'})).not.toBeInTheDocument();
    expect(screen.queryByRole('tab',{name:'Historia clínica'})).not.toBeInTheDocument();
    const file=new File(['%PDF-1.4\nscan'],'historial.pdf',{type:'application/pdf'});
    await userEvent.upload(screen.getByLabelText(/Documento firmado \(PDF/),file);
    expect((screen.getByLabelText(/Documento firmado \(PDF/) as HTMLInputElement).files).toHaveLength(1);
    fireEvent.submit(screen.getByRole('button',{name:'Adjuntar historial clínico'}).closest('form')!);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    await waitFor(()=>expect(uploaded).toHaveBeenCalledWith(patient.id,file));
    expect(await screen.findByText('Documento adjunto: historial.pdf')).toBeInTheDocument();
  });
  it('muestra la carga nueva y permite adjuntar un escaneo a un consentimiento anterior', async()=>{
    const patient={id:'patient-id',first_name:'Paciente',last_name:'Sintético',document_type:'TEST',document_number:'1',active:true,created_at:'2026-09-27'} as Patient;
    const legacy={id:'consent-id',patient_id:patient.id,consent_type:'Consentimiento',document_version:'v1',purpose:'Prueba',signed_at:'2026-09-27T12:00:00Z',signer_name:'Paciente',evidence_location:'Archivo físico',status:'active',created_at:'2026-09-27T12:00:00Z'} as ConsentRecord;
    vi.spyOn(api,'consents').mockResolvedValue([legacy]);
    render(<PatientDetail patient={patient} user={{id:'staff-id',display_name:'Recepción',email:'test@example.com',roles:['recepcion']}} onBack={()=>{}} onUpdate={async()=>{}}/>);
    await userEvent.click(screen.getByRole('tab',{name:'Consentimientos'}));
    expect(await screen.findByText('Consentimiento · v1')).toBeInTheDocument();
    expect(screen.getByRole('button',{name:'Guardar consentimiento y adjunto'})).toBeInTheDocument();
    expect(screen.getByRole('button',{name:'Adjuntar documento'})).toBeInTheDocument();
    expect(screen.getAllByLabelText(/Adjuntar documento firmado/)).toHaveLength(2);
  });
});
