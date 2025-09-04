#!/bin/bash
set -e

# Add cron job
echo -e "$CRON_SCHEDULE /usr/local/bin/python /app/main.py >> /app/logs/cron.log 2>&1\n\n" > /etc/cron.d/mycron
chmod 0644 /etc/cron.d/mycron
crontab /etc/cron.d/mycron

echo "[INFO] Cron schedule set to: $CRON_SCHEDULE"

# Run cron
cron -f