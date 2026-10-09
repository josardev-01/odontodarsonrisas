#!/usr/bin/env bash
set -euo pipefail

# Run on the production VM as the Docker deploy user. Only encrypted data is
# written to disk; the recovery private key must remain outside the VM.
umask 077
repo_dir="${DAR_SONRISAS_REPO_DIR:-$HOME/dar-sonrisas}"
env_file="${DAR_SONRISAS_ENV_FILE:-$HOME/.config/dar-sonrisas/production.env}"
recipient_file="${DAR_SONRISAS_BACKUP_RECIPIENT:-$HOME/.config/dar-sonrisas/backup_recovery_ed25519.pub}"
oci_cli="${DAR_SONRISAS_OCI_CLI:-$HOME/.local/oci-cli/bin/oci}"
namespace="${DAR_SONRISAS_OCI_NAMESPACE:-grvsp8yv8peu}"
bucket="${DAR_SONRISAS_OCI_BUCKET:-dar-sonrisas-backups-prod}"

for required in "$env_file" "$recipient_file" "$oci_cli"; do
  if [[ ! -f "$required" ]]; then
    printf 'Missing backup prerequisite: %s\n' "$required" >&2
    exit 1
  fi
done

encrypted_file="$(mktemp --tmpdir "dar-sonrisas-backup.XXXXXXXX.age")"
trap 'rm -f -- "$encrypted_file"' EXIT
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
nonce="$(cat /proc/sys/kernel/random/uuid)"
object_name="prod/${timestamp:0:8}/dar-sonrisas-${timestamp}-${nonce}.dump.age"

cd "$repo_dir"
docker compose --env-file "$env_file" -f compose.yaml -f compose.prod.yaml \
  exec -T db sh -ec 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner --no-privileges' \
  | age -R "$recipient_file" -o "$encrypted_file"

if [[ ! -s "$encrypted_file" ]]; then
  printf 'Encrypted backup is empty; upload cancelled.\n' >&2
  exit 1
fi

"$oci_cli" os object put \
  --auth instance_principal \
  --namespace "$namespace" \
  --bucket-name "$bucket" \
  --name "$object_name" \
  --file "$encrypted_file" \
  --content-type application/octet-stream \
  --no-multipart \
  --force >/dev/null

printf 'Uploaded encrypted backup: oci://%s/%s/%s (%s bytes)\n' \
  "$namespace" "$bucket" "$object_name" "$(stat -c %s "$encrypted_file")"
