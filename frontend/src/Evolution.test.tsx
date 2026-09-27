import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from './api';
import { Evolution } from './Evolution';
import type { EvolutionEntry, OdontogramWorkItem, TreatmentPlan } from './types';

afterEach(()=>vi.restoreAllMocks());

describe('Evolución',()=>{
  it('permite Observación como tercera respuesta y guarda el checklist del trabajo',async()=>{
    const work={id:'work-1',patient_id:'patient-1',source_event_id:'event-1',tooth_code:'16',surface:'mesial',treatment_id:'treatment-1',treatment_code:'REST',treatment_name:'Restauración',current_plan_id:'plan-1',completed_at:null,completed_by:null,result_event_id:null,created_at:'2026-09-27T12:00:00Z'} as OdontogramWorkItem;
    const plan={id:'plan-1',patient_id:'patient-1',created_by:'staff-1',created_at:'2026-09-27T12:00:00Z',title:'Presupuesto',status:'accepted',items:[],total:'0'} as TreatmentPlan;
    vi.spyOn(api,'odontogramWorkItems').mockResolvedValue([work]);
    vi.spyOn(api,'treatmentPlans').mockResolvedValue([plan]);
    vi.spyOn(api,'evolutionEntries').mockResolvedValue([]);
    const saved=vi.spyOn(api,'recordEvolution').mockResolvedValue({id:'entry-1',patient_id:'patient-1',work_item_id:'work-1',plan_item_id:'item-1',recorded_by:'staff-1',answers:[],created_at:'2026-09-27T12:00:00Z'} as EvolutionEntry);
    render(<Evolution patientId="patient-1"/>);
    expect(await screen.findByRole('heading',{name:'Pieza 16 · Mesial · Restauración'})).toBeInTheDocument();
    await userEvent.click(within(screen.getByRole('group',{name:'Preparación realizada'})).getByRole('radio',{name:'Sí'}));
    await userEvent.click(within(screen.getByRole('group',{name:'Procedimiento realizado'})).getByRole('radio',{name:'Observación'}));
    await userEvent.type(screen.getByLabelText('Detalle de la observación'),'Falta una sesión');
    await userEvent.click(within(screen.getByRole('group',{name:'Control final realizado'})).getByRole('radio',{name:'No'}));
    fireEvent.submit(screen.getByRole('button',{name:'Guardar evolución'}).closest('form')!);
    await waitFor(()=>expect(saved).toHaveBeenCalledWith('patient-1','work-1',[
      {step:'preparation',response:'yes',observation:null},
      {step:'procedure',response:'observation',observation:'Falta una sesión'},
      {step:'final_control',response:'no',observation:null},
    ],null));
    expect(screen.queryByRole('button',{name:/Finalizar procedimiento y actualizar/})).not.toBeInTheDocument();
  });
});
