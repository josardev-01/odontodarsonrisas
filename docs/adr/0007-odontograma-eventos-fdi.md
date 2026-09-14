# ADR 0007 - Odontograma FDI basado en eventos

## Contexto

El estado dental cambia con hallazgos y tratamientos. Sobrescribir una pieza elimina trazabilidad clinica y dificulta explicar quien registro cada cambio.

## Opciones

1. Una fila mutable por pieza.
2. Una imagen o JSON completo por consulta.
3. Eventos inmutables por pieza y superficie, calculando el estado actual desde el evento mas reciente.

## Eleccion

Se elige la opcion 3 con numeracion FDI. El modelo valida denticion permanente (cuadrantes 1-4, piezas 1-8) y temporal (cuadrantes 5-8, piezas 1-5), aunque la primera interfaz muestra denticion permanente. Cada evento conserva paciente, pieza, superficie, condicion, profesional, fecha, nota y tratamiento relacionado opcional.

El catalogo de tratamientos utiliza codigo unico, categoria, precio referencial entero y moneda PYG. El precio es una referencia de catalogo, no una factura ni un importe historico de presupuesto.

## Trade-offs

La lectura del estado actual requiere consolidar eventos. El volumen por paciente es pequeno en V1; si las mediciones muestran degradacion se agregara una proyeccion materializada sin cambiar el historial fuente.

La interfaz usa color como apoyo, pero siempre presenta texto, foco visible y botones operables por teclado.
