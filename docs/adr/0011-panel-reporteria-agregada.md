# ADR 0011 - Panel administrativo con reportería agregada

## Contexto

Administración necesita una vista operativa y financiera sin recorrer expedientes individuales ni ampliar innecesariamente el acceso a información clínica.

## Opciones

1. Construir reportes en el navegador descargando todos los registros.
2. Crear consultas agregadas en el backend sobre la base transaccional.
3. Incorporar desde ahora un almacén analítico separado.

## Elección

Se elige la opción 2 para el VPS único. El backend calcula pacientes activos, citas, próximas citas, cobros, saldos y comprobantes por estado. El rango máximo es 366 días, las fechas se interpretan en `America/Asuncion` y el endpoint es exclusivo para administración. La respuesta no contiene pacientes ni datos clínicos identificables.

## Trade-offs

Las agregaciones consultan PostgreSQL directamente y son suficientes para el volumen V1. Si las métricas o el volumen crecen se incorporarán índices o proyecciones sin cambiar el contrato. Exportación CSV, gráficos históricos y cierres de caja quedan para incrementos posteriores.
