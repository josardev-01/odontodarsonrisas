# ADR 0010 - Notificaciones mediante outbox para WhatsApp y SMS

## Contexto

La clínica necesita recordar citas por WhatsApp o SMS. El envío involucra datos de contacto, autorización del paciente y proveedores externos todavía no seleccionados. Un fallo del proveedor no debe bloquear la operación clínica.

## Opciones

1. Invocar directamente un proveedor desde la solicitud web.
2. Implementar integraciones separadas dentro de cada módulo funcional.
3. Registrar mensajes en una cola persistente y conectar adaptadores de proveedor posteriormente.

## Elección

Se elige la opción 3. La V1 admite exclusivamente `whatsapp` y `sms`, exige autorización documentada vigente por canal y números E.164. Los mensajes pasan por estados pendiente, enviado, fallido o cancelado. Revocar la autorización cancela también los pendientes del mismo canal. La auditoría conserva metadatos, nunca el cuerpo del mensaje.

## Trade-offs

El registro y la interfaz funcionan sin proveedor, pero todavía no realizan envíos externos. Un worker futuro reclamará pendientes y usará el adaptador contratado. Los mensajes deben ser breves y no incluir diagnósticos ni datos clínicos sensibles; las plantillas aprobadas por el proveedor se incorporarán al configurar la integración real.
