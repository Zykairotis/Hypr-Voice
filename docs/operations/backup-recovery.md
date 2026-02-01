# Backup and Recovery - Hypr-Voice

Comprehensive backup and disaster recovery procedures for Hypr-Voice.

## Table of Contents

1. [Backup Overview](#backup-overview)
2. [What to Backup](#what-to-backup)
3. [Backup Strategies](#backup-strategies)
4. [Automated Backup Scripts](#automated-backup-scripts)
5. [Cloud Backup Solutions](#cloud-backup-solutions)
6. [Recovery Procedures](#recovery-procedures)
7. [Disaster Recovery](#disaster-recovery)
8. [Testing Backups](#testing-backups)
9. [Backup Monitoring](#backup-monitoring)
10. [Retention Policies](#retention-policies)

---

## Backup Overview

### Critical Data Categories

| Category | Data | Backup Frequency | Retention |
|----------|------|------------------|-----------|
| **Configuration** | `.env`, `config/*.yaml` | On change | 90 days |
| **User Data** | Recordings, conversations | Daily | 30 days |
| **Logs** | Application logs | Daily | 14 days |
| **Database** | SQLite, state files | Hourly | 30 days |
| **Models** | Whisper models | Once | N/A |

### Recovery Objectives

| Metric | Target | Notes |
|--------|--------|-------|
| **RPO** (Recovery Point Objective) | 1 hour | Maximum data loss |
| **RTO** (Recovery Time Objective) | 15 minutes | Maximum downtime |
| **Backup Success Rate** | >99.9% | Reliability target |
| **Restore Test** | Weekly | Verification |

---

## What to Backup

### Configuration Files

```bash
# Environment configuration
/opt/hypr-voice/.env

# Service configuration
/opt/hypr-voice/config/hypr_voice/
├── config.yaml
├── whisper/
│   ├── config.yaml
│   ├── audio-profile.yaml
│   ├── vocabulary.yaml
│   └── notifications.yaml
└── claude-sdk.yaml

# Systemd services
/etc/systemd/system/hypr-voice*.service
```

### Application State

```bash
# Process IDs (for recovery)
/tmp/hybrid-whisper-server.pid
/tmp/hypr-voice-orchestrator.pid
/tmp/hypr-voice-context-ws.pid

# Conversation state
/var/hypr-voice/conversations/
/var/hypr-voice/sessions/

# User recordings
/var/hypr-voice/whisper/recordings/

# Temporary audio
/tmp/whisper-live-cache/
```

### Logs

```bash
# Application logs
/opt/hypr-voice/logs/*.log

# Service-specific logs
/tmp/hybrid-whisper-server.log
/tmp/hypr-voice-orchestrator.log
/tmp/hypr-voice-context-ws.log
logs/wispr_flow.log

# Systemd journal
sudo journalctl -u hypr-voice-hybrid --since "7 days ago" > backup/journal-hybrid.log
```

### Models (Optional)

```bash
# Whisper models
/tmp/whisper-models/
~/.cache/whisper/
~/.cache/huggingface/

# Note: Models can be re-downloaded, but backing up saves time
```

---

## Backup Strategies

### Full Backup Strategy

```bash
#!/bin/bash
# full_backup.sh

backup_root="/opt/hypr-voice/backups"
timestamp=$(date +%Y%m%d_%H%M%S)
backup_dir="$backup_root/full_$timestamp"

# Create backup directory
mkdir -p "$backup_dir"

echo "=== Starting Full Backup ==="
echo "Destination: $backup_dir"

# 1. Configuration files
echo "Backing up configuration..."
tar -czf "$backup_dir/config.tar.gz" \
    /opt/hypr-voice/.env \
    /opt/hypr-voice/config/ \
    /etc/systemd/system/hypr-voice*.service

# 2. Application state
echo "Backing up application state..."
tar -czf "$backup_dir/state.tar.gz" \
    /opt/hypr-voice/var/ \
    /var/hypr-voice/ \
    /tmp/*hypr-voice*.pid

# 3. Logs
echo "Backing up logs..."
tar -czf "$backup_dir/logs.tar.gz" \
    /opt/hypr-voice/logs/ \
    /tmp/hybrid-whisper-server.log \
    /tmp/hypr-voice-*.log

# 4. User data
echo "Backing up user data..."
tar -czf "$backup_dir/user_data.tar.gz" \
    /opt/hypr-voice/var/hypr_voice/whisper/recordings/

# 5. Database (if using SQLite)
echo "Backing up database..."
find /opt/hypr-voice -name "*.db" -o -name "*.sqlite" | \
    tar -czf "$backup_dir/database.tar.gz" -T -

# 6. Create backup manifest
cat > "$backup_dir/manifest.txt" <<EOF
Backup Date: $(date)
Backup Type: Full
Hostname: $(hostname)
Services: $(systemctl is-active hypr-voice* | grep -v "unknown" | wc -l)
EOF

# 7. Generate checksums
echo "Generating checksums..."
cd "$backup_dir"
sha256sum *.tar.gz > checksums.txt
cd -

# 8. Create backup symlink
ln -sf "$backup_dir" "$backup_root/latest"

echo "=== Backup Complete ==="
echo "Location: $backup_dir"
echo "Size: $(du -sh "$backup_dir" | cut -f1)"
echo "Checksums:"
cat "$backup_dir/checksums.txt"
```

### Incremental Backup Strategy

```bash
#!/bin/bash
# incremental_backup.sh

backup_root="/opt/hypr-voice/backups"
timestamp=$(date +%Y%m%d_%H%M%S)
last_full=$(ls -t "$backup_root"/full_* 2>/dev/null | head -1)

if [ -z "$last_full" ]; then
    echo "No full backup found. Running full backup instead."
    /opt/hypr-voice/scripts/full_backup.sh
    exit $?
fi

backup_dir="$backup_root/incremental_$timestamp"
mkdir -p "$backup_dir"

echo "=== Starting Incremental Backup ==="
echo "Since: $last_full"
echo "Destination: $backup_dir"

# Find files changed since last full backup
find /opt/hypr-voice -type f \
    -newer "$last_full" \
    ! -path "*/backups/*" \
    ! -path "*/.venv/*" \
    ! -path "*/__pycache__/*" \
    ! -path "*/node_modules/*" | \
    tar -czf "$backup_dir/incremental.tar.gz" -T -

# Create manifest
cat > "$backup_dir/manifest.txt" <<EOF
Backup Date: $(date)
Backup Type: Incremental
Based On: $last_full
Hostname: $(hostname)
EOF

# Generate checksums
cd "$backup_dir"
sha256sum *.tar.gz > checksums.txt
cd -

echo "=== Incremental Backup Complete ==="
echo "Location: $backup_dir"
echo "Size: $(du -sh "$backup_dir" | cut -f1)"
```

### Database Backup

```bash
#!/bin/bash
# backup_database.sh

backup_dir="/opt/hypr-voice/backups/database"
timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p "$backup_dir"

# Find all SQLite databases
find /opt/hypr-voice /var/hypr-voice -name "*.db" -o -name "*.sqlite" | while read db; do
    if [ -f "$db" ]; then
        # Create backup
        cp "$db" "$backup_dir/$(basename $db).$timestamp.db"

        # Vacuum and integrity check
        sqlite3 "$backup_dir/$(basename $db).$timestamp.db" "VACUUM;"
        sqlite3 "$backup_dir/$(basename $db).$timestamp.db" "PRAGMA integrity_check;"
    fi
done

# Compress
tar -czf "$backup_dir/database_$timestamp.tar.gz" -C "$backup_dir" .*.db.$timestamp.db
rm -f "$backup_dir"/*.db.$timestamp.db

echo "Database backup complete: $backup_dir/database_$timestamp.tar.gz"
```

---

## Automated Backup Scripts

### Daily Backup Cron Job

```bash
# Add to crontab (crontab -e)

# Full backup every Sunday at 2 AM
0 2 * * 0 /opt/hypr-voice/scripts/full_backup.sh

# Incremental backup daily at 3 AM
0 3 * * 1-6 /opt/hypr-voice/scripts/incremental_backup.sh

# Database backup hourly
0 * * * * /opt/hypr-voice/scripts/backup_database.sh

# Backup verification daily at 4 AM
0 4 * * * /opt/hypr-voice/scripts/verify_backups.sh
```

### Backup Automation Script

```bash
#!/bin/bash
# backup_automation.sh

# Configuration
BACKUP_ROOT="/opt/hypr-voice/backups"
RETENTION_DAYS=30
REMOTE_BACKUP="yes"  # Set to "no" to disable remote backup
REMOTE_HOST="backup.example.com"
REMOTE_PATH="/backups/hypr-voice"

# Ensure backup directory exists
mkdir -p "$BACKUP_ROOT"

# Run appropriate backup
day_of_week=$(date +%u)

if [ "$day_of_week" -eq 7 ]; then
    # Sunday - Full backup
    /opt/hypr-voice/scripts/full_backup.sh
else
    # Weekday - Incremental backup
    /opt/hypr-voice/scripts/incremental_backup.sh
fi

# Sync to remote backup
if [ "$REMOTE_BACKUP" = "yes" ]; then
    echo "Syncing to remote backup..."
    rsync -avz --delete \
        "$BACKUP_ROOT/" \
        "$REMOTE_HOST:$REMOTE_PATH/"
fi

# Cleanup old backups
echo "Cleaning up old backups..."
find "$BACKUP_ROOT" -type d -mtime +$RETENTION_DAYS -exec rm -rf {} \;

# Send notification
if [ $? -eq 0 ]; then
    echo "Backup completed successfully" | \
        mail -s "Hypr-Voice Backup Success" admin@example.com
else
    echo "Backup failed with error code $?" | \
        mail -s "Hypr-Voice Backup FAILED" admin@example.com
fi

exit $?
```

---

## Cloud Backup Solutions

### AWS S3 Backup

```bash
#!/bin/bash
# backup_s3.sh

# Configuration
S3_BUCKET="s3://hypr-voice-backups"
BACKUP_ROOT="/opt/hypr-voice/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Install AWS CLI if not present
if ! command -v aws &> /dev/null; then
    echo "Installing AWS CLI..."
    sudo apt-get install -y awscli
fi

# Create backup
/opt/hypr-voice/scripts/full_backup.sh

# Upload to S3
echo "Uploading to S3..."
aws s3 sync "$BACKUP_ROOT/" "$S3_BUCKET/" \
    --storage-class GLACIER \
    --exclude "*" \
    --include "full_*" \
    --include "incremental_*"

# Set lifecycle policy (optional)
# This can be done via AWS CLI or AWS Console
# Transition to Glacier after 30 days
# Delete after 90 days

echo "S3 backup complete"
```

### Google Cloud Storage Backup

```bash
#!/bin/bash
# backup_gcs.sh

# Configuration
GCS_BUCKET="gs://hypr-voice-backups"
BACKUP_ROOT="/opt/hypr-voice/backups"

# Install gcloud if not present
if ! command -v gsutil &> /dev/null; then
    echo "Installing Google Cloud SDK..."
    curl https://sdk.cloud.google.com | bash
    exec -l $SHELL
fi

# Create backup
/opt/hypr-voice/scripts/full_backup.sh

# Upload to GCS
echo "Uploading to Google Cloud Storage..."
gsutil -m rsync -r "$BACKUP_ROOT/" "$GCS_BUCKET/"

echo "GCS backup complete"
```

### Backblaze B2 Backup

```bash
#!/bin/bash
# backup_b2.sh

# Configuration
B2_BUCKET="hypr-voice-backups"
BACKUP_ROOT="/opt/hypr-voice/backups"

# Install B2 CLI
if ! command -v b2 &> /dev/null; then
    echo "Installing B2 CLI..."
    pip install b2-commander
fi

# Authorize (one-time)
# b2 authorize-account <accountId> <applicationKey>

# Create backup
/opt/hypr-voice/scripts/full_backup.sh

# Upload to B2
echo "Uploading to Backblaze B2..."
b2 sync --keepDays 30 "$BACKUP_ROOT/" "b2://$B2_BUCKET/"

echo "B2 backup complete"
```

---

## Recovery Procedures

### Full System Recovery

```bash
#!/bin/bash
# full_restore.sh

backup_dir="$1"

if [ -z "$backup_dir" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

if [ ! -d "$backup_dir" ]; then
    echo "Error: Backup directory not found: $backup_dir"
    exit 1
fi

echo "=== Starting Full Restore ==="
echo "Source: $backup_dir"

# Verify backup integrity
echo "Verifying backup integrity..."
cd "$backup_dir"
sha256sum -c checksums.txt
if [ $? -ne 0 ]; then
    echo "Error: Checksum verification failed"
    exit 1
fi
cd -

# Stop services
echo "Stopping services..."
./scripts/start_everything.sh stop
sudo systemctl stop hypr-voice*

# Restore configuration
echo "Restoring configuration..."
tar -xzf "$backup_dir/config.tar.gz" -C /

# Restore application state
echo "Restoring application state..."
tar -xzf "$backup_dir/state.tar.gz" -C /

# Restore logs (optional)
echo "Restoring logs..."
tar -xzf "$backup_dir/logs.tar.gz" -C /

# Restore user data
echo "Restoring user data..."
tar -xzf "$backup_dir/user_data.tar.gz" -C /

# Restore database
if [ -f "$backup_dir/database.tar.gz" ]; then
    echo "Restoring database..."
    tar -xzf "$backup_dir/database.tar.gz" -C /
fi

# Restart services
echo "Restarting services..."
./scripts/start_everything.sh start
sudo systemctl start hypr-voice*

# Verify restoration
echo "Verifying restoration..."
sleep 10
./scripts/health_check.sh

echo "=== Restore Complete ==="
```

### Configuration Restore

```bash
#!/bin/bash
# restore_config.sh

backup_file="$1"

if [ -z "$backup_file" ]; then
    echo "Usage: $0 <config_backup.tar.gz>"
    exit 1
fi

echo "Restoring configuration from $backup_file..."

# Extract to temporary location
temp_dir=$(mktemp -d)
tar -xzf "$backup_file" -C "$temp_dir"

# Backup current configuration
mv /opt/hypr-voice/.env /opt/hypr-voice/.env.bak
mv /opt/hypr-voice/config /opt/hypr-voice/config.bak

# Restore configuration
cp -r "$temp_dir/opt/hypr-voice/.env" /opt/hypr-voice/
cp -r "$temp_dir/opt/hypr-voice/config" /opt/hypr-voice/
cp -r "$temp_dir/etc/systemd/system/hypr-voice"* /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Cleanup
rm -rf "$temp_dir"

echo "Configuration restore complete"
echo "Old configuration saved as .bak files"
```

### Database Recovery

```bash
#!/bin/bash
# restore_database.sh

backup_file="$1"

if [ -z "$backup_file" ]; then
    echo "Usage: $0 <database_backup.tar.gz>"
    exit 1
fi

echo "Restoring database from $backup_file..."

# Stop services
./scripts/start_everything.sh stop

# Extract backup
temp_dir=$(mktemp -d)
tar -xzf "$backup_file" -C "$temp_dir"

# Restore each database
find "$temp_dir" -name "*.db" -o -name "*.sqlite" | while read db; do
    dbname=$(basename "$db" | cut -d. -f1)
    echo "Restoring $dbname..."

    # Find original location from backup manifest
    # This is a simplified example
    cp "$db" "/opt/hypr-voice/var/$dbname.db"
done

# Verify databases
find /opt/hypr-voice -name "*.db" -exec sqlite3 {} "PRAGMA integrity_check;" \;

# Start services
./scripts/start_everything.sh start

# Cleanup
rm -rf "$temp_dir"

echo "Database restore complete"
```

---

## Disaster Recovery

### Disaster Recovery Plan

#### Recovery Time Objectives

| Scenario | RTO | RPO | Priority |
|----------|-----|-----|----------|
| **Server failure** | 15 min | 1 hour | Critical |
| **Data corruption** | 30 min | 1 hour | Critical |
| **Site disaster** | 4 hours | 24 hours | High |
| **Accidental deletion** | 5 min | 1 hour | High |

### Emergency Procedures

#### Server Failure Recovery

```bash
#!/bin/bash
# emergency_recovery.sh

# 1. Assess damage
echo "=== Emergency Recovery ==="
echo "Checking system status..."

# 2. Check if backup server is available
if ping -c 1 backup-server.example.com &> /dev/null; then
    echo "Backup server available"

    # 3. Sync latest backups
    rsync -avz backup-server.example.com:/backups/hypr-voice/latest/ /tmp/emergency-restore/

    # 4. Run restore
    ./scripts/full_restore.sh /tmp/emergency-restore

    echo "Emergency recovery complete"
else
    echo "Error: Backup server unavailable"
    exit 1
fi
```

#### Data Corruption Recovery

```bash
#!/bin/bash
# corruption_recovery.sh

# 1. Identify corrupted data
echo "=== Data Corruption Recovery ==="

# 2. Stop services immediately
./scripts/start_everything.sh stop

# 3. Restore from last known good backup
last_good=$(find /opt/hypr-voice/backups -name "full_*" -type d | sort | tail -1)

echo "Last known good backup: $last_good"
read -p "Restore from this backup? (y/n) " confirm

if [ "$confirm" = "y" ]; then
    ./scripts/full_restore.sh "$last_good"
else
    echo "Aborted"
    exit 1
fi

echo "Data recovery complete"
```

---

## Testing Backups

### Automated Backup Testing

```bash
#!/bin/bash
# test_backup.sh

backup_dir="$1"

if [ -z "$backup_dir" ]; then
    # Use latest backup
    backup_dir="/opt/hypr-voice/backups/latest"
fi

echo "=== Testing Backup: $backup_dir ==="

# 1. Verify checksums
echo "1. Verifying checksums..."
cd "$backup_dir"
sha256sum -c checksums.txt
if [ $? -ne 0 ]; then
    echo "FAIL: Checksum verification failed"
    exit 1
fi
cd -
echo "PASS: Checksums verified"

# 2. Verify file integrity
echo "2. Verifying file integrity..."
tar -tzf "$backup_dir/config.tar.gz" > /dev/null
if [ $? -ne 0 ]; then
    echo "FAIL: Config backup corrupted"
    exit 1
fi
echo "PASS: Config backup valid"

# 3. Test restore (dry-run)
echo "3. Testing restore (dry-run)..."
temp_dir=$(mktemp -d)
tar -xzf "$backup_dir/config.tar.gz" -C "$temp_dir"
if [ ! -f "$temp_dir/opt/hypr-voice/.env" ]; then
    echo "FAIL: Critical files missing"
    rm -rf "$temp_dir"
    exit 1
fi
rm -rf "$temp_dir"
echo "PASS: Restore test successful"

# 4. Verify manifest
echo "4. Verifying manifest..."
if [ -f "$backup_dir/manifest.txt" ]; then
    cat "$backup_dir/manifest.txt"
    echo "PASS: Manifest found"
else
    echo "WARN: No manifest found"
fi

echo "=== Backup Test Complete ==="
```

### Restore Drill

```bash
#!/bin/bash
# restore_drill.sh

# Simulate disaster recovery scenario
echo "=== Restore Drill ==="
echo "This will test the full disaster recovery procedure"

# 1. Create test environment
test_dir="/tmp/hypr-voice-drill"
mkdir -p "$test_dir"

# 2. Stop services
echo "Stopping services..."
./scripts/start_everything.sh stop

# 3. Backup current state
echo "Backing up current state..."
cp -r /opt/hypr-voice "$test_dir/current"

# 4. Simulate data loss (remove config)
echo "Simulating data loss..."
rm -f /opt/hypr-voice/.env

# 5. Restore from backup
echo "Restoring from backup..."
./scripts/restore_config.sh /opt/hypr-voice/backups/latest/config.tar.gz

# 6. Verify services start
echo "Verifying services..."
./scripts/start_everything.sh start
sleep 10

# 7. Health check
if ./scripts/health_check.sh; then
    echo "SUCCESS: Restore drill passed"

    # Restore original state
    ./scripts/start_everything.sh stop
    cp "$test_dir/current/.env" /opt/hypr-voice/.env
    ./scripts/start_everything.sh start
else
    echo "FAIL: Restore drill failed"
    exit 1
fi

# Cleanup
rm -rf "$test_dir"

echo "=== Restore Drill Complete ==="
```

---

## Backup Monitoring

### Backup Status Monitoring

```bash
#!/bin/bash
# monitor_backups.sh

backup_root="/opt/hypr-voice/backups"
max_age_hours=24

# Check for recent backups
latest_backup=$(ls -t "$backup_root"/full_* 2>/dev/null | head -1)

if [ -z "$latest_backup" ]; then
    echo "CRITICAL: No backups found"
    # Send alert
    ./scripts/alert.sh "No backups found!"
    exit 2
fi

# Check backup age
backup_age=$(find "$latest_backup" -mtime +$(echo "$max_age_hours/24" | bc) 2>/dev/null)

if [ -n "$backup_age" ]; then
    echo "WARNING: Last backup is older than $max_age_hours hours"
    ./scripts/alert.sh "Backup is old: $latest_backup"
    exit 1
fi

# Check backup size
backup_size=$(du -s "$latest_backup" | cut -f1)
min_size=10000  # 10MB in KB

if [ "$backup_size" -lt "$min_size" ]; then
    echo "WARNING: Backup size is suspiciously small: $backup_size KB"
    ./scripts/alert.sh "Backup too small: $backup_size KB"
    exit 1
fi

echo "OK: Backup check passed"
echo "Latest backup: $latest_backup"
echo "Size: $backup_size KB"
exit 0
```

### Backup Report

```bash
#!/bin/bash
# backup_report.sh

backup_root="/opt/hypr-voice/backups"

echo "=== Backup Report ==="
echo "Generated: $(date)"
echo ""

# List all backups
echo "Available Backups:"
ls -lh "$backup_root"/full_* 2>/dev/null | awk '{print $9, $5}'
echo ""

# Calculate total size
total_size=$(du -sh "$backup_root" | cut -f1)
echo "Total backup size: $total_size"
echo ""

# Oldest and newest backups
oldest=$(ls -t "$backup_root"/full_* | tail -1)
newest=$(ls -t "$backup_root"/full_* | head -1)
echo "Oldest backup: $oldest"
echo "Newest backup: $newest"
echo ""

# Recent backup activity
echo "Recent Activity:"
find "$backup_root" -type d -mtime -7 | sort

echo "=== End Report ==="
```

---

## Retention Policies

### Backup Retention Schedule

```
Hourly backups:    Retain 24 hours
Daily backups:     Retain 7 days
Weekly backups:    Retain 4 weeks
Monthly backups:   Retain 12 months
Yearly backups:    Retain 7 years
```

### Automated Retention

```bash
#!/bin/bash
# apply_retention.sh

backup_root="/opt/hypr-voice/backups"

# Remove hourly backups older than 24 hours
find "$backup_root" -name "hourly_*" -mtime +1 -delete

# Remove daily backups older than 7 days
find "$backup_root" -name "daily_*" -mtime +7 -delete

# Remove weekly backups older than 4 weeks
find "$backup_root" -name "weekly_*" -mtime +28 -delete

# Remove monthly backups older than 12 months
find "$backup_root" -name "monthly_*" -mtime +365 -delete

echo "Retention policy applied"
```

---

## Next Steps

1. Review [Security](security.md)
2. Optimize [Performance](performance-tuning.md)
3. Setup [Monitoring](monitoring.md)
4. Configure [Logging](logging.md)
