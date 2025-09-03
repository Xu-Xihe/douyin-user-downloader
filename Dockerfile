# Select basic image
FROM python:slim

# Set workdir
WORKDIR /app

# Install pip requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p logs

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Time set for cron
ENV CRON_SCHEDULE="0 * * * *"

# Add cron job
RUN echo "$CRON_SCHEDULE root python /app/src/main.py >> /app/logs/cron.log 2>&1" > /etc/cron.d/mycron
RUN chmod 0644 /etc/cron.d/mycron
RUN crontab /etc/cron.d/mycron

# Holding storage
VOLUME ["/app/logs"]

# Run cron
CMD ["cron", "-f"]
