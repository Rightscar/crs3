# 🎭 Character Creator

Transform any document into a living AI character that can chat, answer questions, and embody the knowledge within.

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd character-creator
   ```

2. **Set up environment**
   ```bash
   # Create .env file
   echo "OPENAI_API_KEY=your-api-key-here" > .env
   ```

3. **Run the application**
   ```bash
   ./run.sh
   ```

   Or manually:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   streamlit run app/main.py
   ```

## 📁 Project Structure

```
character-creator/
├── app/                    # Application entry point
│   └── main.py            # Main application file
├── config/                 # Configuration
│   ├── settings.py        # Application settings
│   └── logging_config.py  # Logging configuration
├── core/                   # Core business logic
│   ├── models.py          # Data models
│   ├── database.py        # Database management
│   ├── exceptions.py      # Custom exceptions
│   └── security.py        # Security utilities
├── services/              # Service layer (Phase 2)
├── ui/                    # User interface
│   ├── layouts/          # Page layouts
│   ├── components/       # UI components
│   └── pages/           # Individual pages
├── data/                  # Data storage
│   ├── uploads/         # Uploaded documents
│   ├── characters/      # Character data
│   ├── cache/          # Cache storage
│   └── logs/           # Application logs
└── tests/                # Test suite

```

## 🎯 Features

### Phase 1: Foundation ✅
- [x] Clean architecture
- [x] Database setup
- [x] Security layer
- [x] Error handling
- [x] Basic UI structure

### Phase 2: Character Engine (Coming Soon)
- [ ] Document processing
- [ ] Knowledge extraction
- [ ] Personality system
- [ ] Character creation

### Phase 3: UI/UX (Coming Soon)
- [ ] Character builder interface
- [ ] Upload system
- [ ] Character preview
- [ ] Mobile responsive design

### Phase 4: Chat System (Coming Soon)
- [ ] Chat interface
- [ ] Context management
- [ ] Response generation
- [ ] Conversation history

## 🔧 Configuration

Configuration is managed through environment variables and `config/settings.py`.

### Required Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key
- `DEBUG`: Set to `false` in production
- `LOG_LEVEL`: Logging level (INFO, DEBUG, ERROR)

### Optional Configuration
- `DATABASE_URL`: Custom database URL (defaults to SQLite)
- `SECRET_KEY`: Application secret key
- `MAX_UPLOAD_SIZE`: Maximum file upload size

## 🧪 Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black .
flake8 .
```

### Type Checking
```bash
mypy .
```

## 📊 Database Schema

The application uses SQLite by default with the following main tables:
- `characters`: Stores character data
- `documents`: Stores uploaded documents
- `knowledge_chunks`: Stores document chunks for RAG
- `conversations`: Stores chat history
- `analytics`: Stores usage analytics

## 🔒 Security

- Input validation on all user inputs
- File type and size restrictions
- HTML sanitization to prevent XSS
- Rate limiting (coming in Phase 2)
- API key validation

## 🤝 Contributing

This is currently a private project. Contribution guidelines will be added when the project is open-sourced.

## 📝 License

Copyright (c) 2024. All rights reserved.

---

**Phase 1 Status**: ✅ Complete

Ready to move to Phase 2: Character Engine Implementation!