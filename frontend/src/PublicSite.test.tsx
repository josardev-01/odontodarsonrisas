import { describe, expect, it } from 'vitest';
import { buildContactMailto } from './PublicSite';

describe('sitio público',()=>{
  it('prepara el correo de consulta con destinatario y datos codificados',()=>{
    const href=buildContactMailto({name:'Ana Pérez',email:'ana@example.com',phone:'+595981000000',subject:'Consulta general',message:'Quisiera información'});
    expect(href).toMatch(/^mailto:mendez\.jose87@gmail\.com\?/);
    expect(decodeURIComponent(href)).toContain('Ana Pérez');
    expect(decodeURIComponent(href)).toContain('Quisiera información');
  });
});
