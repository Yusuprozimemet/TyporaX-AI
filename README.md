# 🎓 TyporaX-AI — AI Language Coach

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**TyporaX-AI** is a personalized Dutch language learning platform powered by AI expert coaches. Practice real-world conversations with specialized experts while receiving real-time assessment and feedback tailored to your personality type (MBTI).

---

## ✨ Features

- 🤖 **AI Expert Coaches** - Healthcare Expert, IT Interview Coach, Language Tutor
- 📊 **Real-Time Assessment** - Live feedback on grammar, fluency, and vocabulary
- 🎯 **Personality-Based Learning** - MBTI-optimized study methods
- 📝 **Markdown Editor** - Write and practice with integrated tools
- 🎴 **Anki Flashcards** - Auto-generated spaced repetition cards
- 🔊 **Audio Pronunciation** - Natural Dutch speech synthesis
- 📈 **Progress Tracking** - Monitor your learning journey

---

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- ~2GB RAM

### Installation

```bash
# Clone repository
git clone https://github.com/Yusuprozimemet/TyporaX-AI.git
cd TyporaX-AI

# Create environment
conda create -n typorax python=3.13
conda activate typorax

# Install dependencies
pip install -r requirements.txt

# Launch application
python main.py
```

**Access:** Open browser to `http://localhost:8000`

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
│       ├── healthcare_expert.py
│       └── it_backend_interviewer.py
└── data/users/{user_id}/      # User profiles & progress
```

---

## 🎯 How It Works

### 1. **Expert Chat**
Choose an expert → Practice Dutch conversation → Get AI responses tailored to domain

### 2. **Real-Time Assessment**
Every message analyzed for:
- **Grammar & Fluency** (0-10 scores)
- **Vocabulary Level** (Beginner → Advanced)
- **Live Hints** (Language tips, conversation tips, expert-specific guidance)

### 3. **Personalized Learning**
- **MBTI-Based Methods**: Immersion vs. Structured approach
- **Daily Lessons**: Vocabulary from your activities
- **Progress Tracking**: Realistic timeline predictions

### 4. **Export Resources**
- 📄 PDF learning plans
- 🎴 Anki flashcard decks
- 🔊 Audio pronunciation files

---

## ⚙️ Configuration

### Environment Setup
```bash
# Optional: Configure API tokens
export HF_TOKEN="your_huggingface_token"

# Optional: Custom data directory
export TYPORAX_DATA_DIR="/custom/path"
```

### Expert Customization
Edit prompts in `prompts/` directory:
- `healthcare_expert.json` - Medical scenarios
- `it_backend_interviewer.json` - Tech interviews
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
*TyporaX-AI v8 - Where personality meets AI to unlock your language learning potential*