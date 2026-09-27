import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from './api';
import { Evolution } from './Evolution';
import type { EvolutionEntry, OdontogramWorkItem, TreatmentPlan } from './types';

afterEach(()=>vi.restoreAllMocks());

describe('Evolución',()=>{
  function renderAcceptedWork(){
    const work={id:'work-1',patient_id:'patient-1',source_event_id:'event-1',tooth_code:'16',surface:'mesial',treatment_id:'treatment-1',treatment_code:'REST',treatment_name:'Restauración',current_plan_id:'plan-1',completed_at:null,completed_by:null,result_event_id:null,created_at:'2026-09-27T12:00:00Z'} as OdontogramWorkItem;
    const plan={id:'plan-1',patient_id:'patient-1',created_by:'staff-1',created_at:'2026-09-27T12:00:00Z',title:'Presupuesto',status:'accepted',items:[],total:'0'} as TreatmentPlan;
    vi.spyOn(api,'odontogramWorkItems').mockResolvedValue([work]);
    vi.spyOn(api,'treatmentPlans').mockResolvedValue([plan]);
    vi.spyOn(api,'evolutionEntries').mockResolvedValue([]);
    const saved=vi.spyOn(api,'recordEvolution').mockResolvedValue({id:'entry-1',patient_id:'patient-1',work_item_id:'work-1',plan_item_id:'item-1',recorded_by:'staff-1',control_completed:false,answers:[],created_at:'2026-09-27T12:00:00Z'} as EvolutionEntry);
    render(<Evolution patientId="patient-1"/>);
    return saved;
  }
  it('guarda notas de sesión sin exigir el check ni finalizar el tratamiento',async()=>{
    const saved=renderAcceptedWork();
    expect(await screen.findByRole('heading',{name:'Pieza 16 · Mesial · Restauración'})).toBeInTheDocument();
    expect(screen.getByRole('checkbox',{name:/Control realizado/})).not.toBeChecked();
    expect(screen.queryByRole('radio')).not.toBeInTheDocument();
    await userEvent.type(screen.getByLabelText('Notas de sesión'),'Trabajo iniciado; continúa en otra sesión.');
    fireEvent.submit(screen.getByRole('button',{name:'Guardar notas de sesión'}).closest('form')!);
    await waitFor(()=>expect(saved).toHaveBeenCalledWith('patient-1','work-1',false,'Trabajo iniciado; continúa en otra sesión.'));
  });
  it('finaliza con el único check sin exigir notas',async()=>{
    const saved=renderAcceptedWork();
    await screen.findByRole('heading',{name:'Pieza 16 · Mesial · Restauración'});
    await userEvent.click(screen.getByRole('checkbox',{name:/Control realizado/}));
    expect(screen.queryByLabelText('Notas de sesión')).not.toBeInTheDocument();
    fireEvent.submit(screen.getByRole('button',{name:'Guardar y finalizar tratamiento'}).closest('form')!);
    await waitFor(()=>expect(saved).toHaveBeenCalledWith('patient-1','work-1',true,null));
  });
});
