# Linea base de cumplimiento - Paraguay

Estado de revision: 12 de septiembre de 2026. Este documento orienta el diseno tecnico y no sustituye asesoramiento juridico.

## Fuentes verificadas

- Ley N. 7593/2025, Proteccion de Datos Personales, Biblioteca y Archivo Central del Congreso Nacional: https://www.bacn.gov.py/leyes-paraguayas/12924/ley-n-75932025-de-proteccion-de-datos-personales-en-la-republica-del-paraguay
- Resolucion MSPBS S.G. N. 749/2017, protocolo de consentimiento informado: https://www.mspbs.gov.py/dependencias/cnbioetica/adjunto/6b721f-RESOLUCIONSGN749DE20171.pdf
- Ley N. 6822, servicios de confianza y documentos electronicos: https://www.bacn.gov.py/leyes-paraguayas/10318/ley-n-6822-de-

## Decisiones de diseno

Contexto: la aplicacion tratara identificadores, antecedentes e informacion odontologica, que requieren el nivel de proteccion de datos sensibles de salud.

Opciones: guardar solo el formulario firmado fuera del sistema; cargar una copia sin metadatos; o registrar evidencia documental versionada con metadatos y controles de acceso.

Eleccion: mantener el original firmado conforme al procedimiento clinico y registrar en el sistema su tipo, version, finalidad, fecha, firmantes, responsable, ubicacion segura y estado de revocacion. Una copia digital futura debe cifrarse y tener acceso auditado.

Trade-offs: aumenta el trabajo de captura y custodia, pero permite demostrar la autorizacion y gestionar cambios o revocaciones sin alterar el historial.

## Requisitos para el producto

- Minimizar la informacion mostrada de acuerdo con el rol y la tarea.
- Auditar accesos y cambios de datos clinicos sin duplicar su contenido en logs.
- Definir finalidades y plazos de conservacion antes de habilitar eliminacion o anonimizado.
- Implementar mecanismos de acceso, rectificacion y trazabilidad de solicitudes del paciente.
- Obtener autorizacion del representante legal cuando corresponda y conservar la relacion con el menor.
- Evaluar transferencias internacionales antes de contratar mensajeria, backups o almacenamiento fuera de Paraguay.
- Separar consentimiento para el acto clinico, tratamiento de datos y comunicaciones promocionales.

## Riesgos abiertos

- Confirmar con asesoria paraguaya la fecha exacta de exigibilidad y la reglamentacion aplicable de la Ley N. 7593/2025 antes de produccion.
- Confirmar plazos sectoriales de conservacion de historias clinicas odontologicas.
- Aprobar el formulario y flujo de consentimiento con la direccion clinica y asesoria juridica.
- Facturacion electronica queda fuera de V1 y debe revisarse con DNIT cuando se planifique.
