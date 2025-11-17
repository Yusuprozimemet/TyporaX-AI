# 🎓 TyporaX-AI — AI Language Coach

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)


**TyporaX-AI** is a personalized language learning platform that combines **AI-powered coaching** with **personality-based customization** to create tailored language learning experiences. By analyzing your personality type (MBTI) and daily activities, TyporaX-AI generates personalized study methods, vocabulary lessons, and progress tracking optimized for your learning style.

## 🌟 Key Features

### 🤖 **AI-Powered Personalization**
- **Smart Study Methods**: Customized based on your MBTI personality type and ancestry background
- **Dynamic Lesson Generation**: Vocabulary and sentences based on your daily activities
- **Progress Tracking**: Realistic learning timeline predictions
- **Multi-Modal Output**: PDF reports, Anki flashcards, and audio pronunciation guides

### 📊 **Professional Interface**
- **Modern Web UI**: Built with VS Code-inspired design
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Real-time Processing**: Live progress updates and detailed logging
- **Export Capabilities**: Multiple output formats for different learning styles

### 👥 **Expert Chat System**
- **Dutch Healthcare Expert**: Practice medical terminology and scenarios
- **IT Interview Coach**: Prepare for technical interviews in Dutch
- **Language Coach**: General language learning assistance

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- ~4GB RAM for AI model processing

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Yusuprozimemet/TyporaX-AI.git
   cd TyporaX-AI
   ```

2. **Create and activate virtual environment**
   ```bash
   # Using conda (recommended)
   conda create -n typorax python=3.13
   conda activate typorax
   
   # Or using venv
   python -m venv geneenv
   source geneenv/bin/activate  # On Windows: geneenv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   
   # For Windows users, also install GTK libraries for PDF generation:
   conda install -c conda-forge gtk3 reportlab
   ```

4. **Launch the application**
   ```bash
   python app.py
   ```

5. **Access the web interface**
   - Open your browser to `http://localhost:7860`
   - Upload your 23andMe data and start learning!

## 📁 Project Structure

```
TyporaX-AI/
├── main.py                # Main FastAPI application
├── app.py                 # Web application
├── structure.py           # Project structure utilities
├── requirements.txt       # Python dependencies
├── manifest.json         # Web app manifest
├── LICENSE               # MIT license
├── README.md            # This file
│
├── agents/              # AI agents for personalization
│   ├── calibrator.py   # Study method recommendation
│   ├── tracker.py      # Progress tracking and prediction
│   └── lesson_bot.py   # Daily lesson generation
│
├── tools/              # Utility modules
│   ├── pdf.py         # High-quality PDF report generation
│   ├── anki.py        # Anki flashcard deck export
│   ├── audio.py       # Text-to-speech audio generation
│   ├── dna_plot.py    # Genetic visualization charts
│   └── utils.py       # Common utilities
│
├── data/              # User data storage
│   └── users/         # Individual user profiles
│       └── {user_id}/
│           ├── genome.txt        # Raw DNA data
│           ├── progress.json     # Learning progress
│           ├── mbti.json        # Personality type
│           ├── logs.txt         # Daily activity logs
│           └── outputs/         # Generated materials
│
└── static/            # Web assets
    ├── app.js        # Frontend JavaScript
    ├── vscode.css    # VS Code-inspired styling
    └── images/       # Icons and images
```

## 🎓 How It Works

### 1. **Personalization System**
```
User Profile → MBTI Analysis → Learning Style Calibration → Personalized Method
```

The system customizes learning approaches based on:
- **Personality Type** (MBTI): Learning style preferences
- **Ancestry Background**: Cultural and linguistic considerations
- **Daily Activities**: Context-based vocabulary generation

### 2. **AI Learning System**
- **Input Processing**: Daily activities, personality type (MBTI), ancestry background
- **Method Calibration**: Immersion-heavy vs. structured approaches based on personality
- **Content Generation**: Contextual vocabulary from your daily experiences
- **Progress Modeling**: Realistic timelines based on study patterns

### 3. **Multi-Modal Output Generation**
- **📄 PDF Reports**: Professional learning plans with insights
- **🎴 Anki Decks**: Spaced repetition flashcards with examples
- **🔊 Audio Files**: Native pronunciation guides using Edge TTS
- **📊 Progress Charts**: Visual tracking of vocabulary growth and CEFR levels

## 🎯 Usage Guide

### Step 1: Personal Information
- **Name/ID**: Unique identifier for your learning profile
- **Ancestry**: Choose your background for cultural customization
- **MBTI Type**: Personality type for learning style customization

### Step 2: Language Preference
- **Target Language**: Choose from Japanese, Dutch, or Chinese
- **Language Settings**: Configure your learning preferences

### Step 3: Learning Context
- **Daily Activities**: Describe your day for relevant vocabulary generation
- **Chat with Experts**: Practice with AI language coaches

### Step 4: AI Processing
- **Genetic Calibration**: Study method optimization based on your DNA percentile
- **Progress Prediction**: Learning timeline using realistic growth models
- **Lesson Generation**: Contextual vocabulary and practice sentences

### Step 5: Download Resources
- **Complete PDF Plan**: Comprehensive learning strategy with personalized insights
- **Anki Flashcard Deck**: Ready-to-use spaced repetition cards
- **Audio Pronunciation Guide**: Native pronunciation examples

## 🔬 Learning Methodology

### Personality-Based Customization
- **MBTI Integration**: Adapts teaching style to personality preferences
- **Learning Style Optimization**: Visual, auditory, or kinesthetic emphasis
- **Cultural Background**: Ancestry-aware vocabulary and cultural context

### Study Method Calibration
| Personality Type | Study Focus | Time Allocation | Approach |
|-----------------|-------------|------------------|----------|
| Intuitive (N) | Immersion-Heavy | 90min input + 20min SRS | Natural acquisition |
| Balanced | Mixed | 70min input + 20min SRS | Varied methodology |
| Sensing (S) | Structured | 60min explicit + 30min drill | Systematic learning |

## ⚙️ Configuration

### Environment Variables
```bash
# Optional: Custom model endpoints
TRANSFORMERS_CACHE=/path/to/cache
CUDA_VISIBLE_DEVICES=0

# Optional: Custom data directory
TYPORAX_DATA_DIR=/custom/data/path
```

### Advanced Settings
Edit configuration files to customize:
- **Model Selection**: Change the language model for lesson generation
- **UI Themes**: Modify VS Code theme and styling
- **Export Formats**: Add new output formats
- **Expert Prompts**: Customize AI coach personalities

## 🛠️ Development

### Adding New Features
1. **New Genetic Variants**: Add SNPs to `dna_engine.py`
2. **Custom AI Agents**: Create new modules in `agents/`
3. **Export Formats**: Add new generators in `tools/`
4. **UI Components**: Extend the Gradio interface in `app.py`

### Testing
```bash
# Run basic functionality tests
python -c "from src.services.lesson_bot import run_lesson_bot; print(run_lesson_bot('test log', 'dutch'))"

# Test the application
python main.py
```

### Performance Optimization
- **GPU Acceleration**: Enable CUDA for faster AI processing
- **Model Quantization**: Use smaller models for resource-constrained environments
- **Caching**: Implement result caching for repeated analyses

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### Areas for Contribution
- **Language Support**: Extend to more languages beyond Dutch and Japanese
- **UI/UX**: Improve the web interface and user experience
- **Expert Coaches**: Add new expert personality types
- **Performance**: Optimize processing speed and memory usage
- **Documentation**: Enhance guides and API documentation

## 📊 Performance Metrics

- **AI Lesson Generation**: ~30-60 seconds (CPU), ~5-10 seconds (GPU)
- **PDF Generation**: ~2-5 seconds for complete reports
- **Memory Usage**: ~3-4GB peak during AI processing
- **Response Time**: Sub-second for chat interactions

## 🐛 Troubleshooting

### Common Issues

**1. Port Already in Use**
```bash
# Change port in main.py or kill existing process
lsof -ti:8000 | xargs kill -9  # Unix
# Or modify uvicorn.run(app, port=8001)
```

**2. Model Loading Issues**
```bash
# Clear cache and reinstall
rm -rf ~/.cache/huggingface
pip install --upgrade transformers torch
```

**3. PDF Generation Problems (Windows)**
```bash
# Install GTK libraries
conda install -c conda-forge gtk3
```

**4. Memory Issues**
```bash
# Reduce model size or use CPU-only mode
export CUDA_VISIBLE_DEVICES=""
```

### Getting Help
- **Issues**: Report bugs on [GitHub Issues](https://github.com/Yusuprozimemet/TyporaX-AI/issues)
- **Discussions**: Join conversations in [GitHub Discussions](https://github.com/Yusuprozimemet/TyporaX-AI/discussions)
- **Documentation**: Check our [Wiki](https://github.com/Yusuprozimemet/TyporaX-AI/wiki) for detailed guides

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **23andMe** for making personal genomics accessible
- **Hugging Face** for transformer models and infrastructure
- **Gradio** for the intuitive web interface framework
- **GWAS Catalog** for genetic variant effect sizes
- **Japanese Language Community** for linguistic insights

## 🚀 Future Roadmap

### Version 8.0 Planned Features
- [ ] **Multi-Language Support**: Extend to Korean, Mandarin, Spanish
- [ ] **Advanced Genetics**: Incorporate epigenetic markers and gene expression
- [ ] **Social Learning**: Multi-user progress comparison and collaboration
- [ ] **VR Integration**: Immersive language learning environments
- [ ] **Real-time Adaptation**: Dynamic difficulty adjustment based on performance

### Research Directions
- [ ] **Longitudinal Studies**: Track learning outcomes over months/years
- [ ] **Genome-Wide Analysis**: Expand from targeted SNPs to whole-genome
- [ ] **Neuroimaging Integration**: Combine genetic data with brain imaging
- [ ] **Pharmacogenomics**: Optimize nootropic recommendations for learning

---

**Made with ❤️ for the future of personalized education**

*TyporaX-AI v8 - Where personality meets AI to unlock your language learning potential*