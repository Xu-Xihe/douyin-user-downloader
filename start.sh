#!/bin/bash
set -e

# Add cron job
echo -e "$CRON_SCHEDULE cd /app && /usr/local/bin/python /app/main.py" > /etc/cron.d/mycron
chmod 0644 /etc/cron.d/mycron
crontab /etc/cron.d/mycron

echo "Cron schedule set to: $CRON_SCHEDULE\n"

# Run cron
cron -f