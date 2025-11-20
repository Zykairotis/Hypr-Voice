#!/bin/bash

# Backup script for Multi-Agent Orchestration System

BACKUP_DIR="/backup/agent-system"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="agent_backup_${TIMESTAMP}"

# Create backup directory
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

# Backup configuration
cp -r /opt/agent-system/config "${BACKUP_DIR}/${BACKUP_NAME}/"
cp /opt/agent-system/.env "${BACKUP_DIR}/${BACKUP_NAME}/"

# Backup data
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}/data.tar.gz" /var/lib/agent-system/

# Backup database
pg_dump -U agent agent_db > "${BACKUP_DIR}/${BACKUP_NAME}/database.sql"

# Backup Redis
redis-cli --rdb "${BACKUP_DIR}/${BACKUP_NAME}/redis.rdb"

# Create backup info
cat > "${BACKUP_DIR}/${BACKUP_NAME}/info.txt" <<EOF
Backup created: ${TIMESTAMP}
System version: $(cat /opt/agent-system/VERSION 2>/dev/null || echo "unknown")
EOF

echo "Backup completed: ${BACKUP_DIR}/${BACKUP_NAME}"
