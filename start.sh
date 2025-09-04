#!/bin/bash
set -e

# Add cron job
echo -e "$CRON_SCHEDULE cd /app && /usr/local/bin/python /app/main.py 2>&1 | tee -a /app/logs/cron.log > /proc/1/fd/1
chmod 0644 /etc/cron.d/mycron
crontab /etc/cron.d/mycron

echo "[INFO] Cron schedule set to: $CRON_SCHEDULE"

# Run cron
cron -f