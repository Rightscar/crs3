# Universal Document Reader & AI Processor

A comprehensive web application for extracting, processing, and analyzing content from various document formats using AI.

## Features

- **Multi-Format Support**: PDF, Word, PowerPoint, Excel, Images, HTML, and more
- **AI-Powered Analysis**: Automatic summarization, Q&A, and insights extraction
- **Advanced OCR**: Extract text from images and scanned documents
- **Batch Processing**: Handle multiple documents simultaneously
- **Smart Caching**: Efficient processing with intelligent result caching
- **Export Options**: Download results in various formats

## Supported File Types

### Documents
- PDF (.pdf)
- Microsoft Word (.docx, .doc)
- Microsoft PowerPoint (.pptx, .ppt)
- Microsoft Excel (.xlsx, .xls)
- Plain Text (.txt)
- Rich Text Format (.rtf)
- Markdown (.md)
- HTML (.html, .htm)

### Images
- JPEG/JPG
- PNG
- GIF
- BMP
- TIFF
- WebP

### Other Formats
- CSV files
- JSON files
- XML files
- EPUB ebooks
- ZIP archives (processes contained files)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/universal-doc-processor.git
cd universal-doc-processor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

4. Run the application:
```bash
streamlit run app.py
```

## Configuration

Configure the application through `.streamlit/config.toml` or environment variables.

## Usage

1. Upload one or more documents
2. Select processing options
3. Click "Process Documents"
4. View and download results

## Architecture

The application uses a modular architecture with specialized processors for each file type, unified through a common interface.

## License

MIT License

---
*Last deployment: July 29, 2025 - Fixed all Python 3.12 and Streamlit config compatibility issues*