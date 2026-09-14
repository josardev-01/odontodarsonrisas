import { render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Odontogram } from './Odontogram';

afterEach(()=>vi.restoreAllMocks());

describe('Odontogram',()=>{
  it('presenta las 32 piezas permanentes como controles accesibles con texto de estado',async()=>{
    vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response('[]',{status:200,headers:{'Content-Type':'application/json'}}));
    render(<Odontogram patientId="synthetic-patient"/>);
    const group=screen.getByRole('group',{name:'Dentición permanente'});
    expect(within(group).getAllByRole('button')).toHaveLength(32);
    expect(within(group).getByRole('button',{name:/11.*Sin registro/})).toHaveAttribute('aria-pressed','true');
    expect(await screen.findByText('Historial del odontograma (0)')).toBeInTheDocument();
  });
});
