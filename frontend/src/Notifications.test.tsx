import { describe, expect, it } from 'vitest';
import { channelLabels, deliveryStatusLabels } from './Notifications';

describe('notificaciones',()=>{
  it('solo expone WhatsApp/SMS y presenta estados en español',()=>{
    expect(Object.keys(channelLabels)).toEqual(['whatsapp','sms']);
    expect(channelLabels.whatsapp).toBe('WhatsApp');
    expect(deliveryStatusLabels.pending).toBe('Pendiente');
    expect(deliveryStatusLabels.sent).toBe('Enviado');
  });
});
