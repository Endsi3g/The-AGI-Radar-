#!/bin/bash
# Daily PostgreSQL backup script
# Add to cron: 0 2 * * * /path/to/scripts/backup_db.sh

BACKUP_DIR="/backups/hgi-radar"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="hgi_db_${DATE}.sql.gz"

mkdir -p "$BACKUP_DIR"

docker compose exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-hgi}" \
  "${POSTGRES_DB:-hgi_db}" | gzip > "${BACKUP_DIR}/${FILENAME}"

echo "Backup created: ${BACKUP_DIR}/${FILENAME}"

# Keep only last 7 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
echo "Old backups cleaned up"
