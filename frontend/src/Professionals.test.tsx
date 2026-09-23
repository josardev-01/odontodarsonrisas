import { render,screen } from '@testing-library/react';
import { describe,expect,it,vi } from 'vitest';
import { Professionals } from './Professionals';

describe('gestión de profesionales',()=>{
  it('distingue profesionales activos e inactivos',()=>{
    render(<Professionals items={[{id:'1',display_name:'Dra. Ana',specialty:'General',active:true,created_at:'2026-09-15T00:00:00Z'},{id:'2',display_name:'Dr. Luis',specialty:'Ortodoncia',active:false,created_at:'2026-09-15T00:00:00Z'}]} onCreate={vi.fn()} onUpdate={vi.fn()}/>);
    expect(screen.getByText('1 activos')).toBeInTheDocument();
    expect(screen.getAllByRole('button',{name:'Editar'})).toHaveLength(2);
    expect(screen.getByRole('button',{name:'Desactivar'})).toBeInTheDocument();
    expect(screen.getByRole('button',{name:'Reactivar'})).toBeInTheDocument();
  });
});
