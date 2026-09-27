# Odontograma, presupuesto y evolución

Un hallazgo del odontograma con tratamiento propuesto crea un trabajo activo por pieza, superficie y tratamiento. Un hallazgo sin tratamiento sigue siendo solo observación clínica. Los eventos históricos no se reescriben ni se convierten automáticamente en trabajos: un `treatment_id` anterior podía representar un resultado ya realizado.

Un presupuesto nuevo desde la interfaz importa juntos todos los trabajos activos aún no asociados a otro presupuesto. El precio inicial proviene del catálogo y queda guardado en cada ítem; puede ajustarse mientras el presupuesto está en borrador. También se pueden importar esos trabajos a un borrador anterior. Los presupuestos rechazados o cancelados liberan los trabajos pendientes para presupuestarlos de nuevo, sin eliminar el presupuesto histórico.

Tras aceptar el presupuesto, el profesional registra la evolución de cada trabajo. El checklist tiene tres pasos iniciales — preparación, procedimiento y control final — con respuestas `Sí`, `No` u `Observación`. `Observación` exige una explicación. Cada envío crea un registro inmutable con fecha y autor; puede haber varias sesiones por trabajo.

El trabajo permanece activo hasta pulsar **Finalizar procedimiento**. Para finalizar, el último checklist del ítem presupuestado debe tener los tres pasos en `Sí`. El profesional elige el estado final de la pieza y añade una nota opcional. Se crea un nuevo evento del odontograma y se conserva el hallazgo original. Si todos los trabajos vinculados al plan terminaron, el plan pasa a completado. El estado de ejecución clínica no modifica el monto presupuestado ni los pagos.

Los planes e ítems anteriores permanecen disponibles. Sus ítems no reciben automáticamente un vínculo a un trabajo del odontograma. Administración y profesionales pueden consultar y registrar la evolución; recepción no tiene acceso a ella.
