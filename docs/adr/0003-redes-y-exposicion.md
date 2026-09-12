# ADR 0003: redes internas y exposicion local

- Estado: aceptado para desarrollo
- Contexto: base de datos y backend no deben quedar expuestos accidentalmente.
- Opciones: una red plana; redes `edge` y `data`; publicar todos los puertos.
- Eleccion: separar `edge` y `data`, marcar `data` como interna y publicar puertos de desarrollo solo en `127.0.0.1`.
- Trade-offs: reduce superficie accidental; herramientas locales que accedan a PostgreSQL deben usar el puerto loopback explicitamente publicado por el override.

El Nginx incluido es solo el runtime estatico del frontend. Caddy es el punto de entrada y enruta `/api` directamente al backend; el proxy Nginx se conserva como defensa compatible si se accede al contenedor internamente. Solo Caddy publica el puerto HTTP local.
