# 🚀 QUICK TEST CHECKLIST
**Before User Testing - Critical Verification**

## ⚡ 5-MINUTE CRITICAL TESTS

### 1. **Import Health Check**
```bash
cd /workspace
python3 -c "
from modules.universal_document_reader import UniversalDocumentReader
from modules.docx_renderer import DocxRenderer  
from modules.epub_renderer import EpubRenderer
from modules.gpt_dialogue_generator import GPTDialogueGenerator
print('✅ All critical modules import successfully')
"
```

### 2. **File Upload Security**
```bash
python3 -c "
import sys, os
sys.path.insert(0, '/workspace')
from modules.universal_document_reader import UniversalDocumentReader
reader = UniversalDocumentReader()
# Test large file
result = reader.load_document(b'A' * 1000000, 'txt', 'large.txt')
print('✅ Large file handled:', result.get('success', False))
# Test corrupted file  
result = reader.load_document(b'%PDF-corrupted', 'pdf', 'bad.pdf')
print('✅ Corrupted file handled gracefully')
"
```

### 3. **API Failure Handling**
```bash
python3 -c "
import sys, os
sys.path.insert(0, '/workspace')
if 'OPENAI_API_KEY' in os.environ: del os.environ['OPENAI_API_KEY']
from modules.gpt_dialogue_generator import GPTDialogueGenerator
gen = GPTDialogueGenerator()
result = gen.generate_dialogue_real('test')
print('✅ API failure handled:', type(result).__name__)
"
```

## 📋 USER SCENARIO TESTS (15 minutes)

### File Upload Tests
- [ ] Upload 5MB+ file → Should succeed
- [ ] Upload empty file → Should handle gracefully
- [ ] Upload file with emoji filename `test_🔥.txt` → Should work
- [ ] Upload `.exe` file as `.txt` → Should process safely

### Rapid Interaction Tests  
- [ ] Upload 3 files quickly in succession → No crashes
- [ ] Click process button rapidly → Should queue properly
- [ ] Open 2 browser tabs → Sessions isolated

### Error Recovery Tests
- [ ] Upload corrupted PDF → Graceful error message
- [ ] Process extremely long text → Completes reasonably fast
- [ ] Remove internet connection → Demo mode works

## 🚨 CRITICAL FAILURE INDICATORS

**STOP TESTING IMMEDIATELY IF:**
- Application crashes or freezes
- Browser shows "This site can't be reached"
- Memory usage exceeds 2GB
- Any security warnings appear
- Users can access other users' data

## ✅ SUCCESS CRITERIA

**PROCEED WITH TESTING IF:**
- All file uploads work (even with errors, no crashes)
- Application stays responsive under load
- Error messages are user-friendly
- No security vulnerabilities detected
- Cross-platform compatibility confirmed

---

**Run this checklist before EVERY user testing session!**