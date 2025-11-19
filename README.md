# 🎓 TyporaX-AI — AI Language Coach

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq-Powered-orange.svg)](https://groq.com)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)

**TyporaX-AI** is a personalized Dutch language learning platform powered by lightning-fast Groq AI models. Practice with specialized expert coaches, enjoy immersive podcast conversations, and receive real-time assessment with desktop PWA experience.

> 🌟 **We're an open-source project and we welcome contributors!** Whether you're fixing a typo or adding a new feature, your contributions help make language learning accessible to everyone. [See how to contribute →](#-contributing)

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
git clone https://github.com/Yusuprozimemet/TyporaX-AI.git
cd TyporaX-AI

# Create environment
conda create -n env python=3.13
conda activate env

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

**We welcome contributions from everyone!** 🎉 Whether you're a developer, language expert, designer, or just passionate about education technology, there's a place for you here.

### 🌟 Why Contribute?

- 🚀 Help make language learning accessible to everyone
- 💡 Share your expertise and ideas
- 🌍 Join a community of developers and educators
- 📚 Learn FastAPI, AI integration, and modern web development
- ✨ See your code make a real impact

### 🎯 How to Contribute

#### For First-Time Contributors

1. **Fork the repository** - Click the "Fork" button at the top right
2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/TyporaX-AI.git
   cd TyporaX-AI
   ```
3. **Set up development environment**
   ```bash
   conda create -n env python=3.13
   conda activate env
   pip install -r requirements.txt
   ```
4. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
5. **Make your changes** - Write code, fix bugs, improve docs
6. **Test your changes**
   ```bash
   python main.py  # Test the application
   ```
7. **Commit with clear messages**
   ```bash
   git add .
   git commit -m "Add: Brief description of your change"
   ```
8. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
9. **Open a Pull Request** - Go to the original repository and click "New Pull Request"

#### Contribution Ideas

**🐛 Bug Fixes**
- Fix reported issues in GitHub Issues
- Improve error handling
- Fix typos or broken links

**✨ New Features**
- Add support for new languages (French, Spanish, German, etc.)
- Create new expert personalities (Business Coach, Travel Guide, etc.)
- Implement new assessment metrics
- Add gamification features (badges, streaks, etc.)

**🎨 UI/UX Improvements**
- Enhance the web interface design
- Improve mobile responsiveness
- Add dark mode support
- Create better visualizations for progress tracking

**📚 Documentation**
- Improve README or other docs
- Add code comments
- Create tutorials or video guides
- Translate documentation to other languages

**🔧 Code Quality**
- Refactor code for better performance
- Add unit tests
- Improve code organization
- Optimize API endpoints

**🌐 Localization**
- Translate UI to other languages
- Add language-specific learning content
- Adapt cultural references

### 📝 Contribution Guidelines

- **Code Style**: Follow PEP 8 for Python code
- **Commit Messages**: Use clear, descriptive commit messages (e.g., "Add: Spanish language support", "Fix: Audio playback issue")
- **Testing**: Test your changes thoroughly before submitting
- **Documentation**: Update docs if you change functionality
- **Small PRs**: Keep pull requests focused on a single feature or fix

### 🐛 Reporting Issues

Found a bug? Have a suggestion? Please open an issue on GitHub:
1. Check if the issue already exists
2. Use a clear, descriptive title
3. Provide detailed steps to reproduce (for bugs)
4. Include your environment details (OS, Python version, etc.)

### 💬 Getting Help

- **Questions?** Open a discussion on GitHub Discussions
- **Stuck?** Comment on the issue you're working on
- **Ideas?** Share them in GitHub Issues with the "enhancement" label

### 🎓 Learning Resources

New to the technologies we use?
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Groq API Docs](https://console.groq.com/docs)
- [Python Beginner's Guide](https://www.python.org/about/gettingstarted/)
- [Git & GitHub Tutorial](https://docs.github.com/en/get-started)

### 🏆 Recognition

All contributors will be:
- Listed in our Contributors section
- Credited in release notes
- Part of a growing open-source community

**Thank you for helping make language learning better for everyone!** 💙

---

## 👥 Contributors

We appreciate all contributions to this project! 🙏

<!-- Contributors list will be automatically updated -->
Want to see your name here? [Start contributing today!](#-contributing)

---

## 📜 License

This project is licensed under the Apache 2.0 License - see [LICENSE](LICENSE) file.

**This means you can:**
- ✅ Use this software commercially
- ✅ Modify and distribute
- ✅ Use privately
- ✅ Use patents (if any)

**With the conditions:**
- 📋 Include original license and copyright
- 📝 State significant changes made

---

## 🙏 Acknowledgments

- **Hugging Face** - AI model infrastructure
- **FastAPI** - Modern web framework
- **Edge TTS** - Natural speech synthesis

---

*TyporaX-AI v8 - Where personality meets AI to unlock your language learning potential*
*TyporaX-AI v8 - Where personality meets AI to unlock your language learning potential*