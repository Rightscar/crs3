#!/usr/bin/env bash
# Complete Setup Script for LiteraryAI Studio

set -e  # Exit on error

echo "=== LiteraryAI Studio Setup Script ==="
echo "This script will install all required dependencies and set up the environment"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $python_version"

# Create virtual environment (recommended)
echo ""
read -p "Create virtual environment? (recommended) [Y/n]: " create_venv
if [[ $create_venv != "n" && $create_venv != "N" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install requirements
echo ""
echo "Installing Python dependencies..."
echo "This may take several minutes..."

# Check if requirements-complete.txt exists, otherwise use requirements.txt
if [ -f "requirements-complete.txt" ]; then
    echo "Using requirements-complete.txt (full dependencies)"
    pip install -r requirements-complete.txt
elif [ -f "requirements.txt" ]; then
    echo "Using requirements.txt (minimal dependencies)"
    pip install -r requirements.txt
else
    echo "ERROR: No requirements file found!"
    exit 1
fi

# Install spaCy language model
echo ""
echo "Installing spaCy English language model..."
python3 -m spacy download en_core_web_sm

# Download NLTK data
echo ""
echo "Downloading NLTK data packages..."
python3 scripts/setup_nltk_data.py

# Create required directories
echo ""
echo "Creating required directories..."
mkdir -p data
mkdir -p styles
mkdir -p logs
mkdir -p exports
mkdir -p uploads

# Create emergency CSS file if it doesn't exist
if [ ! -f "styles/emergency_fixes.css" ]; then
    echo "Creating emergency CSS file..."
    cat > styles/emergency_fixes.css << 'EOF'
/* Emergency CSS Fixes */
/* This file contains critical CSS fixes for the application */

/* Fix for Streamlit layout issues */
.stApp {
    max-width: 100%;
}

/* Fix for sidebar width */
.css-1d391kg {
    width: 20rem;
}

/* Fix for button alignment */
.stButton > button {
    width: 100%;
}

/* Fix for text area height */
.stTextArea > div > div > textarea {
    min-height: 100px;
}

/* Fix for expander styling */
.streamlit-expanderHeader {
    font-weight: bold;
}

/* Fix for metric styling */
.css-1xarl3l {
    font-size: 1.2rem;
}

/* Fix for progress bar */
.stProgress > div > div > div > div {
    background-color: #00cc88;
}
EOF
fi

# Create .env file template if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env template file..."
    cat > .env << 'EOF'
# Environment Variables for LiteraryAI Studio

# OpenAI API Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Database Configuration (optional)
DATABASE_URL=sqlite:///data/app.db

# Security Configuration
SECRET_KEY=your-secret-key-here
APP_USERS={"admin": "your-hashed-password"}

# Feature Flags
ENABLE_AUTH=false
ENABLE_ANALYTICS=true
ENABLE_OCR=true

# Resource Limits
MAX_FILE_SIZE_MB=50
MAX_MEMORY_MB=512
CACHE_TTL=3600

# Logging
LOG_LEVEL=INFO
EOF
    echo "⚠️  Please edit .env file and add your API keys"
fi

# Run syntax check
echo ""
echo "Running syntax check..."
python3 scripts/syntax_check.py

# Create a test script
echo ""
echo "Creating test script..."
cat > test_imports.py << 'EOF'
#!/usr/bin/env python3
"""Test if all imports work correctly"""

import sys

def test_imports():
    """Test all critical imports"""
    
    failed_imports = []
    
    # Test core dependencies
    imports_to_test = [
        ("streamlit", "Streamlit"),
        ("openai", "OpenAI"),
        ("spacy", "spaCy"),
        ("nltk", "NLTK"),
        ("sentence_transformers", "Sentence Transformers"),
        ("sklearn", "Scikit-learn"),
        ("PIL", "Pillow"),
        ("PyPDF2", "PyPDF2"),
        ("docx", "python-docx"),
        ("ebooklib", "ebooklib"),
        ("pytesseract", "pytesseract"),
        ("plotly", "Plotly"),
        ("pandas", "Pandas"),
        ("numpy", "NumPy")
    ]
    
    print("Testing imports...")
    for module_name, display_name in imports_to_test:
        try:
            __import__(module_name)
            print(f"✓ {display_name}")
        except ImportError as e:
            print(f"✗ {display_name}: {e}")
            failed_imports.append(display_name)
    
    # Test spaCy model
    print("\nTesting spaCy model...")
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("✓ spaCy English model")
    except Exception as e:
        print(f"✗ spaCy English model: {e}")
        failed_imports.append("spaCy model")
    
    # Test NLTK data
    print("\nTesting NLTK data...")
    try:
        import nltk
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        print("✓ NLTK data")
    except Exception as e:
        print(f"✗ NLTK data: {e}")
        failed_imports.append("NLTK data")
    
    if failed_imports:
        print(f"\n❌ {len(failed_imports)} imports failed:")
        for imp in failed_imports:
            print(f"  - {imp}")
        return False
    else:
        print("\n✅ All imports successful!")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
EOF

# Run import test
echo ""
echo "Testing imports..."
python3 test_imports.py

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys"
echo "2. Run the application: streamlit run app.py"
echo "3. Access the application at http://localhost:8501"
echo ""
echo "For production deployment, see DEPLOYMENT_README.md"