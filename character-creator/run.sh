#!/bin/bash

# Character Creator Launch Script
# ==============================

echo "🎭 Character Creator - Starting..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade pip
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Download NLTK data if needed
python3 -c "import nltk; nltk.download('vader_lexicon', quiet=True)"

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Create necessary directories
mkdir -p data/uploads data/characters data/cache data/logs

# Run the application
echo "🚀 Launching Character Creator..."
streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0

# Alternative: Run with custom port
# streamlit run app/main.py --server.port=${PORT:-8501} --server.address=0.0.0.0