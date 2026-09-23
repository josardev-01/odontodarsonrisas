import { render,screen } from '@testing-library/react';
import { afterEach,describe,expect,it,vi } from 'vitest';
import { StaffUsers } from './StaffUsers';

afterEach(()=>vi.restoreAllMocks());
describe('usuarios del personal',()=>{
  it('muestra las cuentas y protege la cuenta actual',async()=>{
    vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(JSON.stringify([{id:'admin-1',email:'admin@example.com',display_name:'Admin',role:'admin',active:true}]),{status:200,headers:{'Content-Type':'application/json'}}));
    render(<StaffUsers currentUserId="admin-1"/>);
    expect(await screen.findByText('admin@example.com')).toBeInTheDocument();
    expect(screen.getByRole('button',{name:'Desactivar'})).toBeDisabled();
  });
});
