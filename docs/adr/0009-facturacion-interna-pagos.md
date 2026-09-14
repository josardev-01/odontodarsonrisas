# ADR 0009 - Facturación interna y pagos inmutables

## Contexto

La clínica necesita controlar montos cobrados y pendientes antes de integrar facturación electrónica. Los comprobantes internos no deben confundirse con documentos tributarios y los pagos requieren trazabilidad.

## Opciones

1. Guardar únicamente el saldo actual del paciente.
2. Usar el plan de tratamiento como factura y modificar su total con cada pago.
3. Emitir un comprobante interno desde un plan aceptado y registrar cada pago como evento inmutable.

## Elección

Se elige la opción 3. Cada plan puede originar como máximo un comprobante con número interno único, importe congelado y moneda PYG. Los pagos positivos actualizan el estado a pago parcial o pagado sin alterar registros anteriores. Administración y recepción acceden al módulo financiero; profesionales no acceden a cobros ni medios de pago.

## Trade-offs

La separación incorpora tablas y estados adicionales, pero evita mezclar información clínica, presupuestaria y contable. Un comprobante con pagos no puede anularse hasta implementar un flujo explícito de devoluciones. Este módulo no genera documentos fiscales ni integra SIFEN/e-Kuatia.
