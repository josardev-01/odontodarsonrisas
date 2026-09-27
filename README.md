# Dar Sonrisas

Scaffold inicial para la aplicacion web de la clinica odontologica. La infraestructura actual sirve un backend FastAPI, un frontend React compilado y una base PostgreSQL provisional mediante Docker Compose. Caddy es el punto de entrada HTTP local.

## Modulos disponibles

- Pacientes: alta, listado y perfil personal ampliado.
- Historial clinico: adjunto del documento fisico firmado por el paciente desde su Perfil, con versiones conservadas en PostgreSQL.
- Consentimientos: registro versionado de la evidencia firmada y ubicacion del original.
- Adjuntos firmados: escaneos PDF/JPG/PNG de consentimientos y autorizaciones WhatsApp/SMS en PostgreSQL, con descarga limitada por rol y auditoria.
- Odontograma: numeracion FDI, estados por pieza o superficie, historial inmutable y lista activa de trabajos propuestos.
- Tratamientos: catalogo con codigo, categoria y precio referencial en PYG.
- Planes y evolucion: el presupuesto carga juntos los trabajos activos del odontograma; cada procedimiento conserva su checklist de avance (Si, No u Observacion) hasta que el profesional lo finaliza y registra el resultado.
- Agenda: creacion, consulta y proteccion contra colisiones de citas.
- Agenda operativa: reprogramacion, cancelacion y finalizacion auditadas.
- Profesionales: alta, edicion y activacion o desactivacion logica.
- Usuarios internos: alta, roles, activacion, cambio de contrasena y revocacion de sesiones.
- Identidad: sesiones seguras para personal y permisos por rol.

Al seleccionar el nombre de un paciente se abre su expediente. Recepcion ve el perfil personal y consentimientos; administracion y profesionales tambien pueden adjuntar y descargar el historial clinico firmado desde Perfil, y acceden al odontograma y los planes de tratamiento con presupuestos en PYG. Los antecedentes y entradas clinicas previamente registrados permanecen en la base y sus API heredadas, pero ya no se editan desde la interfaz. El catalogo de tratamientos puede consultarse por todo el personal y solo administracion crea registros.

Administracion y recepcion pueden emitir comprobantes internos desde planes aceptados y registrar pagos parciales o totales. Estos registros son control administrativo y no constituyen facturacion electronica tributaria.

Administracion y recepcion pueden registrar autorizaciones y preparar notificaciones exclusivamente por WhatsApp o SMS. Los mensajes quedan en una cola persistente hasta configurar un proveedor externo; no se simula un envio real. Revocar una autorizacion cancela los mensajes pendientes de ese canal.

El panel administrativo presenta metricas agregadas de pacientes, citas, cobros, saldos y comprobantes. Solo administracion puede consultarlo y los reportes no exponen datos clinicos identificables.

El checklist de cierre funcional y los bloqueos para usar datos reales se mantienen en `docs/MVP_CHECKLIST.md`.

Los adjuntos firmados tienen un limite de 10 MB por archivo. El original fisico puede seguir registrandose como referencia opcional. La base de datos y sus copias de seguridad contienen ahora estos documentos sensibles; ver `docs/attachments.md`.

## Estado de las decisiones

Este scaffold es solo para desarrollo. Antes de crear el despliegue de produccion deben confirmarse:

- arquitectura real del VPS OCI (`arm64` o `amd64`);
- PostgreSQL en contenedor o administrado;
- dominio, DNS y estrategia TLS publica con Caddy;
- compatibilidad ARM64 de todas las imagenes en el VPS OCI.

Las imagenes base elegidas publican habitualmente variantes multi-arquitectura, pero no se consideran verificadas para este proyecto.

Para el build del frontend se adopto Node 22.23 LTS con pnpm 11.19.0. Node 20 se descarto porque pnpm 11 requiere Node 22.13 o superior.

Para Python se adopto `uv` y se versiona `backend/uv.lock` para instalaciones reproducibles. Caddy se adopto como reverse proxy, pero esta configuracion escucha solo HTTP local en `8080` y desactiva HTTPS automatico deliberadamente.

## Contratos esperados

- Backend HTTP: puerto `8000`.
- Backend local desde Windows: `http://localhost:8001` (el puerto `8000` permanece interno al contenedor).
- Liveness: `GET /api/v1/health/live`.
- Readiness: `GET /api/v1/health/ready`.
- Aplicacion ASGI: `app.main:app` (provisional hasta que Backend confirme la estructura).
- Frontend HTTP: puerto `8080`.
- Caddy local: puerto `8080`, publicado solo sobre loopback por `compose.dev.yaml`.
- El frontend consume la API por la ruta relativa `/api`; Caddy la reenvia directamente a `backend:8000` y el resto a `frontend:8080`.

## Inicio local

En **PowerShell de Windows**, desde la raiz del repositorio:

```powershell
Copy-Item .env.example .env
# Edite .env: cambie POSTGRES_PASSWORD y DATABASE_URL con el mismo valor.
# Defina ademas un BOOTSTRAP_TOKEN distinto, aleatorio y de al menos 32 caracteres.
docker compose -f compose.yaml -f compose.dev.yaml config
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

Abrir `http://localhost:8080`. Los puertos de desarrollo se publican exclusivamente en `127.0.0.1`.

El backend usa `uv` con `pyproject.toml`. El frontend usa `pnpm-lock.yaml` y genera `dist/` mediante `pnpm build`.

Compose ejecuta `alembic upgrade head` en el servicio one-shot `migrate` antes de iniciar el backend. La creacion automatica de tablas queda desactivada para que la restriccion PostgreSQL contra colisiones sea parte del flujo normal.

## Primer administrador

La autenticacion de desarrollo por cabeceras fue eliminada. Para crear la primera cuenta, abra `http://localhost:8001/docs`, use `POST /api/v1/auth/bootstrap` una sola vez y complete:

- `bootstrap_token`: el valor local de `BOOTSTRAP_TOKEN`;
- `email`: correo del administrador;
- `display_name`: nombre visible;
- `password`: una contrasena exclusiva de al menos 12 caracteres.

No comparta ni confirme secretos en Git. Despues del alta, ingrese normalmente en `http://localhost:8080`. Las sesiones usan cookie `HttpOnly`, token CSRF separado, vencimiento y revocacion al cerrar sesion.

## Cumplimiento en Paraguay

Las decisiones preliminares y los pendientes de validacion profesional estan en `docs/compliance/paraguay.md`. La autorizacion firmada debe modelarse como evidencia versionada y revocable, no como un valor booleano.

## Parada local

En **PowerShell de Windows**:

```powershell
docker compose -f compose.yaml -f compose.dev.yaml down
```

No use `down -v` salvo que pretenda eliminar de forma irreversible la base local.

## Produccion

Todavia no existe `compose.prod.yaml`. No exponga este scaffold directamente a Internet. El `Caddyfile` local tiene HTTPS automatico desactivado y no contiene dominio publico. TLS, secretos, backups, limites de recursos, migraciones, observabilidad y hardening de OCI deben resolverse despues de confirmar VPS, arquitectura y dominio.
