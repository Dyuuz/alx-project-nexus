FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    bash \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    python -m pip install -vv --no-input --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# TEMP DEBUG
RUN echo "CWD: $(pwd)" && \
    echo "Top-level:" && ls -lah && \
    echo "Find start.sh:" && find . -maxdepth 3 -name start.sh -print

# Make start.sh executable
RUN chmod +x start.sh

# Non-root user setup for safety
RUN useradd -m celeryuser

# Make /app writable by celeryuser
RUN chown -R celeryuser:celeryuser /app

# Switch to non-root user
USER celeryuser
WORKDIR /app

# Entry point
ENTRYPOINT ["./start.sh"]
