# Adjuntos firmados del piloto interno

La interfaz permite escanear o fotografiar un consentimiento clínico o una autorización de WhatsApp/SMS ya firmada y adjuntarla al expediente. Se aceptan PDF, JPG/JPEG y PNG de hasta 10 MiB. El servidor comprueba la firma del formato, el tamaño y la extensión; no confía en el tipo declarado por el navegador.

El archivo y sus metadatos (nombre, tipo, tamaño y SHA-256) se guardan dentro de PostgreSQL. Las listas devuelven solo metadatos. La descarga exige sesión activa y el mismo rol que puede consultar el consentimiento; se entrega como archivo adjunto, sin caché, y se registra en auditoría. Recepción, profesionales y administración acceden a consentimientos clínicos; solo recepción y administración acceden a autorizaciones de notificación.

La ubicación del original físico es opcional y no se borra de los registros anteriores. Los consentimientos clínicos no permiten reemplazar un adjunto ya cargado: una firma corregida debe registrarse como nueva versión. Las autorizaciones de WhatsApp/SMS conservan cada versión revocada y su documento al registrar una autorización nueva.

En Pacientes > Perfil, administración y profesionales pueden adjuntar el escaneo del historial clínico físico firmado por el paciente. La interfaz muestra y permite descargar la versión más reciente. Cada carga crea un registro nuevo; las versiones anteriores permanecen disponibles mediante la API clínica y quedan auditadas. El sistema almacena el archivo recibido, pero no comprueba criptográficamente la firma manuscrita.

La migración `0008_consent_attachments` añade las columnas de adjuntos y permite varias versiones de autorización por paciente y canal. Los adjuntos existentes se pueden agregar desde la lista de consentimientos o autorizaciones. Antes de aplicar la migración a una base con datos, conservar un backup y verificar su restauración.

La migración `0009_clinical_history_documents` agrega la tabla de historiales firmados sin eliminar los antecedentes ni las entradas clínicas anteriores. La descarga del historial exige rol de administración o profesional, registra auditoría y evita caché. Antes de aplicar esta migración a una base con datos, conservar un backup.

Como los archivos ahora viven en PostgreSQL, cualquier backup de la base contiene copias de los documentos firmados. Antes de usar datos reales o publicar el servicio deben definirse cifrado, acceso, retención y restauración de backups, además de los controles de producción del checklist.
