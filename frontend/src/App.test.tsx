import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { App } from './App';

afterEach(()=>vi.restoreAllMocks());
describe('App',()=>{
  it('solicita correo y contraseña después de comprobar que no existe sesión',async()=>{
    vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(null,{status:401}));
    render(<App/>);
    await userEvent.click(screen.getByRole('button',{name:'Acceso personal'}));
    expect(await screen.findByLabelText('Correo electrónico')).toBeRequired();
    expect(screen.getByLabelText('Contraseña')).toBeRequired();
    expect(screen.queryByText('Rol')).not.toBeInTheDocument();
  });
  it('muestra credenciales inválidas de forma accesible',async()=>{
    vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(null,{status:401}));
    render(<App/>);
    await userEvent.click(screen.getByRole('button',{name:'Acceso personal'}));
    await userEvent.type(await screen.findByLabelText('Correo electrónico'),'persona@example.com');
    await userEvent.type(screen.getByLabelText('Contraseña'),'incorrecta');
    await userEvent.click(screen.getByRole('button',{name:'Ingresar'}));
    expect(await screen.findByRole('alert')).toHaveTextContent('correo o la contraseña');
  });
  it('muestra primero la landing pública y sus canales de contacto',()=>{
    vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(null,{status:401}));
    render(<App/>);
    expect(screen.getByRole('heading',{name:'Tu sonrisa merece un cuidado extraordinario.'})).toBeInTheDocument();
    expect(screen.getByRole('link',{name:'Consultar por WhatsApp'})).toHaveAttribute('href',expect.stringContaining('595994761736'));
    expect(screen.getByRole('button',{name:'Contactanos'})).toBeInTheDocument();
  });
});
