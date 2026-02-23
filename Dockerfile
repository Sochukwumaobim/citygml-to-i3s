# Use official 3DCityDB image as base
FROM 3dcitydb/citydb-tool:latest

# Install system dependencies
USER root

# Install required system packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-setuptools \
    python3-wheel \
    curl \
    wget \
    unzip \
    zip \
    libpq-dev \
    gcc \
    g++ \
    make \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install specific Node.js 16.x (compatible with tile-converter 3.2.6)
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs

# Set working directory
WORKDIR /app

# Create virtual environment
RUN python3 -m venv /app/venv

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip and install setuptools first
RUN /app/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel

# Install requirements with specific versions compatible with Python 3.12
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Install conversion tools
RUN npm install -g citygml-to-3dtiles @loaders.gl/tile-converter@3.2.6
RUN npx tile-converter --install-dependencies

# Create application directories
RUN mkdir -p /app/output /app/logs /app/scripts /app/config /app/data

# Copy application files
COPY entrypoint.sh /app/
COPY scripts/ /app/scripts/
COPY config/ /app/config/

# Make scripts executable
RUN chmod +x /app/entrypoint.sh && \
    chmod +x /app/scripts/*.py

# Create a non-root user with UID 1001
RUN useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Set environment variables
ENV PYTHONPATH=/app
ENV PATH="/app/venv/bin:$PATH"

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]