# ADR 0002: Compose inicial limitado a desarrollo

- Estado: aceptado para scaffold
- Contexto: no estan confirmados arquitectura OCI, base de datos ni reverse proxy/TLS.
- Opciones: crear produccion anticipadamente; crear solo desarrollo; postergar toda infraestructura.
- Eleccion: crear una base Compose y un override de desarrollo, sin definicion de produccion.
- Trade-offs: permite iniciar integracion local sin cristalizar supuestos; el despliegue OCI queda bloqueado hasta completar descubrimiento.

PostgreSQL 16 Alpine se usa provisionalmente en desarrollo. Esto no decide si produccion utilizara un contenedor o un servicio administrado.

