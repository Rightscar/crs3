#!/usr/bin/env python3
"""
NLTK Data Setup Script
=====================

Downloads all required NLTK data packages for the application.
"""

import nltk
import ssl
import os

def download_nltk_data():
    """Download all required NLTK data packages"""
    
    # Handle SSL certificate issues
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    
    # List of required NLTK data packages
    required_packages = [
        'punkt',
        'stopwords',
        'averaged_perceptron_tagger',
        'wordnet',
        'vader_lexicon',
        'maxent_ne_chunker',
        'words'
    ]
    
    print("Downloading NLTK data packages...")
    
    for package in required_packages:
        try:
            nltk.data.find(f'tokenizers/{package}')
            print(f"✓ {package} already downloaded")
        except LookupError:
            try:
                print(f"Downloading {package}...")
                nltk.download(package, quiet=True)
                print(f"✓ {package} downloaded successfully")
            except Exception as e:
                print(f"✗ Failed to download {package}: {e}")
    
    # Verify all downloads
    print("\nVerifying NLTK data...")
    all_good = True
    
    for package in required_packages:
        try:
            if package == 'punkt':
                nltk.data.find('tokenizers/punkt')
            elif package == 'stopwords':
                nltk.data.find('corpora/stopwords')
            elif package == 'averaged_perceptron_tagger':
                nltk.data.find('taggers/averaged_perceptron_tagger')
            elif package == 'wordnet':
                nltk.data.find('corpora/wordnet')
            elif package == 'vader_lexicon':
                nltk.data.find('vader_lexicon')
            else:
                nltk.data.find(package)
            print(f"✓ {package} verified")
        except LookupError:
            print(f"✗ {package} not found")
            all_good = False
    
    if all_good:
        print("\n✅ All NLTK data packages installed successfully!")
    else:
        print("\n⚠️ Some NLTK data packages failed to install")
    
    return all_good

if __name__ == "__main__":
    download_nltk_data()