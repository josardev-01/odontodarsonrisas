import { describe, expect, it, vi } from 'vitest';
import { defaultReportRange } from './AdminDashboard';

describe('panel administrativo',()=>{
  it('propone un rango inicial acotado de treinta días',()=>{
    vi.useFakeTimers();vi.setSystemTime(new Date('2026-09-14T12:00:00Z'));
    expect(defaultReportRange()).toEqual({from:'2026-08-15',to:'2026-09-14'});
    vi.useRealTimers();
  });
});
