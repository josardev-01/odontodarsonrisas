import { describe, expect, it, vi } from 'vitest';
import { api, messageForStatus } from './api';

describe('cliente API', () => {
  it.each([[401,'El correo o la contraseña no son válidos, o la sesión venció.'],[403,'No tenés permiso para realizar esta acción.'],[409,'La operación entra en conflicto con datos existentes. Revisá la fecha o los datos.']])('mapea %i', (status, expected) => expect(messageForStatus(status)).toBe(expected));
  it('usa cookies al consultar la sesión y no envía identidad mediante cabeceras', async () => {
    const fetchMock=vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response('{"id":"1","display_name":"Admin","email":"admin@example.com","roles":["admin"]}',{status:200,headers:{'Content-Type':'application/json'}}));
    await api.me();
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/auth/me',expect.objectContaining({credentials:'include'}));
    expect(fetchMock.mock.calls[0][1]?.headers).not.toHaveProperty('X-Dev-User');
  });
  it('incluye from y to al listar citas', async () => {
    const fetchMock=vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response('[]',{status:200,headers:{'Content-Type':'application/json'}}));
    await api.appointments('2026-01-01','2026-01-31');
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/appointments?from=2026-01-01T00%3A00%3A00Z&to=2026-01-31T23%3A59%3A59.999Z');
  });
  it('envía el adjunto como multipart con la protección CSRF de la sesión', async () => {
    document.cookie = 'ds_csrf=synthetic-csrf-token';
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('{}', { status: 201 }));
    const file = new File(['%PDF-1.4'], 'firma.pdf', { type: 'application/pdf' });
    await api.createConsentWithAttachment('patient-id', {
      consent_type: 'consentimiento', document_version: 'v1', purpose: 'Prueba',
      signed_at: '2026-09-27T12:00:00Z', signer_name: 'Paciente', evidence_location: null,
    }, file);
    const [url, options] = fetchMock.mock.lastCall!;
    expect(url).toBe('/api/v1/patients/patient-id/consents/with-attachment');
    expect(options?.headers).toHaveProperty('X-CSRF-Token', 'synthetic-csrf-token');
    expect(options?.headers).not.toHaveProperty('Content-Type');
    expect(options?.body).toBeInstanceOf(FormData);
    expect((options?.body as FormData).get('attachment')).toEqual(file);
  });
});
