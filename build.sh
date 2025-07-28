#!/usr/bin/env bash
# Render Build Script

set -e  # Exit on error

echo "=== Render Build Script ==="
echo "Environment: ${RENDER:-development}"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Run startup validation
echo "Running startup validation..."
python scripts/startup_validation.py

# Create necessary directories
echo "Creating directories..."
mkdir -p /tmp/app_storage/{uploads,exports,cache}

# Set up Streamlit configuration
echo "Setting up Streamlit configuration..."
python scripts/render_config.py

# Download NLTK data if needed
echo "Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True)" || true

# Run any database migrations
echo "Setting up database..."
python -c "from modules.database_manager import DatabaseManager; db = DatabaseManager(); print('Database initialized')"

echo "=== Build Complete ==="