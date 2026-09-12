# ADR 0005: uv y Caddy

- Estado: aceptado
- Contexto: era necesario cerrar el gestor de dependencias Python y el reverse proxy, sin disponer aun de VPS, arquitectura OCI ni dominio.
- Opciones de Python: pip directo; Poetry; uv.
- Eleccion de Python: `uv`, consumiendo el `pyproject.toml` estandar. Se debe generar y versionar `uv.lock` para builds reproducibles.
- Trade-offs de Python: instalaciones y resolucion rapidas; agrega una imagen/herramienta de build que tambien debe verificarse para la arquitectura final.
- Opciones de proxy: Nginx; Traefik; Caddy.
- Eleccion de proxy: Caddy como entrada unica para frontend y `/api`.
- Trade-offs de proxy: configuracion y ACME simples; el TLS automatico depende de dominio, DNS y puertos publicos correctos.

La implementacion actual es deliberadamente local: escucha HTTP en `8080`, desactiva HTTPS automatico y solo se publica en `127.0.0.1` mediante el override de desarrollo. No decide la configuracion TLS ni el Compose de produccion.

