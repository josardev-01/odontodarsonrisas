import { describe, expect, it } from 'vitest';
import { invoiceStatusLabels, paymentMethodLabels } from './Billing';

describe('etiquetas de facturación',()=>{
  it('mantiene estados y medios visibles en español',()=>{
    expect(invoiceStatusLabels.partially_paid).toBe('Pago parcial');
    expect(invoiceStatusLabels.cancelled).toBe('Anulado');
    expect(paymentMethodLabels.cash).toBe('Efectivo');
    expect(paymentMethodLabels.transfer).toBe('Transferencia');
  });
});
