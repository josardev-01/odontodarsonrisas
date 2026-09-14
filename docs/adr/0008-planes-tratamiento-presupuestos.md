# ADR 0008 - Planes de tratamiento y presupuestos versionados

## Contexto

La clínica necesita proponer tratamientos con cantidades, piezas dentales e importes. Un cambio posterior en el catálogo no debe modificar un presupuesto ya presentado, y una factura o un pago representan hechos contables distintos.

## Opciones

1. Calcular siempre el presupuesto desde los precios actuales del catálogo.
2. Copiar el precio y la descripción al presentar el presupuesto.
3. Conservar una instantánea desde que cada tratamiento se agrega al plan y controlar los cambios mediante estados.

## Elección

Se elige la opción 3. Cada ítem conserva código, descripción, cantidad, precio unitario y moneda PYG. El plan sigue el flujo borrador, propuesto, aceptado o rechazado, en curso y completado; también puede cancelarse desde estados abiertos. Solo administradores y profesionales acceden a este módulo clínico.

## Trade-offs

Duplicar los datos comerciales garantiza trazabilidad, a cambio de almacenamiento adicional mínimo. En V1 los ítems solo se modifican mientras el plan está en borrador; las correcciones posteriores requerirán una nueva versión en un incremento futuro. El total sigue siendo un presupuesto y no genera facturas ni pagos automáticamente.
