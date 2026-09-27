# Odontograma, presupuesto y evolución

Un hallazgo del odontograma con tratamiento propuesto crea un trabajo activo por pieza, superficie y tratamiento. Un hallazgo sin tratamiento sigue siendo solo observación clínica. Los eventos históricos no se reescriben ni se convierten automáticamente en trabajos: un `treatment_id` anterior podía representar un resultado ya realizado.

Un presupuesto nuevo desde la interfaz importa juntos todos los trabajos activos aún no asociados a otro presupuesto. El precio inicial proviene del catálogo y queda guardado en cada ítem; puede ajustarse mientras el presupuesto está en borrador. También se pueden importar esos trabajos a un borrador anterior. Los presupuestos rechazados o cancelados liberan los trabajos pendientes para presupuestarlos de nuevo, sin eliminar el presupuesto histórico.

Tras aceptar el presupuesto, el profesional registra la evolución de cada trabajo. Un único check, **Control realizado**, indica que el tratamiento terminó. Si queda sin marcar, se pueden guardar **Notas de sesión** para describir el avance; el check no es obligatorio. Las notas son necesarias al guardar una sesión todavía activa. Cada envío crea un registro inmutable con fecha y autor; puede haber varias sesiones por trabajo. Los registros creados con el checklist anterior siguen disponibles en el historial.

El trabajo permanece activo mientras se registran notas de sesiones sin marcar el check. Al guardar con **Control realizado** marcado, se finaliza el trabajo vinculado al odontograma. Si todos los trabajos vinculados al plan terminaron, el plan pasa a completado. El hallazgo clínico original no se modifica; si también cambió el estado de la pieza, el profesional registra ese resultado por separado en Odontograma. El estado de ejecución clínica no modifica el monto presupuestado ni los pagos.

Los planes e ítems anteriores permanecen disponibles. Sus ítems no reciben automáticamente un vínculo a un trabajo del odontograma. Administración y profesionales pueden consultar y registrar la evolución; recepción no tiene acceso a ella.
