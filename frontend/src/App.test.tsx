import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { App } from './App';

afterEach(()=>vi.restoreAllMocks());
describe('App',()=>{
  it('solicita nombre y rol sin contraseña ni token',()=>{render(<App/>);expect(screen.getByLabelText('Nombre de desarrollo')).toBeRequired();expect(screen.getByLabelText('Rol')).toBeInTheDocument();expect(screen.queryByLabelText('Contraseña')).not.toBeInTheDocument();});
  it('muestra un rechazo 403 de forma accesible',async()=>{vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(null,{status:403}));render(<App/>);await userEvent.type(screen.getByLabelText('Nombre de desarrollo'),'Persona Sintética');await userEvent.click(screen.getByRole('button',{name:'Ingresar'}));expect(await screen.findByRole('alert')).toHaveTextContent('No tenés permiso');});
});
