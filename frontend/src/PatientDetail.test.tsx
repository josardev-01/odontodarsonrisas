import { describe, expect, it } from 'vitest';
import { clinicalEntryLabels } from './PatientDetail';

describe('etiquetas clínicas',()=>{
  it('presenta los códigos internos en español',()=>{
    expect(clinicalEntryLabels.consultation).toBe('Consulta');
    expect(clinicalEntryLabels.evolution).toBe('Evolución');
    expect(clinicalEntryLabels.diagnosis).toBe('Diagnóstico');
    expect(clinicalEntryLabels.procedure).toBe('Procedimiento');
  });
});
