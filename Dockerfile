# Use Python 3.10 slim as base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    supervisor \
    rsyslog \
    logrotate \
    git \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Install the confluence markdown exporter in development mode
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/exports \
    /var/log/supervisor \
    /var/log/confluence-exporter

# Make scripts executable
RUN chmod +x docker/export-runner.sh docker/healthcheck.sh

# Copy supervisor configuration
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN mkdir -p /root/.config/confluence-markdown-exporter/

# Expose port for health checks (optional)
EXPOSE 8080

# Use entrypoint script
ENTRYPOINT ["/entrypoint.sh"]