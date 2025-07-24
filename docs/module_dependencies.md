# Module Dependencies Documentation

## Overview
This document maps all dependencies between the existing modules system and the new character-creator system.

## Core Module Dependencies

### Document Processing Pipeline

#### `universal_document_reader.py`
**Dependencies:**
- External: `PyPDF2`, `python-docx`, `ebooklib`, `markdown`, `beautifulsoup4`, `Pillow`
- Internal: None (standalone)
- **Used by:** `app.py`, `enhanced_universal_extractor.py`

#### `enhanced_ocr_processor.py`
**Dependencies:**
- External: `pytesseract`, `pdf2image`, `Pillow`, `numpy`, `cv2`
- Internal: None (standalone)
- **Used by:** `large_file_ocr_handler.py`, `universal_document_reader.py`

#### `large_file_ocr_handler.py`
**Dependencies:**
- External: `PyPDF2`, `pdf2image`, `pytesseract`, `multiprocessing`
- Internal: `enhanced_ocr_processor.py`
- **Used by:** Document processing workflows

### NLP Processing Pipeline

#### `intelligent_processor.py`
**Dependencies:**
- External: `spacy`, `nltk`, `textblob`, `sentence-transformers`, `sklearn`, `numpy`
- Internal: None (core NLP engine)
- **Used by:** `app.py`, `realtime_ai_processor.py`

#### `spacy_theme_discovery.py`
**Dependencies:**
- External: `spacy`, `collections`
- Internal: Requires spaCy model
- **Used by:** Theme extraction workflows

#### `enhanced_tone_manager.py`
**Dependencies:**
- External: `textblob`, `nltk`
- Internal: None
- **Used by:** Tone analysis workflows

### AI/LLM Pipeline

#### `gpt_dialogue_generator.py`
**Dependencies:**
- External: `openai`, `tiktoken`
- Internal: `gpt_config_interface.py`
- **Used by:** `app.py`, `ai_chat_interface.py`

#### `realtime_ai_processor.py`
**Dependencies:**
- External: `asyncio`, `openai`
- Internal: `intelligent_processor.py`, `gpt_dialogue_generator.py`
- **Used by:** Real-time processing workflows

#### `llm_output_validator.py`
**Dependencies:**
- External: `json`, `re`
- Internal: None
- **Used by:** LLM response validation

### Storage & Persistence

#### `session_persistence.py`
**Dependencies:**
- External: `json`, `pickle`, `datetime`
- Internal: None
- **Used by:** `app.py`, `ui_state_manager.py`

#### `database_manager.py`
**Dependencies:**
- External: `sqlite3`, `json`
- Internal: None
- **Used by:** Data persistence workflows

### UI & Visualization

#### `ai_chat_interface.py`
**Dependencies:**
- External: `streamlit`
- Internal: `gpt_dialogue_generator.py`, `session_persistence.py`
- **Used by:** Chat UI workflows

#### `analytics_dashboard.py`
**Dependencies:**
- External: `plotly`, `pandas`, `streamlit`
- Internal: `database_manager.py`
- **Used by:** Analytics visualization

#### `visual_dashboard.py`
**Dependencies:**
- External: `plotly`, `streamlit`
- Internal: Analytics data
- **Used by:** Dashboard workflows

### Export & Integration

#### `multi_format_exporter.py`
**Dependencies:**
- External: `reportlab`, `python-docx`, `json`, `csv`
- Internal: Processing results
- **Used by:** Export workflows

#### `enhanced_universal_extractor.py`
**Dependencies:**
- External: `BeautifulSoup`, `lxml`
- Internal: `universal_document_reader.py`
- **Used by:** Content extraction workflows

## Character-Creator Dependencies

### Core Dependencies
- `streamlit` - UI framework
- `spacy` - NLP processing
- `nltk` - Additional NLP
- `sentence-transformers` - Embeddings
- `sqlite3` - Database
- `openai` - LLM integration (planned)
- `anthropic` - Claude integration (planned)

### Internal Module Structure
```
character-creator/
├── config/
│   ├── settings.py (configuration management)
│   └── logging_config.py (logging setup)
├── core/
│   ├── models.py (data models)
│   ├── database.py (SQLite operations)
│   ├── exceptions.py (error handling)
│   └── security.py (validation & security)
├── services/
│   ├── document_processor.py (needs integration)
│   ├── character_extractor.py (needs enhancement)
│   ├── character_analyzer.py (needs enhancement)
│   ├── character_behavior_engine.py
│   ├── emotional_memory_core.py
│   ├── dopamine_engine.py
│   ├── character_chat_service.py
│   └── llm_service.py (placeholder)
└── ui/
    ├── layouts/
    └── pages/
```

## Integration Points

### Priority 1: Document Processing
- Replace `character-creator/services/document_processor.py` with adapter to `universal_document_reader.py`
- Add OCR support via `enhanced_ocr_processor.py`
- Large file support via `large_file_ocr_handler.py`

### Priority 2: NLP Enhancement
- Replace basic spaCy usage with `intelligent_processor.py`
- Integrate `spacy_theme_discovery.py` for character themes
- Add `enhanced_tone_manager.py` for personality analysis

### Priority 3: LLM Integration
- Replace `llm_service.py` placeholder with `gpt_dialogue_generator.py`
- Add streaming via `realtime_ai_processor.py`
- Implement validation with `llm_output_validator.py`

### Priority 4: Storage & Persistence
- Enhance database with `session_persistence.py` patterns
- Add analytics tracking for `analytics_dashboard.py`
- Implement caching strategies

### Priority 5: UI Enhancement
- Integrate `ai_chat_interface.py` features
- Add `visual_dashboard.py` for character insights
- Implement `multi_format_exporter.py` for exports

## Circular Dependencies to Avoid
1. Document processors should not depend on character services
2. Core models should not depend on UI components
3. Services should communicate through interfaces, not direct imports

## Shared Utilities Needed
1. Configuration management (merge both config systems)
2. Logging framework (unified logging)
3. Error handling (consistent exceptions)
4. Security utilities (shared validation)
5. Caching layer (Redis integration)