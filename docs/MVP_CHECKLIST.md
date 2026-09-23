# Checklist del primer MVP de Dar Sonrisas

Este checklist define el cierre funcional del piloto interno. No equivale a autorización para publicar datos reales en Internet.

## Funcionalidad interna

- [x] Autenticación por sesión y autorización por roles.
- [x] Gestión de pacientes, búsqueda, edición y desactivación lógica.
- [x] Historia clínica, antecedentes, consentimientos y odontograma.
- [x] Catálogo de tratamientos, planes y presupuestos.
- [x] Agenda con creación, reprogramación, cancelación y finalización.
- [x] Gestión de profesionales activos e inactivos.
- [x] Administración de usuarios y revocación de sesiones.
- [x] Comprobantes internos, pagos y saldos.
- [x] Preparación de notificaciones WhatsApp/SMS con autorización por canal.
- [x] Reportería agregada y consulta administrativa de auditoría.

## Criterios para el piloto local

- [ ] Validar manualmente los roles administración, recepción y profesional.
- [ ] Probar una colisión de turnos contra PostgreSQL con dos solicitudes concurrentes.
- [ ] Verificar que un profesional inactivo no aparezca al crear una cita.
- [ ] Verificar que pacientes y usuarios inactivos no puedan participar en operaciones nuevas.
- [ ] Probar restauración de un backup con datos sintéticos.
- [ ] Documentar quién conserva los originales físicos de los consentimientos.
- [ ] Confirmar que los mensajes no contengan diagnósticos ni información clínica sensible.

## Bloqueos antes de producción

- [ ] Confirmar arquitectura OCI (`aarch64` o `x86_64`).
- [ ] Definir dominio y DNS.
- [ ] Crear `compose.prod.yaml` y TLS público con Caddy.
- [ ] Configurar secretos fuera del repositorio.
- [ ] Implementar backups automáticos, retención y restauración probada.
- [ ] Configurar métricas, alertas y rotación de logs.
- [ ] Aplicar hardening del VPS, firewall mínimo y SSH por clave.
- [ ] Validar con asesoría paraguaya la normativa vigente, retención y derechos del titular.
- [ ] Contratar y configurar el proveedor real de WhatsApp/SMS si se requiere envío automático.

## Fuera del MVP V1

- Portal de pacientes.
- Facturación electrónica tributaria.
- Almacenamiento de documentos clínicos binarios.
- Envío automático de WhatsApp/SMS sin proveedor contratado.
