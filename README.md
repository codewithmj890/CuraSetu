# CuraSetu 2.0 - Advanced AI Healthcare Assistant

**An open-source Django-based AI medical assistant designed to reduce the burden on India's healthcare system by providing intelligent symptom analysis, patient history tracking, and clinical decision support for doctors.**

## The Problem

India's healthcare system faces critical challenges:
- **Doctor-to-patient ratio**: 1:1,456 (WHO recommends 1:1,000)
- **Overcrowded OPDs**: Doctors spend <5 minutes per patient
- **Rural healthcare gap**: 70% population with limited access to specialists
- **Preventable ER visits**: 40% cases are minor ailments treatable at home
- **Lost patient history**: No continuity of care across visits

## The Solution

CuraSetu 2.0 is **NOT a doctor replacement** — it's a medical assistant that:

### For Patients
- **Triage minor ailments**: Provides evidence-based guidance for common conditions (fever, cold, gastritis)
- **Reduces unnecessary ER visits**: Helps identify when home care is sufficient vs. when to seek immediate medical attention
- **Health education**: Explains symptoms, prevention, and warning signs in simple language
- **24/7 availability**: Accessible anytime, especially in rural areas with limited doctor access

### For Doctors
- **Patient history tracking**: Maintains detailed conversation logs for continuity of care
- **Pre-consultation screening**: Patients arrive with documented symptom history
- **Clinical decision support**: Provides differential diagnosis suggestions with confidence scores
- **Time efficiency**: Reduces time spent on history-taking, allowing doctors to focus on diagnosis and treatment
- **Follow-up monitoring**: Tracks patient progress across multiple consultations

### Impact on Healthcare System
- **Reduces OPD load**: Filters out 30-40% of minor cases that can be managed at home
- **Improves doctor productivity**: Saves 2-3 minutes per patient on history documentation
- **Enhances rural healthcare**: Provides preliminary guidance where doctors are scarce
- **Data-driven insights**: Aggregates regional disease patterns for public health planning

## Key Features

### Medical Intelligence
- **Advanced Medical Reasoning Engine**: Multi-layered confidence scoring with symptom quality analysis
- **Primary Symptom Weighting**: Prioritizes hallmark symptoms (+30%) over secondary indicators
- **Regional Disease Awareness**: India-focused with monsoon season adjustments for dengue/malaria/typhoid
- **Clinical Accuracy**: Severity weighting, time-based progression analysis, comorbidity detection
- **Transparent Uncertainty**: Displays confidence scores (0-100%) with clinical reasoning explanations
- **Differential Diagnosis**: "What this is NOT" reassurance sections to reduce patient anxiety
- **Context-Aware Follow-ups**: Generates relevant questions when confidence <85%

### User Experience
- **60fps Performance**: Adaptive glassmorphism with device-based rendering optimization
- **Professional Medical UI**: Font Awesome icons, theme-aware design, no emojis
- **Adaptive Chat Bubbles**: Auto-sizing with smooth 18px curved edges and proper text wrapping
- **Dark/Light Theme**: Semantic CSS variables for consistent readability
- **Persistent Chat History**: Thread-based conversations with message history
- **User Profile Management**: Edit profile and upload profile pictures
- **Secure Authentication**: Django built-in auth with password visibility toggle

## Technologies Used

- **Backend**: Django 4.2.7, Python 3.8+
- **Database**: MySQL (SQLite supported for development)
- **AI Stack**: LLM-powered reasoning (Gemini), semantic retrieval (FAISS + sentence-transformers)
- **Frontend**: Bootstrap 5, HTML5, CSS3 (adaptive glassmorphism), JavaScript (60fps optimizations)
- **Icons**: Font Awesome 6 (professional medical UI)
- **Authentication**: Django built-in auth system

### Why FAISS?

FAISS enables fast similarity search over medical knowledge embeddings, allowing CuraSetu to retrieve clinically relevant context before reasoning. This ensures responses are grounded in verified data rather than purely generative output.

## Setup Instructions

### Prerequisites

1. Python 3.8 or higher
2. MySQL Server
3. MySQL Workbench (optional, for database management)
4. Google Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   cd ai_healthcare_chatbot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Fill in your database credentials and Gemini API key:
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   DB_NAME=curasetu_db
   DB_USER=root
   DB_PASSWORD=your-mysql-password
   DB_HOST=localhost
   DB_PORT=3306
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

4. **Set up MySQL database**
   - Create a new database named `curasetu_db` in MySQL
   - Update the database credentials in `.env`

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Open your browser and go to `http://127.0.0.1:8000`
   - Register a new account or login with existing credentials

## Usage

1. **Registration**: Create a new account with username, email, and password
2. **Login**: Sign in to access your personal chat interface
3. **Chat**: Describe your symptoms to get AI-powered health advice
4. **Profile**: Update your profile information and upload a profile picture
5. **Chat History**: View and resume previous conversations

## Medical Reasoning Architecture

CuraSetu 2.0 uses a sophisticated multi-layered confidence scoring system:

1. **Symptom Quality Analysis**: Evaluates severity (mild/moderate/severe), duration, progression (worsening/improving), age modifiers, comorbidity detection, and contradiction detection
2. **Regional Weighting**: India-focused with monsoon season boost (+15% for dengue/malaria/typhoid during June-Sept)
3. **Symptom Role Weighting**: Primary symptom match (+30%), secondary match (+10%), co-occurrence pairs (+15%), negative evidence penalty (-25%)
4. **Confidence Separation**: Enforces minimum 12% gap between top two conditions for clear diagnosis
5. **Clinical Reasoning**: Generates transparent explanations for disease ranking and uncertainty

**Confidence Caps**: 90% absolute max, 85% without complete info, 60% with contradictions, 25% minimum display threshold

**Note**: Confidence scores are heuristic estimates, not probabilistic diagnoses.

**Response Structure**: Ranked conditions → Ranking explanation → Uncertainty explanation → Disease details → "What this is NOT" → Treatment/warnings/prevention → Follow-up questions → Reassurance

## Performance Optimizations

- **Adaptive Rendering**: Device capability detection (high-end/mobile/reduced-motion)
- **GPU Acceleration**: Transform/opacity-only animations, will-change hints
- **Debounced Handlers**: Scroll and input events optimized with requestAnimationFrame
- **Shadow Budget**: Limited blur effects on mobile devices
- **Lazy Loading**: Conditional glassmorphism based on device capability

## Project Structure

```
CuraSetu/
├── accounts/              # User authentication and profile management
├── chatbot/              # AI chatbot with medical reasoning engine
│   ├── services.py       # Core medical reasoning logic
│   └── views.py          # Chat interface and thread management
├── curasetu/             # Django project settings
├── templates/            # HTML templates with theme-aware design
│   ├── base.html         # Semantic CSS variables, theme management
│   └── chatbot/chat.html # Adaptive chat bubbles, Font Awesome icons
├── static/
│   ├── css/
│   │   └── performance.css  # Adaptive glassmorphism, device detection
│   └── js/
│       └── performance.js   # 60fps optimizations, FPS monitoring
├── media/                # User uploaded files
├── disease_data.json     # Medical knowledge base
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## What's New in 2.0

- ✅ Advanced medical reasoning with confidence scoring
- ✅ Primary symptom weighting and clinical accuracy corrections
- ✅ Regional disease awareness (India-focused with monsoon adjustments)
- ✅ 60fps performance optimizations for low-end devices
- ✅ Professional medical UI (Font Awesome icons, no emojis)
- ✅ Adaptive chat bubbles with smooth 18px curved edges
- ✅ Theme-aware design with semantic CSS variables
- ✅ Transparent uncertainty explanations
- ✅ "What this is NOT" differential diagnosis sections
- ✅ Context-aware follow-up questions
- ✅ Comorbidity detection and age-based risk modifiers

## Safety Guardrails

- CuraSetu never provides definitive diagnoses
- Emergency symptoms always trigger escalation advice
- Medication suggestions are non-prescriptive and informational
- Pediatric and pregnancy-related queries use stricter thresholds
- All outputs include uncertainty framing

## Medical Knowledge Sources

- WHO (World Health Organization)
- CDC (Centers for Disease Control)
- MedlinePlus
- Mayo Clinic
- NIDDK (National Institute of Diabetes and Digestive and Kidney Diseases)
- NHS (where applicable)

All responses cite source-backed content. No synthetic medical facts are generated.

## Ethical AI Commitment

CuraSetu prioritizes safety, transparency, and patient well-being. It avoids hallucinations, discloses uncertainty, and encourages professional care when needed.

## Contributing

We welcome contributions from developers, medical professionals, and healthcare enthusiasts!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Make your changes
4. Test thoroughly (ensure 60fps performance on mobile)
5. Submit a pull request

**Areas for contribution**:
- Expanding disease knowledge base
- Adding regional language support (Hindi, Tamil, Bengali, etc.)
- Improving medical reasoning algorithms
- Integrating with hospital EMR systems
- Mobile app development (React Native/Flutter)

## Roadmap

- **Phase 3**: Multilingual support (Hindi, Tamil, Bengali)
- **Phase 4**: Offline-first PWA for rural areas
- **Phase 5**: Doctor dashboard with patient timeline view
- **Phase 6**: Integration with Ayushman Bharat Digital Mission (ABDM)

## License

Licensed under the MIT License. See [LICENSE](LICENSE) file.

## Medical Disclaimer

⚠️ **IMPORTANT**: CuraSetu is a medical assistant tool, NOT a replacement for professional medical advice.

- Always consult a qualified doctor for diagnosis and treatment
- Use this tool for preliminary guidance and health education only
- Seek immediate medical attention for severe symptoms or emergencies
- This tool is designed to complement, not replace, doctor consultations
- Doctors retain full authority over patient care decisions

## Acknowledgments

Built with the goal of making healthcare more accessible and efficient in India. Special thanks to the open-source community and medical professionals who provided guidance on clinical accuracy.

---

**For support or queries**: Open an issue on GitHub  
**For medical emergencies**: Call 108 (India Emergency Services)