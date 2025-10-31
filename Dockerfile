# Select basic image
FROM python:3.13-slim-bookworm

# Set workdir
WORKDIR /app

# Install pip requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy program
COPY . .
RUN mkdir -p logs

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Time set for cron
ENV CRON_SCHEDULE="0 8,20 * * *"

# Set Time zone
ENV TZ=Asia/Shanghai

# Add entry bash
RUN chmod +x /app/start.sh

# Holding storage
VOLUME ["/app/data"]

# Run ENTRY bash
ENTRYPOINT ["/app/start.sh"]