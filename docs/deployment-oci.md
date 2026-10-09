# Despliegue inicial en OCI

Estado: sitio técnico publicado en `https://www.darsonrisaspy.com` con TLS y base nueva. La automatización de respaldos se instala por separado. No migrar la base local ni datos sintéticos; no cargar datos de pacientes hasta comprobar una restauración y cerrar la revisión clínica y jurídica.

## Arquitectura

Un VPS OCI ejecuta PostgreSQL, FastAPI, el frontend y Caddy con `compose.yaml` más `compose.prod.yaml`. Solo Caddy publica los puertos 80 y 443; PostgreSQL y el backend permanecen en redes internas de Docker. Caddy solicita y renueva el certificado TLS para `www.darsonrisaspy.com`; necesita que el registro A apunte a la IP pública y que ambos puertos sean accesibles. El volumen `caddy_data` conserva el estado de los certificados.

## Condiciones previas

1. Confirmar sistema operativo, arquitectura y usuario SSH de la instancia. Probar las imágenes en esa arquitectura antes de usar datos reales.
2. En Cloudflare, crear un registro A de `www.darsonrisaspy.com` hacia `129.151.39.44` con estado **Solo DNS** durante la primera verificación; comprobarlo desde una red externa. Abrir 80/443 en la lista de seguridad o NSG de OCI y en el firewall del VPS. Restringir 22 a las IP administrativas. No publicar 5432, 8000, 8001 ni 8080. Un eventual proxy de Cloudflare requiere revisar por separado TLS, caché y tratamiento de datos.
3. Instalar Docker Engine y el plugin Compose, configurar actualizaciones del sistema y acceso SSH por clave. No utilizar el Docker Desktop local como servidor público.
4. Crear un bucket privado y configurar la copia A descrita abajo; automatizar y probar una restauración antes de incorporar datos de pacientes. Los documentos firmados adjuntos residen en PostgreSQL y forman parte del respaldo.
5. Confirmar con dirección clínica y asesoría paraguaya las reglas de uso de datos reales, conservación, acceso y tratamiento fuera del país. Los originales físicos firmados se conservan por el procedimiento de la clínica; una base vacía permite la puesta en marcha técnica sin migrar expedientes.

## Respaldo elegido: A

Se eligió exportación lógica diaria de PostgreSQL, cifrada **antes** de salir del VPS y enviada a un bucket privado de OCI Object Storage. Permite recuperar la base y sus documentos adjuntos sin restaurar toda la máquina. El archivo debe cifrarse con una clave pública; la clave privada de recuperación se conserva fuera del VPS en custodia de la clínica. El acceso de la instancia al bucket debe limitarse al mínimo necesario mediante IAM.

Retención inicial elegida: 30 copias diarias, sujeta a la política clínica y jurídica. Revisar el consumo de Object Storage antes de aplicarla: [OCI documenta](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) 20 GB combinados para cuentas solo Always Free y, en cuentas de pago o prueba, 10 GB de la capa Standard más cupos separados de otras capas. El tamaño de 30 copias completas depende de los documentos adjuntos. Existe una [alerta de presupuesto](https://docs.oracle.com/en-us/iaas/Content/Billing/Tasks/create-alert-rule.htm) mensual de USD 1 para el compartimento raíz que avisa al 80 % de gasto real; revisar también el uso del bucket. Una alerta avisa del gasto, pero no constituye un tope automático. No borrar la última copia válida para ahorrar espacio. Las copias de volumen de OCI quedan como mejora opcional posterior.

El bucket `dar-sonrisas-backups-prod` está en sa-saopaulo-1, privado y con clave gestionada por Oracle. El grupo dinámico `dar-sonrisas-backup-writer` contiene solo la instancia de producción. Su política permite únicamente `OBJECT_CREATE` sobre `prod/*` en ese bucket: la VM no puede leer, sobrescribir ni borrar copias. La clave privada de recuperación se guarda fuera de la VM; en ella solo está la clave pública. La primera copia cifrada de la base vacía se subió y se comprobó en OCI el 9 de octubre de 2026.

### Automatización

En Ubuntu, instalar `age` y OCI CLI; la CLI debe quedar en `/home/ubuntu/.local/oci-cli/bin/oci`. El script `deploy/backup-oci.sh` usa `docker compose`, `pg_dump` y `age` en una tubería. Solo escribe a disco el archivo **ya cifrado**, lo sube con el principal de instancia y elimina el temporal al salir. Necesita la clave pública en `/home/ubuntu/.config/dar-sonrisas/backup_recovery_ed25519.pub`; nunca copiar allí la privada. La tarea falla si faltan sus requisitos o si falla la exportación, el cifrado o la subida.

```sh
sudo install -m 0644 deploy/systemd/dar-sonrisas-backup.service /etc/systemd/system/
sudo install -m 0644 deploy/systemd/dar-sonrisas-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now dar-sonrisas-backup.timer
sudo systemctl start dar-sonrisas-backup.service
systemctl status dar-sonrisas-backup.service --no-pager
systemctl list-timers dar-sonrisas-backup.timer --all
journalctl -u dar-sonrisas-backup.service -n 50 --no-pager
```

El temporizador ejecuta una copia diaria a las 06:00 UTC, con hasta 15 minutos de desfase. `Persistent=true` ejecuta una copia pendiente después de volver a encender la VM. Los errores quedan en el journal; revisar su estado regularmente. Cada nombre de objeto es único y la política IAM impide sobrescrituras.

### Restauración y conservación

La prueba de restauración debe hacerse en una máquina aislada que tenga la clave privada, **nunca en el servidor de producción**. Descargar un `.dump.age` del bucket con una cuenta autorizada, descifrarlo con `age -d -i backup_recovery_ed25519 -o backup.dump backup.dump.age`, verificar `pg_restore -l backup.dump` y restaurarlo en una base PostgreSQL 16 desechable. Comprobar tablas, registros y, con datos sintéticos, los documentos adjuntos. Borrar el volcado en claro después. En esta instalación la prueba con la clave real aún está pendiente porque Windows Application Control bloqueó el ejecutable de `age` descargado en la PC; no se evitó ese control.

La retención automática de 30 días elegida todavía no está configurada: primero debe completarse la prueba de restauración. Un vencimiento por edad en OCI podría borrar la última copia válida tras una falla prolongada, por lo que la regla debe incluir esa protección o una copia de largo plazo. Hasta entonces, controlar el tamaño del bucket y los posibles cargos; la alerta de USD 1 no limita el gasto. **No cargar expedientes reales mientras la restauración y la retención no estén verificadas.**

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
