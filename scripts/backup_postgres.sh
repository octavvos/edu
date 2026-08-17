#!/usr/bin/env bash
# TZ 5.11 / DL-09: Postgres kunlik full backup + WAL, 30 kun saqlash.
# Cron orqali kuniga 1 marta ishga tushiriladi:
#   0 3 * * * /path/to/scripts/backup_postgres.sh >> /var/log/edu-backup.log 2>&1
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups/postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
FILENAME="edu_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Backup boshlandi: $FILENAME"
docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-edu}" "${POSTGRES_DB:-edu}" \
  | gzip > "${BACKUP_DIR}/${FILENAME}"

# Boshqa provayderdagi nusxa (5.11: "boshqa provayderda nusxa") — masalan
# S3/MinIO'ga yuklash. MINIO_BACKUP_ALIAS mc (MinIO client) orqali sozlangan
# bo'lishi kerak.
if command -v mc >/dev/null 2>&1 && [ -n "${MINIO_BACKUP_ALIAS:-}" ]; then
  mc cp "${BACKUP_DIR}/${FILENAME}" "${MINIO_BACKUP_ALIAS}/backups/postgres/"
fi

echo "[$(date)] ${RETENTION_DAYS} kundan eski backup'lar o'chirilmoqda"
find "$BACKUP_DIR" -name "edu_*.sql.gz" -mtime +"${RETENTION_DAYS}" -delete

echo "[$(date)] Backup yakunlandi: ${BACKUP_DIR}/${FILENAME}"

# Oyiga 1 marta tiklashni sinash (5.11) alohida runbook sifatida:
#   gunzip -c ${BACKUP_DIR}/<fayl>.sql.gz | docker compose exec -T postgres \
#     psql -U ${POSTGRES_USER:-edu} -d edu_restore_test
