# GeneLingua Project Structure

## 📁 New Organized Structure

```
GeneLingua/
├── main.py                     # 🚀 Main FastAPI application entry point
├── config/                     # ⚙️ Configuration files
│   ├── __init__.py
│   └── settings.py            # Application settings and environment variables
├── src/                       # 📦 Main source code
│   ├── __init__.py
│   ├── api/                   # 🌐 API endpoints (FastAPI routers)
│   │   ├── __init__.py
│   │   ├── main_router.py     # Main app endpoints (index, file uploads)
│   │   ├── chat_router.py     # Chat/conversation endpoints
│   │   └── assessment_router.py # Language assessment endpoints
│   ├── experts/               # 🎭 Expert conversation modules
│   │   ├── __init__.py
│   │   ├── healthcare_expert.py
│   │   ├── it_backend_interviewer.py
│   │   └── experts_voice.py
│   ├── services/              # 💼 Business logic services
│   │   ├── __init__.py
│   │   ├── assessment.py      # Real-time language assessment
│   │   ├── dna_engine.py      # DNA analysis engine
│   │   ├── calibrator.py      # Learning calibration
│   │   ├── tracker.py         # Progress tracking
│   │   └── lesson_bot.py      # Lesson generation
│   ├── utils/                 # 🛠️ Utility functions
│   │   ├── __init__.py
│   │   ├── prompt_manager.py  # AI prompt management
│   │   ├── utils.py           # General utilities
│   │   ├── anki.py           # Anki deck generation
│   │   ├── audio.py          # Audio generation
│   │   ├── dna_plot.py       # DNA visualization
│   │   └── pdf.py            # PDF generation
│   └── models/                # 📊 Data models (future)
│       └── __init__.py
├── prompts/                   # 🧠 AI prompt configurations
│   ├── README.md
│   ├── app.json
│   ├── assessment.json
│   ├── healthcare_expert.json
│   └── it_backend_interviewer.json
├── scripts/                   # 🔧 CLI tools and scripts
│   └── prompt_cli.py         # Prompt management CLI
├── static/                    # 🎨 Frontend assets
│   ├── css/
│   ├── js/
│   └── images/
├── templates/                 # 📄 HTML templates
│   └── index.html
├── data/                      # 💾 Data storage
│   └── users/
└── tests/                     # 🧪 Test files (future)
```

## 🎯 Architecture Benefits

### 1. **Microservices Ready**
- Clear separation of concerns
- Each service can become independent
- API-first design with routers
- Configuration-driven

### 2. **Maintainable**
- Logical organization by function
- Clear import paths
- Centralized configuration
- Utility functions properly organized

### 3. **Scalable**
- Services can be scaled independently
- Easy to add new experts/services
- Clean dependency management
- Testable architecture

## 🔄 Migration Summary

### Files Moved:
- `tools/*.py` → `src/utils/`
- `agents/*.py` → `src/services/`
- `other_experts/*.py` → `src/experts/`
- `assessment.py` → `src/services/`
- `dna_engine.py` → `src/services/`
- `prompt_manager.py` → `src/utils/`
- `prompt_cli.py` → `scripts/`

### New Files Created:
- `main.py` - New application entry point
- `config/settings.py` - Centralized configuration
- `src/api/*.py` - Modular API routers
- All `__init__.py` files for proper packages

### Key Changes:
- **Modular API**: Split monolithic `app.py` into focused routers
- **Service Layer**: Clear separation of business logic
- **Configuration**: Environment-based settings
- **Utilities**: All helper functions in one place
- **Experts**: Specialized conversation modules

## 🚀 Running the Application

### Development:
```bash
python main.py
```

### Production:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🔧 Key Components

### API Layer (`src/api/`)
- **main_router.py**: File uploads, profile management
- **chat_router.py**: Expert conversations, language detection
- **assessment_router.py**: Real-time language analysis

### Services Layer (`src/services/`)
- **assessment.py**: Language quality analysis
- **dna_engine.py**: Genetic analysis for personalization
- **calibrator.py**: Learning method calibration
- **lesson_bot.py**: Lesson content generation

### Utils Layer (`src/utils/`)
- **prompt_manager.py**: AI prompt configuration system
- **audio.py**: Text-to-speech generation
- **anki.py**: Flashcard deck creation
- **pdf.py**: Report generation

### Experts Layer (`src/experts/`)
- **healthcare_expert.py**: Medical conversation roleplay
- **it_backend_interviewer.py**: Technical interview practice
- **experts_voice.py**: Voice interaction handling

## 🎛️ Configuration

All settings now centralized in `config/settings.py`:
- API endpoints and tokens
- File paths and directories
- Audio settings
- Assessment parameters
- Logging configuration

## 📈 Future Microservices Path

This structure makes it easy to split into microservices:

1. **API Gateway** (`main.py` + `src/api/`)
2. **Chat Service** (`src/experts/` + chat logic)
3. **Assessment Service** (`src/services/assessment.py`)
4. **DNA Service** (`src/services/dna_engine.py`)
5. **Content Service** (`src/services/lesson_bot.py`)
6. **Utils Service** (`src/utils/`)

Each service can have its own:
- Database
- Configuration
- Scaling strategy
- Deployment pipeline

The current structure provides a clean foundation for this evolution! 🎉