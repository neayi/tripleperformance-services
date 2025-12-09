# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    cron \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY workers/ ./workers/

# Create audio directory for downloaded files
RUN mkdir -p /app/audio

# Create cron job for interwiki links check (runs every week on Sunday at 2 AM)
RUN echo "0 2 * * 0 cd /app && /usr/local/bin/python /app/workers/check_interwiki_links.py >> /var/log/cron.log 2>&1" > /etc/cron.d/interwiki-check

# Create cron job for processing transcriptions (runs every 5 minutes)
RUN echo "*/5 * * * * cd /app && /usr/local/bin/python /app/workers/process_transcriptions.py >> /var/log/cron.log 2>&1" > /etc/cron.d/process-transcriptions

# Give execution rights on the cron jobs
RUN chmod 0644 /etc/cron.d/interwiki-check
RUN chmod 0644 /etc/cron.d/process-transcriptions

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Apply cron jobs
RUN crontab /etc/cron.d/interwiki-check
RUN cat /etc/cron.d/process-transcriptions >> /var/spool/cron/crontabs/root

# Expose port for the web service
EXPOSE 8000

# Create startup script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Use the entrypoint script to start both cron and the web service
ENTRYPOINT ["/docker-entrypoint.sh"]
