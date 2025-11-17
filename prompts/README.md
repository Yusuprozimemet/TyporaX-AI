# TyporaX-AI Prompt Management System

This system externalizes all AI prompts from Python code into JSON configuration files, making it easy to update and customize expert behavior without touching the codebase.

## 🏗️ Architecture

```
prompts/
├── app.json                 # Main app prompts (language coach, expert prompts)
├── assessment.json          # Assessment and analysis prompts
├── healthcare_expert.json   # Healthcare expert prompts
├── it_backend_interviewer.json # IT interview expert prompts
└── ... (other expert modules)
```

## 📁 File Structure

### `prompts/app.json`
Contains the main application prompts:
- `language_coach`: Fallback Dutch language coach
- `expert_prompts.healthcare`: Healthcare expert behavior
- `expert_prompts.interview`: IT interview expert behavior  
- `expert_prompts.language`: General language learning expert

### `prompts/assessment.json`
Contains assessment and analysis prompts:
- `language_analysis`: Dutch language quality analysis
- `hints_generation`: Real-time conversation hints

### `prompts/healthcare_expert.json`
Contains healthcare roleplay prompts:
- `patient_role`: AI patient behavior in medical scenarios
- `user_prompt`: Patient response generation
- `medical_analysis`: Medical Dutch language analysis

### `prompts/it_backend_interviewer.json`
Contains IT interview prompts:
- `interviewer_role`: AI interviewer behavior
- `user_prompt`: Interview question generation
- `technical_analysis`: Technical Dutch language analysis

## 🛠️ Usage

### In Python Code

```python
from prompt_manager import get_prompt

# Simple prompt
system_prompt = get_prompt('app', 'language_coach')

# Prompt with variables
prompt = get_prompt('assessment', 'language_analysis', {
    'message': user_message
})

# Nested prompt (using dot notation)
expert_prompt = get_prompt('app', 'expert_prompts.healthcare')
```

### Command Line Tool

```bash
# List all modules
python prompt_cli.py list

# List prompts in a module
python prompt_cli.py list app

# Show a specific prompt
python prompt_cli.py show app language_coach

# Test prompt with variables
python prompt_cli.py test assessment language_analysis message="Ik ben ziek"

# Validate all configurations
python prompt_cli.py validate

# Reload configurations (useful during development)
python prompt_cli.py reload
```

## 📝 Prompt Configuration Format

### Simple Prompt
```json
{
  "language_coach": "Je bent een Nederlandse taalcoach..."
}
```

### Template Prompt
```json
{
  "language_analysis": {
    "prompt_template": "Analyseer deze tekst: {message}",
    "variables": ["message"]
  }
}
```

### Complex Prompt Configuration
```json
{
  "medical_analysis": {
    "system_prompt": "Je bent een medische taalexpert...",
    "user_prompt_template": "Patient zegt: {user_input}",
    "variables": ["user_input"]
  }
}
```

## 🔧 Advanced Features

### Variable Substitution
Templates support Python `str.format()` syntax:
```json
{
  "prompt_template": "Expert: {expert}\nContext: {context}\nMessage: {message}"
}
```

### Nested Access
Use dot notation for nested prompts:
```python
get_prompt('app', 'expert_prompts.healthcare')
```

### Caching
Prompt files are cached for performance. Use `reload_cache()` to refresh:
```python
from prompt_manager import reload_prompts
reload_prompts()
```

## ✨ Benefits

1. **Easy Customization**: Update expert behavior without code changes
2. **Version Control**: Track prompt changes separately from code
3. **A/B Testing**: Swap different prompt versions easily
4. **Non-Technical Editing**: Others can modify prompts without Python knowledge
5. **Centralized Management**: All prompts in one place
6. **Template System**: Reuse prompts with different variables
7. **Validation**: Built-in validation for prompt configurations

## 🚀 Migration Guide

To migrate existing hardcoded prompts:

1. **Extract the prompt** from Python code
2. **Add to appropriate JSON file** in `prompts/` directory
3. **Replace in code** with `get_prompt()` call
4. **Test the changes** using the CLI tool

### Example Migration

**Before:**
```python
system_prompt = "Je bent een Nederlandse taalcoach..."
```

**After:**
```python
system_prompt = get_prompt('app', 'language_coach')
```

**JSON Configuration:**
```json
{
  "language_coach": "Je bent een Nederlandse taalcoach..."
}
```

## 🧪 Testing Prompts

Always test prompts after changes:
```bash
# Test basic prompt
python prompt_cli.py show app language_coach

# Test template with variables
python prompt_cli.py test assessment language_analysis message="Hallo, hoe gaat het?"

# Validate all configurations
python prompt_cli.py validate
```

## 🔄 Development Workflow

1. **Edit prompts** in JSON files
2. **Test changes** using CLI tool
3. **Reload in app** (automatic in development)
4. **Validate** before deployment

## 📋 Best Practices

1. **Use descriptive keys**: `medical_patient_role` vs `prompt1`
2. **Include metadata**: Add `variables` array for templates
3. **Keep prompts focused**: One responsibility per prompt
4. **Document variables**: Use clear variable names
5. **Test regularly**: Validate after every change
6. **Version control**: Commit prompt changes with descriptive messages

## 🛡️ Error Handling

The system gracefully handles:
- Missing prompt files
- Invalid JSON syntax
- Missing variables in templates
- Non-existent prompt keys

Errors are logged and fallback behavior is provided.

---

This system makes TyporaX-AI's AI behavior highly configurable and maintainable! 🎯