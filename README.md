# 🎓 TyporaX-AI — AI Language Coach

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq-Powered-orange.svg)](https://groq.com)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**TyporaX-AI** is a personalized Dutch language learning platform powered by lightning-fast Groq AI models. Practice with specialized expert coaches, enjoy immersive podcast conversations, and receive real-time assessment with desktop PWA experience.

---

## ✨ Features

- 🎙️ **Dutch Podcast Expert** - Interactive Emma & Daan conversations with voice synthesis
- 🤖 **AI Expert Coaches** - Healthcare Expert, IT Interview Coach, Language Tutor  
- 📊 **Real-Time Assessment** - Live feedback on grammar, fluency, and vocabulary
- 💻 **PWA Desktop App** - Install as native desktop application
- 🎯 **Personality-Based Learning** - MBTI-optimized study methods
- 🎴 **Anki Flashcards** - Auto-generated spaced repetition cards
- 🔊 **Audio Pronunciation** - Natural Dutch speech synthesis (Edge-TTS)
- 📈 **Progress Tracking** - Monitor your learning journey

---

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- ~2GB RAM

### Installation

```bash
# Clone repository
git clone https://github.com/Yusuprozimemet/GeneLingua.git
cd GeneLingua

# Create environment
conda create -n geneenv python=3.13
conda activate geneenv

# Install dependencies
pip install -r requirements.txt

# Setup API key (get free key from groq.com)
echo "GROQ_API_KEY=your_groq_api_key" > .env

# Launch application
python main.py
```

**Access:** Open browser to `http://localhost:8000` → **Install as PWA for desktop experience**

---

## 📂 Project Structure

```
TyporaX-AI/
├── main.py                    # FastAPI application
├── requirements.txt           # Dependencies
├── templates/index.html       # Web interface
├── static/                    # CSS, JS, images
├── src/
│   ├── api/                   # API routes
│   │   ├── main_router.py     # Core endpoints
│   │   ├── chat_router.py     # Expert chat
│   │   └── assessment_router.py # Live assessment
│   ├── services/              # Business logic
│   │   ├── lesson_bot.py      # Lesson generation
│   │   ├── assessment.py      # Language analysis
│   │   └── calibrator.py      # Learning method
│   ├── utils/                 # Utilities
│   │   ├── audio.py           # TTS engine
│   │   ├── anki.py            # Flashcard export
│   │   └── pdf.py             # Report generation
│   └── experts/               # Expert personalities
│       ├── dutch_podcast_expert.py
│       ├── healthcare_expert.py
│       └── it_backend_interviewer.py
└── data/users/{user_id}/      # User profiles & progress
```

---

## 🎯 How It Works

### 1. **Dutch Podcast Experience**
Interactive Emma & Daan conversations → Real-time voice synthesis → Immersive listening practice

### 2. **Expert Chat**
Choose an expert → Practice Dutch conversation → Get AI responses tailored to domain

### 3. **Real-Time Assessment**
Every message analyzed for:
- **Grammar & Fluency** (0-10 scores)
- **Vocabulary Level** (Beginner → Advanced)  
- **Better Version** (Corrected sentences)
- **Live Hints** (Language tips, conversation tips, expert-specific guidance)

### 4. **Desktop PWA**
- **Install as App**: Native desktop experience
- **Draggable Panels**: Customizable assessment interface
- **Offline Ready**: Works without internet connection

### 5. **Export Resources**
- 📄 PDF learning plans
- 🎴 Anki flashcard decks
- 🔊 Audio pronunciation files

---

## ⚙️ Configuration

### Environment Setup
```bash
# Required: Groq API key (free at groq.com)
export GROQ_API_KEY="your_groq_api_key"

# Optional: Backup HuggingFace token
export HF_TOKEN="your_huggingface_token"

# Optional: Custom data directory
export TYPORAX_DATA_DIR="/custom/path"
```

### Expert Customization
Edit prompts in `prompts/` directory:
- `dutch_podcast_expert.json` - Podcast conversations
- `healthcare_expert.json` - Medical scenarios
- `it_backend_interviewer.json` - Tech interviews
- `assessment.json` - Language analysis
- `app.json` - General language coaching

---

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/api/chat` | POST | Expert conversation |
| `/api/assessment` | POST | Language analysis |
| `/api/generate-lesson` | POST | Create daily lesson |
| `/download/pdf/{user_id}` | GET | Learning plan PDF |
| `/download/anki/{user_id}` | GET | Flashcard deck |
| `/download/audio/{user_id}` | GET | Pronunciation audio |

---

## 🛠️ Development

### Adding New Expert
1. Create personality file in `src/experts/`
2. Add prompt template in `prompts/`
3. Register in expert router
4. Update frontend expert selector

### Testing
```bash
# Test lesson generation
python -c "from src.services.lesson_bot import run_lesson_bot; print(run_lesson_bot('test', 'dutch'))"

# Run application
python main.py
```

---

## 🐛 Troubleshooting

**Port already in use:**
```bash
# Change port in main.py
uvicorn.run(app, host="0.0.0.0", port=8001)
```

**PDF generation issues (Windows):**
```bash
conda install -c conda-forge gtk3 reportlab
```

**Memory issues:**
```bash
# Use lighter model or CPU-only
export CUDA_VISIBLE_DEVICES=""
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/NewFeature`
3. Commit changes: `git commit -m 'Add NewFeature'`
4. Push to branch: `git push origin feature/NewFeature`
5. Open Pull Request

**Areas for contribution:**
- Additional language support
- New expert personalities
- UI/UX improvements
- Performance optimization

---

## 📜 License

This project is licensed under the Apache 2.0 License - see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

- **Hugging Face** - AI model infrastructure
- **FastAPI** - Modern web framework
- **Edge TTS** - Natural speech synthesis

---

*TyporaX-AI v8 - Where personality meets AI to unlock your language learning potential*
