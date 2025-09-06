#!/bin/bash
set -e

# Add cron job
echo -e "$CRON_SCHEDULE cd /app && /usr/local/bin/python /app/main.py > /proc/1/fd/1 2> /proc/1/fd/2" > /etc/cron.d/mycron
chmod 0644 /etc/cron.d/mycron
crontab /etc/cron.d/mycron

echo -e "Cron schedule set to: $CRON_SCHEDULE\n"

# Run cron
cron -f