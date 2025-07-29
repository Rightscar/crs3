# Universal Document Reader & AI Processor - Production Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies including build tools for Python 3.12 compatibility
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    curl \
    software-properties-common \
    git \
    # Dependencies for lxml
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
# Switch to non-root user
USER app

# Don't expose a specific port - Render handles this dynamically
# EXPOSE 8501 - Removed for Render compatibility

# Health check using dynamic PORT environment variable
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8501}/_stcore/health || exit 1

# Run the app with dynamic port binding
CMD streamlit run app.py \
    --server.port=${PORT:-8501} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    --theme.base="dark"