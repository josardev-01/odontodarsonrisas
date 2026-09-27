import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from './api';
import { TreatmentPlans } from './TreatmentPlans';
import type { OdontogramWorkItem, TreatmentPlan } from './types';

afterEach(()=>vi.restoreAllMocks());

describe('Planes vinculados al odontograma',()=>{
  it('carga todos los trabajos activos al crear el presupuesto',async()=>{
    const work=(id:string,tooth:string)=>({id,patient_id:'patient-1',source_event_id:`event-${id}`,tooth_code:tooth,surface:'mesial',treatment_id:'treatment-1',treatment_code:'REST',treatment_name:'Restauración',current_plan_id:null,completed_at:null,completed_by:null,result_event_id:null,created_at:'2026-09-27T12:00:00Z'} as OdontogramWorkItem);
    vi.spyOn(api,'treatmentPlans').mockResolvedValue([]);
    vi.spyOn(api,'odontogramWorkItems').mockResolvedValue([work('work-1','16'),work('work-2','26')]);
    const created=vi.spyOn(api,'createTreatmentPlan').mockResolvedValue({id:'plan-1',patient_id:'patient-1',created_by:'staff-1',created_at:'2026-09-27T12:00:00Z',title:'Presupuesto de prueba',status:'draft',items:[],total:'0'} as TreatmentPlan);
    render(<TreatmentPlans patientId="patient-1"/>);
    expect(await screen.findByRole('heading',{name:'Trabajos activos disponibles (2)'})).toBeInTheDocument();
    expect(screen.getByText('Pieza 16 · Mesial · Restauración')).toBeInTheDocument();
    expect(screen.getByText('Pieza 26 · Mesial · Restauración')).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText('Título'),'Presupuesto de prueba');
    fireEvent.submit(screen.getByRole('button',{name:'Crear presupuesto con 2 trabajos'}).closest('form')!);
    await waitFor(()=>expect(created).toHaveBeenCalledWith('patient-1',{title:'Presupuesto de prueba',clinical_notes:null,valid_until:null,from_odontogram:true}));
  });
});
