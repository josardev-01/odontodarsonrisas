import { describe, expect, it, vi } from 'vitest';
import { api, messageForStatus } from './api';

describe('cliente API', () => {
  it.each([[401,'La identidad de desarrollo no es válida. Ingresá nuevamente.'],[403,'No tenés permiso para realizar esta acción.'],[409,'La operación entra en conflicto con datos existentes. Revisá la fecha o los datos.']])('mapea %i', (status, expected) => expect(messageForStatus(status)).toBe(expected));
  it('envía la identidad solo por cabeceras al endpoint real de sesión', async () => {
    const fetchMock=vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response('{}',{status:200,headers:{'Content-Type':'application/json'}}));
    await api.me({user:'Persona Sintética',role:'recepcion'});
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/auth/me',expect.objectContaining({headers:expect.objectContaining({'X-Dev-User':'Persona Sintética','X-Dev-Role':'recepcion'})}));
  });
  it('incluye from y to al listar citas', async () => {
    const fetchMock=vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response('[]',{status:200,headers:{'Content-Type':'application/json'}}));
    await api.appointments({user:'Persona Sintética',role:'recepcion'},'2026-01-01','2026-01-31');
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/appointments?from=2026-01-01T00%3A00%3A00Z&to=2026-01-31T23%3A59%3A59.999Z');
  });
});
