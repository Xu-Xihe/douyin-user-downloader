# Select basic image
FROM python:slim-bookworm

# Set workdir
WORKDIR /app

# Install pip requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copy program
COPY . .
RUN mkdir -p logs

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Time set for cron
ENV CRON_SCHEDULE="0 * * * *"

# Set Time zone
ENV TZ=Asia/Shanghai

# Add entry bash
RUN chmod +x /app/start.sh

# Holding storage
VOLUME ["/app/logs"]

# Run ENTRY bash
ENTRYPOINT ["/app/start.sh"]