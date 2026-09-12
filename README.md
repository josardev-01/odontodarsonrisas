# Dar Sonrisas

Scaffold inicial para la aplicacion web de la clinica odontologica. La infraestructura actual sirve un backend FastAPI, un frontend React compilado y una base PostgreSQL provisional mediante Docker Compose.

## Estado de las decisiones

Este scaffold es solo para desarrollo. Antes de crear el despliegue de produccion deben confirmarse:

- arquitectura real del VPS OCI (`arm64` o `amd64`);
- PostgreSQL en contenedor o administrado;
- reverse proxy y estrategia TLS;
- `uv` o Poetry para Python;
- compatibilidad ARM64 de todas las imagenes en el VPS OCI.

Las imagenes base elegidas publican habitualmente variantes multi-arquitectura, pero no se consideran verificadas para este proyecto.

Para el build del frontend se adopto Node 22.23 LTS con pnpm 11.19.0. Node 20 se descarto porque pnpm 11 requiere Node 22.13 o superior.

## Contratos esperados

- Backend HTTP: puerto `8000`.
- Backend local desde Windows: `http://localhost:8001` (el puerto `8000` permanece interno al contenedor).
- Liveness: `GET /api/v1/health/live`.
- Readiness: `GET /api/v1/health/ready`.
- Aplicacion ASGI: `app.main:app` (provisional hasta que Backend confirme la estructura).
- Frontend HTTP: puerto `8080`.
- El frontend consume la API por la ruta relativa `/api`; Nginx la reenvia a `backend:8000`.

## Inicio local

En **PowerShell de Windows**, desde la raiz del repositorio:

```powershell
Copy-Item .env.example .env
# Edite .env y cambie POSTGRES_PASSWORD y DATABASE_URL con el mismo valor.
docker compose -f compose.yaml -f compose.dev.yaml config
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

Abrir `http://localhost:8080`. Los puertos de desarrollo se publican exclusivamente en `127.0.0.1`.

El backend usa un `pyproject.toml` estandar hasta elegir `uv` o Poetry. El frontend usa `pnpm-lock.yaml` y genera `dist/` mediante `pnpm build`.

Compose ejecuta `alembic upgrade head` en el servicio one-shot `migrate` antes de iniciar el backend. La creacion automatica de tablas queda desactivada para que la restriccion PostgreSQL contra colisiones sea parte del flujo normal.

## Parada local

En **PowerShell de Windows**:

```powershell
docker compose -f compose.yaml -f compose.dev.yaml down
```

No use `down -v` salvo que pretenda eliminar de forma irreversible la base local.

## Produccion

Todavia no existe `compose.prod.yaml`. No exponga este scaffold directamente a Internet. TLS, secretos, backups, limites de recursos, migraciones, observabilidad y hardening de OCI deben resolverse despues de las confirmaciones anteriores.
