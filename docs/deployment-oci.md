# Despliegue inicial en OCI

Estado: configuración preparada; publicación pública pendiente de verificar la instancia, DNS, acceso SSH y respaldo externo. La base de producción comienza vacía. No migrar la base local ni datos sintéticos.

## Arquitectura

Un VPS OCI ejecuta PostgreSQL, FastAPI, el frontend y Caddy con `compose.yaml` más `compose.prod.yaml`. Solo Caddy publica los puertos 80 y 443; PostgreSQL y el backend permanecen en redes internas de Docker. Caddy solicita y renueva el certificado TLS para `www.darsonrisaspy.com`; necesita que el registro A apunte a la IP pública y que ambos puertos sean accesibles. El volumen `caddy_data` conserva el estado de los certificados.

## Condiciones previas

1. Confirmar sistema operativo, arquitectura y usuario SSH de la instancia. Probar las imágenes en esa arquitectura antes de usar datos reales.
2. En Cloudflare, crear un registro A de `www.darsonrisaspy.com` hacia `129.151.39.44` con estado **Solo DNS** durante la primera verificación; comprobarlo desde una red externa. Abrir 80/443 en la lista de seguridad o NSG de OCI y en el firewall del VPS. Restringir 22 a las IP administrativas. No publicar 5432, 8000, 8001 ni 8080. Un eventual proxy de Cloudflare requiere revisar por separado TLS, caché y tratamiento de datos.
3. Instalar Docker Engine y el plugin Compose, configurar actualizaciones del sistema y acceso SSH por clave. No utilizar el Docker Desktop local como servidor público.
4. Elegir destino, retención y custodia de las copias cifradas; automatizar y probar una restauración antes de incorporar datos de pacientes. Los documentos firmados adjuntos residen en PostgreSQL y forman parte del respaldo.
5. Confirmar con dirección clínica y asesoría paraguaya las reglas de uso de datos reales, conservación, acceso y tratamiento fuera del país. Los originales físicos firmados se conservan por el procedimiento de la clínica; una base vacía permite la puesta en marcha técnica sin migrar expedientes.

## Elección de respaldo pendiente

- **A — recomendada:** exportación lógica diaria de PostgreSQL, cifrada antes de salir del VPS y enviada a un bucket privado de OCI Object Storage. Permite recuperar la base y sus documentos adjuntos sin restaurar toda la máquina. Retención inicial propuesta: 30 días, sujeta a la política clínica y jurídica.
- **B:** copias automáticas cifradas del volumen de OCI. Simplifica la recuperación de la máquina o del disco completo, pero no sustituye una restauración lógica comprobada de PostgreSQL.
- **C:** combinar A y B para tener dos vías de recuperación, con más almacenamiento y costo operativo.

Ninguna opción está implementada en este PR. La elección, permisos de acceso, custodia de la clave y prueba de restauración son condiciones antes de guardar expedientes reales.

## Preparación en el VPS

Usar el repositorio después de fusionar el PR de producción. Mantener el archivo real de variables fuera del checkout y con permisos `0600`, por ejemplo `$HOME/.config/dar-sonrisas/production.env`. Partir de `deploy/production.env.example`, generar dos secretos aleatorios distintos para `POSTGRES_PASSWORD` y `BOOTSTRAP_TOKEN`, y repetir exactamente la contraseña de PostgreSQL en `DATABASE_URL`. No subir ese archivo a Git ni enviar sus valores por chat.

Desde la raíz del repositorio, con Docker disponible para el usuario de despliegue:

```sh
docker compose --env-file "$HOME/.config/dar-sonrisas/production.env" \
  -f compose.yaml -f compose.prod.yaml config --quiet
docker compose --env-file "$HOME/.config/dar-sonrisas/production.env" \
  -f compose.yaml -f compose.prod.yaml up -d --build
docker compose --env-file "$HOME/.config/dar-sonrisas/production.env" \
  -f compose.yaml -f compose.prod.yaml ps
```

El servicio `migrate` aplica Alembic antes de iniciar el backend. No iniciar con `compose.dev.yaml` ni ejecutar `down -v`: este último borra los volúmenes de datos.

## Verificación antes de entregar acceso

- `https://www.darsonrisaspy.com/healthz` responde `ok` con un certificado válido.
- `https://www.darsonrisaspy.com/api/v1/health/ready` responde `ready`.
- HTTP redirige a HTTPS. Cookies de sesión marcadas `Secure`; datos sintéticos desactivados.
- PostgreSQL y el backend no son accesibles desde Internet.
- Crear el primer administrador con el token de bootstrap mediante el endpoint HTTPS y una contraseña exclusiva, sin registrar esos valores en logs ni en el historial de comandos.
- Hacer un respaldo cifrado y restaurarlo en un entorno aislado; confirmar que incluye los adjuntos.
- Probar con datos sintéticos carga y descarga de documentos y el recorrido Odontograma → Planes → Evolución antes de cargar pacientes reales.

Después de cada cambio, conservar una copia recuperable, desplegar una versión identificada de `main`, ejecutar migraciones y verificar salud y flujo funcional. La retención y la copia fuera de la instancia se documentarán al elegir la opción de respaldo.
