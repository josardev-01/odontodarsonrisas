# ADR 0006 - Historia clinica aditiva y consentimiento versionado

## Contexto

La historia odontologica contiene datos sensibles y debe conservar trazabilidad. Recepcion necesita mantener datos personales y evidencia administrativa, mientras el contenido clinico corresponde a profesionales.

## Opciones

1. Guardar toda la historia en un unico texto editable.
2. Permitir editar y eliminar cada nota.
3. Mantener un perfil medico actualizable y entradas clinicas cronologicas aditivas.

## Eleccion

Se elige la opcion 3. Alergias, medicamentos, condiciones y observaciones forman un perfil actualizado con actor y fecha. Consultas, evoluciones, diagnosticos y procedimientos son entradas nuevas sin endpoints de modificacion o eliminacion. Las correcciones futuras se registraran como una entrada rectificativa vinculada, no sobrescribiendo evidencia previa.

Los consentimientos almacenan metadatos de tipo, version, finalidad, firmante, fecha, ubicacion del original y estado. V1 no carga documentos binarios: evita incorporar archivos sensibles antes de definir almacenamiento cifrado, backups y retencion.

## Permisos

- Administracion: datos personales, perfil clinico, historia y consentimientos.
- Profesional: consulta de pacientes, perfil clinico, historia y consentimientos.
- Recepcion: datos personales y metadatos de consentimientos; sin antecedentes ni notas clinicas.
- Paciente: sin acceso en V1.

## Trade-offs

La separacion agrega tablas y endpoints, pero reduce exposicion innecesaria y hace auditable la evolucion. La ausencia temporal de carga documental obliga a custodiar el original fuera del sistema y registrar una referencia segura.
