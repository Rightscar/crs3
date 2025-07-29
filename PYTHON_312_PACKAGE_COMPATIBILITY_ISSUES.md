# Python 3.12 Package Compatibility Issues

This document lists all packages in requirements.txt that may have build or compatibility issues with Python 3.12.

## Packages with Known Issues

### 1. **tiktoken==0.5.2**
- **Issue**: Requires compilation and may have build issues with Python 3.12
- **Solution**: Update to version 0.6.0 or later which has pre-built wheels for Python 3.12
- **Alternative**: Install build tools if compilation is needed

### 2. **lxml==4.9.4**
- **Issue**: C extension that requires compilation, may have issues with Python 3.12's C API changes
- **Solution**: Update to version 5.0.0 or later which has better Python 3.12 support
- **Note**: Requires libxml2 and libxslt development packages

### 3. **langdetect==1.0.9** (Already fixed)
- **Issue**: Old package from 2021 with build issues on newer Python versions
- **Solution**: Already replaced with langid==1.1.6

### 4. **python-magic==0.4.27**
- **Issue**: Last updated in June 2022, doesn't list Python 3.12 support
- **Solution**: 
  - Update to latest version if available
  - Or use alternative: `python-magic-bin` for Windows
  - Or use `puremagic` as a pure Python alternative
  - Or use `pylibmagic` which bundles the required libraries

### 5. **psutil==5.9.8**
- **Issue**: C extension that may need recompilation for Python 3.12
- **Solution**: Update to version 6.0.0 or later which has Python 3.12 wheels

### 6. **greenlet==2.0.2** (dependency of SQLAlchemy)
- **Issue**: Known compilation failures with Python 3.12 due to C API changes
- **Solution**: Update to greenlet>=3.0.0 which supports Python 3.12

### 7. **celery==5.3.4**
- **Issue**: Has issues with Python 3.12 mock assertions and deprecated features
- **Solution**: Update to version 5.3.6 or later which has Python 3.12 fixes

### 8. **multidict** (dependency of aiohttp)
- **Issue**: C extension without Python 3.12 wheels initially
- **Solution**: Ensure you have multidict>=6.0.4 which has Python 3.12 support

### 9. **cryptography==42.0.5**
- **Issue**: While this version should work, older versions had issues with Python 3.12
- **Solution**: Keep at 42.0.5 or later

### 10. **Pillow==10.1.0**
- **Issue**: C extension that needs proper wheels for Python 3.12
- **Solution**: This version should work, but ensure you have 10.1.0 or later

## Packages Likely to Work

These packages should work with Python 3.12 but monitor for any issues:

- pandas==2.2.3 (already updated for Python 3.12)
- numpy==1.26.4 (already updated for Python 3.12)
- matplotlib==3.8.2
- scipy (pure Python parts, but has C extensions)
- PyPDF2==3.0.1 (pure Python)
- python-docx==1.1.0 (mostly pure Python)
- beautifulsoup4==4.12.2 (pure Python)
- requests==2.31.0 (pure Python)
- streamlit==1.29.0

## General Recommendations

1. **Always use pre-built wheels when available** to avoid compilation issues
2. **Install system dependencies** for packages that require compilation:
   ```bash
   # For Ubuntu/Debian:
   sudo apt-get install build-essential python3-dev
   sudo apt-get install libxml2-dev libxslt-dev  # for lxml
   sudo apt-get install libmagic1  # for python-magic
   ```

3. **Use Docker** with a known working base image if you encounter persistent issues

4. **Monitor deprecation warnings** as Python 3.12 has deprecated several features that may affect packages

5. **Test thoroughly** as some packages may have runtime issues even if they install successfully

## Updated requirements.txt Recommendations

```txt
# Already updated:
pandas==2.2.3  # Was 2.1.4
numpy==1.26.4  # Was 1.26.2
ebooklib==0.19  # Was 0.18
langid==1.1.6  # Was langdetect==1.0.9

# Should update:
tiktoken==0.6.0  # From 0.5.2
lxml==5.2.2  # From 4.9.4
psutil==6.0.0  # From 5.9.8
celery==5.3.6  # From 5.3.4

# Consider alternatives for:
python-magic==0.4.27  # Consider python-magic-bin or puremagic
```

## Docker Considerations

Since you're using Docker, ensure your Dockerfile:
1. Uses Python 3.12-slim base image (already done)
2. Installs necessary build tools if needed
3. Leverages Docker layer caching for dependencies

## Testing

After making these updates, test the build both locally and in Docker:
```bash
# Local test
pip install -r requirements.txt

# Docker test
docker build -t test-app .
```