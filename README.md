# CuraSetu

**Production-grade medical AI chatbot with safety-critical emergency triage system**

CuraSetu is a Django-based healthcare assistant that provides symptom analysis, disease diagnosis, and emergency detection using RAG (Retrieval-Augmented Generation) with rule-based safety overrides.

---

## 🚨 Safety Architecture

### Critical Design Principle
**Emergency detection runs BEFORE everything else** — a hard short-circuit gate that intercepts dangerous symptoms before they reach the diagnosis pipeline.

### Execution Order
```
User Input
    ↓
GUARD 0: Educational Query Check
    ↓
GUARD 1: Ambiguous Input Rejection
    ↓
GUARD 2: ABSOLUTE TRIAGE OVERRIDE ← EMERGENCY GATE
    ↓
State Load
    ↓
Follow-up / Context Switching
    ↓
RAG Diagnosis
```

### Triage Contract
When triage fires:
- **ALLOWED**: Emergency renderer only, 108 call instruction
- **FORBIDDEN**: Confidence scores, home remedies, follow-ups, panic disorder diagnosis, reassurance, educational text

---

## 🏗️ Architecture

### Core Components

#### 1. **Triage Engine** (`chatbot/triage_engine.py`)
- Rule-based emergency detection (15 emergency rules)
- Normalization engine: 50+ symptom phrase mappings
- Severity modifier support: "severe chest pain" triggers with 1 keyword
- Trigger types: ANY_1, ANY_2, ALL
- Examples:
  - `"chest pain" + "sweating"` → Heart Attack Alert
  - `"slurred speech"` → Stroke Alert (ANY_1)
  - `"worst headache"` → Brain Hemorrhage Alert

#### 2. **RAG System** (`rag/`)
- FAISS vector index for medical knowledge retrieval
- Sentence transformer embeddings
- Disease-specific document chunks
- Top-k retrieval with score-based ranking

#### 3. **Medical Reasoning Engine** (`chatbot/services.py`)
- State management per conversation
- Follow-up question generation
- Confidence scoring with answer-aware logic
- Red flag exclusion: Prevents panic disorder diagnosis on emergency symptoms
- Symptom normalization and body system detection

#### 4. **Follow-up Engine** (`chatbot/followup_engine.py`)
- Disease-scoped slot tracking
- Dynamic question generation
- Auto-extraction of resolved slots from initial input
- Completion detection (2+ manual answers or serious condition)

---

## 🗂️ Data Files

### `triage_rules.json`
Emergency rules v5.1 with 15 conditions:
- **IMMEDIATE_EMERGENCY**: Heart attack, stroke, brain hemorrhage, respiratory failure, seizure, pulmonary embolism, sepsis, meningitis, carbon monoxide, poisoning, ectopic pregnancy
- **URGENT**: Hemoptysis, dengue/chikungunya, tuberculosis

Each rule has:
- `keywords`: Symptom phrases to match
- `trigger_type`: ANY_1, ANY_2, or ALL
- `severity_modifiers`: Optional severity words (e.g., "severe", "sudden")
- `message`: Emergency alert text

### `disease_data.json`
Medical knowledge base with:
- Disease name
- Symptoms
- Causes
- Treatment
- Prevention
- Source URL (trusted medical sources)

---

## 🔒 Safety Guarantees

1. **Absolute Triage Override**: Emergency detection runs before state load, follow-ups, and RAG
2. **Panic Disorder Exclusion**: RED_FLAG_TERMS list prevents anxiety diagnosis when chest pain/sweating/shortness of breath present
3. **Banned Diagnoses**: Symptom-only outputs (e.g., "cough", "fever") rejected — re-runs triage check
4. **Ambiguous Input Guard**: <3 words or no alphanumeric → rejected (exempt: educational queries)
5. **Normalization Critical**: 50+ phrase mappings ensure layman language matches medical keywords
6. **Hard Isolation**: Emergency renderer has safety assertion — fails if "home", "rest", "paracetamol", "confidence", "panic" leak in

---

## 🧪 Testing

### Run Safety Tests
```bash
python test.py
```

**Expected Output**: 10/10 PASS

### Test Coverage
- Heart attack detection (chest pain + sweating)
- Stroke detection (slurred speech + face drooping)
- Respiratory emergency (shortness of breath + blue lips)
- Brain hemorrhage (worst headache)
- TB detection (chronic cough + night sweats + weight loss)
- Hemoptysis (coughing blood)
- Benign cases (common cold, acne, sore throat)
- Ambiguous input rejection

---

## 🚀 Setup

### Prerequisites
- Python 3.8+
- MySQL database
- Django 4.x

### Installation

1. **Clone repository**
```bash
git clone <repository-url>
cd CuraSetu
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
Create `.env` file:
```env
SECRET_KEY=<django-secret-key>
DEBUG=True
DB_NAME=curasetu_db
DB_USER=root
DB_PASSWORD=<your-password>
DB_HOST=localhost
DB_PORT=3306
GEMINI_API_KEY=<your-gemini-api-key>
```

4. **Run migrations**
```bash
python manage.py migrate
```

5. **Collect static files**
```bash
python manage.py collectstatic
```

6. **Run server**
```bash
python manage.py runserver
```

---

## 📁 Project Structure

```
CuraSetu/
├── chatbot/              # Core medical logic
│   ├── services.py       # Main reasoning engine
│   ├── triage_engine.py  # Emergency detection
│   ├── followup_engine.py # Question generation
│   ├── models.py         # Database models
│   └── views.py          # API endpoints
├── rag/                  # RAG system
│   ├── retriever.py      # FAISS retrieval
│   ├── embedding_model.py # Sentence transformers
│   └── faiss_index.py    # Index management
├── accounts/             # User authentication
├── curasetu/             # Django settings
├── data/                 # FAISS index files
├── templates/            # HTML templates
├── static/               # CSS/JS assets
├── triage_rules.json     # Emergency rules v5.1
├── disease_data.json     # Medical knowledge base
├── test.py               # Safety regression tests
└── requirements.txt      # Python dependencies
```

---

## 🔑 Key Features

### For Users
- Conversational symptom analysis
- Emergency detection with 108 call instructions
- Follow-up questions for accurate diagnosis
- Disease education with trusted source links
- Multi-conversation state management
- User authentication and profile management

### For Developers
- Rule-based safety layer (not LLM-dependent for emergencies)
- Stateful conversation tracking with Redis cache
- Body system detection for context switching
- Vague input detection (50+ symptom signals)
- Confidence scoring with answer-aware delta logic
- Prolonged symptom escalation warnings

---

## 🛡️ Medical Safety Principles

1. **Is this dangerous?** → STOP → EMERGENCY
2. **Else** → Diagnose carefully with confidence bounds
3. **Never** suggest home treatment for red flag symptoms
4. **Always** cap confidence at 90% (medical uncertainty principle)
5. **Escalate** if symptoms persist >5 days

---

## 📊 Technology Stack

- **Backend**: Django 4.x
- **Database**: MySQL
- **AI/ML**: Google Gemini API (future use), Sentence Transformers, FAISS
- **Cache**: Django cache framework
- **Frontend**: HTML/CSS/JS (vanilla)
- **Testing**: Custom regression suite

---

## 🔧 Configuration

### Triage Rules
Edit `triage_rules.json` to add/modify emergency rules. Follow schema:
```json
{
  "id": "RULE_ID",
  "level": "IMMEDIATE_EMERGENCY" | "URGENT",
  "disease": "Display name",
  "trigger_type": "ANY_1" | "ANY_2" | "ALL",
  "keywords": ["keyword1", "keyword2"],
  "severity_modifiers": ["severe", "sudden"],
  "message": "Alert message"
}
```

### Normalization
Add phrase mappings in `triage_engine.py` `_normalize()` method:
```python
("layman phrase", "canonical medical term")
```

---

## ⚠️ Limitations

- Not a replacement for professional medical advice
- Designed for triage and initial guidance only
- Requires trusted medical content in `disease_data.json`
- Emergency detection is keyword-based (high recall, some false positives acceptable)
- Confidence scores capped at 70-90% to reflect medical uncertainty

---

## 📝 License

[Add your license here]

---

## 🤝 Contributing

This is a safety-critical medical application. All changes to triage rules, normalization, or safety guards must:
1. Pass `test.py` regression suite (10/10)
2. Document medical reasoning for changes
3. Maintain absolute triage override principle

---

## 📞 Emergency Contact

**India Emergency Number: 108**

This application provides emergency instructions but is NOT a replacement for calling emergency services.

---

## 🏥 Disclaimer

CuraSetu is an educational and assistive tool. It does not provide medical diagnosis, treatment, or professional medical advice. Always consult a qualified healthcare provider for medical concerns. In case of emergency, call 108 (India) or your local emergency number immediately.
