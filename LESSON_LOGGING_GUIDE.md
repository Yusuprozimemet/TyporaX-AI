# Lesson Generation Logging & Tracking System

## Overview
A comprehensive logging system has been implemented to track how lessons are generated based on user assessments. This allows you to verify that the AI is properly analyzing assessment data and generating appropriate lessons.

## Components Added

### 1. Enhanced Logging in `lesson_generator.py`
- **Assessment Analysis Logging**: Shows all errors, focus areas, grammar issues, and vocabulary gaps extracted from assessments.json
- **Prompt Logging**: Logs the exact prompt sent to the AI model
- **AI Response Logging**: Captures the AI's response for inspection
- **Lesson Parsing Logging**: Shows exercise types and structure of generated lessons
- **Detailed Metadata**: Stores assessment count, error patterns used, grammar issues, and vocabulary gaps in lesson metadata

### 2. Lesson Generation Logging (`src/utils/lesson_logger.py`)
A dedicated logging utility that stores:
- `lesson_log_[timestamp].json` - Complete lesson generation log with all metadata
- `prompt_[timestamp].txt` - Full AI prompt sent
- `response_[timestamp].txt` - Full AI response received

Location: `data/users/{user_id}/lesson_logs/`

### 3. Main Router Enhancement (`main_router.py`)
Enhanced `/api/generate-lesson` endpoint to:
- Log assessment file loading
- Show assessment count
- Record complete generation process

### 4. New API Endpoints

#### `GET /api/lesson-generation-logs/{user_id}`
Returns all lesson generation logs for a user
```json
{
  "user_id": "tester",
  "total_lessons": 3,
  "logs": [
    {
      "timestamp": "2025-11-21T...",
      "analysis": {
        "error_patterns": [...],
        "focus_areas": [...],
        "grammar_issues": [...],
        "vocabulary_gaps": [...],
        "difficulty_level": "beginner",
        "avg_grammar_score": 4.5
      },
      "lesson": {
        "title": "...",
        "exercise_count": 8,
        "exercises": [...]
      }
    }
  ]
}
```

#### `GET /api/lesson-generation-logs/latest/{user_id}`
Returns the most recent lesson generation log with full details

#### `GET /api/lesson-generation-impact/{user_id}`
Analyzes how assessments impacted lesson generation over time
```json
{
  "total_lessons_generated": 3,
  "lessons": [
    {
      "timestamp": "...",
      "difficulty": "beginner",
      "grammar_score": 4.5,
      "error_patterns": ["subject-verb agreement", "preposition usage"],
      "focus_areas": ["grammar", "vocabulary"],
      "exercise_types": {
        "typing": 2,
        "fill_blank": 3,
        "word_order": 2,
        "matching": 1
      }
    }
  ]
}
```

### 5. Lesson Logs Viewer (`static/lesson-logs-viewer.html`)
Interactive web interface to view and analyze lesson generation logs

**URL**: `http://localhost:8000/lesson-logs`

**Features**:
- 🔍 Search logs by user ID
- 📊 View all generated lessons with assessment details
- 📈 See how assessments impacted each lesson
- 🎯 Check error patterns addressed in lessons
- 📝 Verify grammar issues and vocabulary gaps were incorporated
- 💡 Impact analysis showing progression over time

## How to Verify AI Quality

### Method 1: Via Web Interface
1. Open `http://localhost:8000/lesson-logs`
2. Enter user ID (e.g., "tester", "alex", "yusup")
3. Click "Load Latest" to see the most recent lesson
4. Check:
   - ✅ Error Patterns: Are your assessment errors being addressed?
   - ✅ Focus Areas: Do they match your assessment data?
   - ✅ Grammar Issues: Are grammar problems from assessments targeted?
   - ✅ Vocabulary Gaps: Are vocabulary weaknesses addressed?
   - ✅ Difficulty Level: Is it appropriate for your grammar score?

### Method 2: Via API
```bash
# Get all logs
curl http://localhost:8000/api/lesson-generation-logs/tester

# Get latest log
curl http://localhost:8000/api/lesson-generation-logs/latest/tester

# Get impact analysis
curl http://localhost:8000/api/lesson-generation-impact/tester
```

### Method 3: Check Log Files Directly
Navigate to: `data/users/{user_id}/lesson_logs/`

Files:
- `lesson_log_[timestamp].json` - Structured log
- `prompt_[timestamp].txt` - Raw prompt sent to AI
- `response_[timestamp].txt` - Raw AI response

## Console Logging
The application also logs to console with formatted output:

```
================================================================================
GENERATING LESSON PLAN
  User ID: tester
  Language: dutch
  Expert Domain: general
  Assessments Count: 3
================================================================================

✓ ASSESSMENT ANALYSIS SUMMARY:
  - Difficulty Level: beginner
  - Average Grammar Score: 4.5/10
  - Error Patterns (3): ['subject-verb agreement', 'preposition usage', 'word order']
  - Focus Areas: ['grammar', 'vocabulary']
  - Grammar Issues: ['grammar: subject-verb agreement']
  - Vocabulary Gaps: ['vocabulary: prepositions']

✓ LESSON GENERATED SUCCESSFULLY:
  - Title: Grammar Fundamentals Practice
  - Exercises: 8
  - Difficulty: beginner
  - Assessment-based Focus Areas: ['grammar', 'vocabulary']
  - Grammar Issues Addressed: ['subject-verb agreement']
  - Vocabulary Gaps: ['prepositions']
```

## What This Proves

When you review the logs, you can verify:

1. **Assessments are loaded**: Log shows count and file location
2. **Errors are extracted**: All error patterns from assessments.json are listed
3. **Focus areas are identified**: Focus areas match user's assessment data
4. **AI gets proper context**: The prompt shows exactly what errors/gaps the AI was told to address
5. **Lessons are personalized**: Exercise types and difficulty match assessment data
6. **Grammar/Vocabulary gaps are targeted**: Specific weaknesses appear in generated exercises

## Example Verification Flow

```
1. User "tester" generates a lesson
2. Check logs/latest: See that 3 assessment errors were found
3. Open "prompt_*.txt": Verify AI was told about these specific errors
4. Check "lesson_log_*.json": See which exercises address which errors
5. Open generated lesson: Verify exercises match the logged focus areas
```

## Notes

- Logs are stored per user in `data/users/{user_id}/lesson_logs/`
- Each lesson generation creates 3 files (JSON log, prompt, response)
- Logs are **never deleted** - providing a complete audit trail
- Console output shows real-time generation progress
- All timestamps are ISO format (UTC)
- Logs survive application restarts
