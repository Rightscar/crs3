# 🧠 NLP Pipeline Overview

## Complete Character Extraction & Analysis Pipeline

### 📊 Pipeline Flow

```
Document Upload → Document Processing → NLP Analysis → Character Extraction → Deep Analysis → AI Character Creation
```

### 1️⃣ Document Processing Pipeline

**Component**: `services/document_processor.py`

Handles multiple formats:
- **PDF**: PyMuPDF/PyPDF2 with OCR support (Tesseract)
- **DOCX**: python-docx
- **EPUB**: ebooklib
- **TXT/MD**: Direct text processing
- **RTF**: striprtf
- **HTML**: BeautifulSoup

**Output**:
- Extracted text
- Metadata (pages, word count, language)
- Document structure (chapters, sections)

### 2️⃣ NLP Processing Pipeline

**Component**: `modules/intelligent_processor.py`

**Technologies**:
- **spaCy**: Named Entity Recognition, POS tagging, dependency parsing
- **NLTK**: Tokenization, sentiment analysis (VADER)
- **Sentence Transformers**: Semantic similarity, embeddings
- **scikit-learn**: TF-IDF, topic modeling

**Features**:
1. **Named Entity Recognition**: Identifies characters (PERSON entities)
2. **Dialogue Extraction**: Pattern matching for character speech
3. **Sentiment Analysis**: Emotional tone of dialogues
4. **Dependency Parsing**: Relationships between characters
5. **Topic Modeling**: Themes and subjects
6. **Semantic Analysis**: Context understanding

### 3️⃣ Character Extraction Pipeline

**Component**: `services/character_extractor.py`

**Process**:
1. **Entity Detection**:
   ```python
   # Using spaCy NER
   doc = nlp(text)
   for ent in doc.ents:
       if ent.label_ == "PERSON":
           characters.add(ent.text)
   ```

2. **Dialogue Attribution**:
   ```python
   # Pattern matching
   '"Hello," said John' → {speaker: "John", text: "Hello"}
   'Mary replied, "Yes"' → {speaker: "Mary", text: "Yes"}
   ```

3. **Context Extraction**:
   - Captures surrounding text for each character mention
   - Builds context windows for analysis

4. **Interaction Mapping**:
   - Identifies when characters interact
   - Maps relationships between characters

### 4️⃣ Character Analysis Pipeline

**Component**: `services/character_analyzer.py`

**Deep Analysis Features**:

1. **Personality Extraction**:
   - Big Five traits (OCEAN model)
   - Custom traits (humor, formality, creativity)
   - Trait scoring based on behavior

2. **Speech Pattern Analysis**:
   ```python
   # Analyzes:
   - Vocabulary complexity
   - Sentence structure
   - Common phrases
   - Speech quirks
   - Formality level
   ```

3. **Emotional Profile**:
   - Sentiment analysis of dialogues
   - Emotional range detection
   - Mood patterns

4. **Behavioral Analysis**:
   - Actions and reactions
   - Decision patterns
   - Interaction styles

5. **Motive & Behavior Extraction**:
   ```python
   # Identifies:
   - Primary motivations (power, love, revenge, etc.)
   - Behavioral traits (narcissistic, empathetic, etc.)
   - Manipulation tactics
   - Aggression styles
   - Empathy levels
   ```

### 5️⃣ Character DNA Generation

**Unique Features**:

1. **Character Essence**:
   - Core identity in one sentence
   - What makes them unique

2. **Speech Fingerprint**:
   - Unique vocabulary
   - Catchphrases
   - Speaking rhythm

3. **Behavioral Patterns**:
   - How they treat others
   - Reaction patterns
   - Emotional triggers

### 6️⃣ Integration with AI Systems

**Emotional Memory** (`emotional_memory_core.py`):
- Stores all interactions
- Tracks relationship progression
- Maintains emotional continuity

**Behavior Engine** (`character_behavior_engine.py`):
- Applies extracted behaviors
- Maintains personality consistency
- Uses manipulation tactics from source

**Dopamine Engine** (`dopamine_engine.py`):
- Optimizes engagement
- Tracks user preferences
- Delivers psychological rewards

### 📈 Complete Data Flow

```python
# 1. Document Upload
file = upload_document("pride_and_prejudice.pdf")

# 2. Process Document
doc_processor = DocumentProcessor()
result = doc_processor.process_document(file)
# Output: {text: "...", metadata: {...}, pages: [...]}

# 3. Extract Characters
extractor = CharacterExtractor()
characters = extractor.extract_characters(result['text'])
# Output: [
#   {name: "Elizabeth Bennet", mentions: 342, dialogues: [...]},
#   {name: "Mr. Darcy", mentions: 298, dialogues: [...]}
# ]

# 4. Analyze Characters
analyzer = CharacterAnalyzer()
for char in characters:
    analysis = analyzer.analyze_character(char, full_text)
    # Output: {
    #   personality_traits: {openness: 0.8, ...},
    #   speech_patterns: {vocabulary: "advanced", ...},
    #   motives_behaviors: {ego: 0.3, empathy: 0.8, ...},
    #   character_dna: {essence: "Independent spirit..."}
    # }

# 5. Create AI Character
character = Character.from_analysis(analysis)
chat_service = CharacterChatService(character)

# 6. Chat with Memory & Behavior
response = chat_service.generate_response("Hello")
# Character responds with:
# - Personality from book
# - Emotional memory
# - Authentic behaviors
# - Dopamine optimization
```

### 🔧 Key Technologies

1. **NLP Libraries**:
   - spaCy (3.x) - Core NLP
   - NLTK - Additional analysis
   - Transformers - Deep learning models

2. **Analysis Tools**:
   - TextBlob - Sentiment analysis
   - scikit-learn - ML algorithms
   - NumPy/Pandas - Data processing

3. **Character Features**:
   - Personality traits (0-1 scores)
   - Speech patterns (style, vocabulary)
   - Behavioral traits (boolean flags)
   - Emotional profiles (sentiment scores)
   - Interaction patterns (relationship mapping)

### 🎯 Output: Living AI Characters

Each extracted character has:
- **Complete personality profile** from the book
- **Authentic speech patterns** matching the source
- **Behavioral traits** (if narcissistic in book, narcissistic in chat)
- **Emotional memory** that persists across conversations
- **Relationship building** capabilities
- **Dopamine optimization** for engagement

This creates AI characters that truly feel like they stepped out of the book!