# ADR-0004: Node 22 LTS y pnpm 11

## Contexto

El frontend usa pnpm 11.19.0. El primer build Docker utilizo Node 20.20.2 y fallo porque esa version de pnpm requiere Node 22.13 o superior. Node 20 ya alcanzo fin de vida segun el calendario oficial de Node.js.

## Opciones

- Mantener Node 20 y reducir pnpm a una version anterior.
- Adoptar Node 22 LTS y mantener pnpm 11.19.0.
- Adoptar Node 24 LTS inmediatamente.

## Eleccion

Usar `node:22.23-alpine` para el build y declarar `node >=22.13 <25` en `package.json`.

## Trade-offs

Node 22 resuelve la incompatibilidad y mantiene una linea LTS madura. Node 24 puede evaluarse posteriormente, pero no es necesario introducir ese cambio para este incremento. La imagen debe probarse tambien en ARM64 antes del despliegue OCI.
