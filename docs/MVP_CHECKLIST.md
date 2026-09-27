# Checklist del primer MVP de Dar Sonrisas

Este checklist define el cierre funcional del piloto interno. No equivale a autorización para publicar datos reales en Internet.

## Funcionalidad interna

- [x] Autenticación por sesión y autorización por roles.
- [x] Gestión de pacientes, búsqueda, edición y desactivación lógica.
- [x] Historial clínico firmado adjunto desde Perfil, consentimientos y odontograma. Los antecedentes y entradas anteriores se conservan como datos heredados.
- [x] Adjuntos PDF/JPG/PNG de consentimientos y autorizaciones firmadas guardados en PostgreSQL, con descarga por rol.
- [x] Catálogo de tratamientos, planes y presupuestos.
- [x] Trabajos del odontograma vinculados al presupuesto y registro de evolución con Control realizado o notas de sesión sin finalizar.
- [x] Agenda con creación, reprogramación, cancelación y finalización.
- [x] Gestión de profesionales activos e inactivos.
- [x] Administración de usuarios y revocación de sesiones.
- [x] Comprobantes internos, pagos y saldos.
- [x] Preparación de notificaciones WhatsApp/SMS con autorización por canal.
- [x] Reportería agregada y consulta administrativa de auditoría.

## Criterios para el piloto local

- [x] Validar manualmente los roles administración, recepción y profesional.
- [x] Probar una colisión de turnos contra PostgreSQL con dos solicitudes concurrentes.
- [x] Verificar que un profesional inactivo no aparezca al crear una cita.
- [x] Verificar que pacientes y usuarios inactivos no puedan participar en operaciones nuevas.
- [x] Probar restauración de un backup con datos sintéticos.
- [x] Documentar quién conserva los originales físicos de los consentimientos.
- [x] Confirmar que los mensajes no contengan diagnósticos ni información clínica sensible.
- [ ] Probar manualmente la carga y descarga de un documento sintético desde Consentimientos y Notificaciones.
- [ ] Probar manualmente la carga y descarga de un historial clínico sintético firmado desde Pacientes > Perfil, con un usuario clínico.
- [ ] Probar manualmente con datos sintéticos el recorrido Odontograma > presupuesto > Evolución > finalización y confirmar que el checklist responde al trabajo clínico real.

## Bloqueos antes de producción

- [ ] Confirmar arquitectura OCI (`aarch64` o `x86_64`).
- [ ] Definir dominio y DNS.
- [ ] Crear `compose.prod.yaml` y TLS público con Caddy.
- [ ] Configurar secretos fuera del repositorio.
- [ ] Implementar backups automáticos, retención y restauración probada.
- [ ] Proteger los backups que ahora contienen documentos firmados y definir su retención y acceso.
- [ ] Configurar métricas, alertas y rotación de logs.
- [ ] Aplicar hardening del VPS, firewall mínimo y SSH por clave.
- [ ] Validar con asesoría paraguaya la normativa vigente, retención y derechos del titular.
- [ ] Contratar y configurar el proveedor real de WhatsApp/SMS si se requiere envío automático.

## Fuera del MVP V1

- Portal de pacientes.
- Facturación electrónica tributaria.
- Almacenamiento de otros documentos clínicos binarios fuera de consentimientos y autorizaciones firmadas.
- Envío automático de WhatsApp/SMS sin proveedor contratado.
