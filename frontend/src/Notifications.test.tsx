import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from './api';
import { Notifications, channelLabels, deliveryStatusLabels } from './Notifications';
import type { NotificationConsent } from './types';

afterEach(() => vi.restoreAllMocks());

describe('notificaciones',()=>{
  it('solo expone WhatsApp/SMS y presenta estados en español',()=>{
    expect(Object.keys(channelLabels)).toEqual(['whatsapp','sms']);
    expect(channelLabels.whatsapp).toBe('WhatsApp');
    expect(deliveryStatusLabels.pending).toBe('Pendiente');
    expect(deliveryStatusLabels.sent).toBe('Enviado');
  });
  it('muestra la carga del documento firmado y el adjunto pendiente de una autorización anterior', async()=>{
    const legacy={id:'authorization-id',patient_id:'patient-id',channel:'sms',status:'granted',granted_at:'2026-09-27T12:00:00Z',evidence_location:'Archivo físico',created_at:'2026-09-27T12:00:00Z'} as NotificationConsent;
    vi.spyOn(api,'notificationConsents').mockResolvedValue([legacy]);
    vi.spyOn(api,'notifications').mockResolvedValue([]);
    render(<Notifications patientId="patient-id"/>);
    expect(await screen.findByText('SMS · Vigente')).toBeInTheDocument();
    expect(screen.getByRole('button',{name:'Guardar autorización y adjunto'})).toBeInTheDocument();
    expect(screen.getByRole('button',{name:'Adjuntar documento'})).toBeInTheDocument();
    expect(screen.getAllByLabelText(/Adjuntar autorización firmada/)).toHaveLength(2);
  });
});
