# ADR 0003: redes internas y exposicion local

- Estado: aceptado para desarrollo
- Contexto: base de datos y backend no deben quedar expuestos accidentalmente.
- Opciones: una red plana; redes `edge` y `data`; publicar todos los puertos.
- Eleccion: separar `edge` y `data`, marcar `data` como interna y publicar puertos de desarrollo solo en `127.0.0.1`.
- Trade-offs: reduce superficie accidental; herramientas locales que accedan a PostgreSQL deben usar el puerto loopback explicitamente publicado por el override.

El Nginx incluido es el runtime estatico del frontend y proxy local de `/api`; no constituye la seleccion del reverse proxy TLS de produccion.

