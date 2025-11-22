# Quick Reference: Verifying Lesson Generation Quality

## TL;DR - How to Check if AI is Using Assessments

### 🚀 Quick Start (2 minutes)

1. **Start the server** (if not already running)
   ```bash
   python -m uvicorn main:app --reload
   ```

2. **Open the logs viewer**
   - Go to: `http://localhost:8000/lesson-logs`

3. **Enter user ID and view**
   ```
   User ID: tester (or alex, yusup, etc.)
   Click "Load Latest"
   ```

4. **Check the verification section at bottom**
   - ✅ Shows how many error patterns from assessments were used
   - ✅ Confirms difficulty was adapted
   - ✅ Verifies grammar score was considered

---

## What You'll See

### Before: No Personalization
```
Lesson: "Generic Practice"
- Exercises don't match user's mistakes
- Difficulty is random
- No reference to assessments
```

### After: Personalized Based on Assessments
```
Lesson: "Grammar Fundamentals Practice"
Assessment Analysis Used for Generation:
  ✓ Error Patterns Addressed: [subject-verb agreement, prepositions, word order]
  ✓ Focus Areas: [grammar, vocabulary]
  ✓ Grammar Issues: [subject-verb agreement]
  ✓ Vocabulary Gaps: [prepositions, articles]

Verification:
  ✅ Generated based on 3 error patterns from assessments.json
  ✅ Difficulty adapted to: beginner
  ✅ Grammar score used: 4.5/10
```

---

## The Three Tabs Explained

### 1. "All Logs" Tab
Shows **every lesson** generated for a user
- Click "Load All Logs"
- See progression over time
- Check if lessons adapt as user improves

### 2. "Latest Log" Tab
Shows **most recent lesson** with full details
- Click "Load Latest"
- See exactly what assessments.json data was extracted
- See the full list of exercises generated
- **Best for verification** ✨

### 3. "Impact Analysis" Tab
Shows **how assessments influenced each lesson**
- Click "Impact Analysis"
- See difficulty progression
- See grammar score trend
- See exercise type distribution

---

## Console Output Example

When a lesson is generated, you'll see:

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
  - Error Patterns (3): [subject-verb agreement, preposition usage]
  - Focus Areas: [grammar, vocabulary]
  - Grammar Issues: [grammar: subject-verb agreement]
  - Vocabulary Gaps: [vocabulary: prepositions]

✓ LESSON GENERATED SUCCESSFULLY:
  - Title: Grammar Fundamentals Practice
  - Exercises: 8
  - Difficulty: beginner
  - Assessment-based Focus Areas: [grammar, vocabulary]
  - Grammar Issues Addressed: [subject-verb agreement]
  - Vocabulary Gaps: [prepositions]

✓ Generation logs saved to: data/users/tester/lesson_logs/lesson_log_20251121_123456.json
```

---

## Proof Points: How to Verify AI Quality

### 1. Error Patterns Are Being Used
**Check**: View "Latest Log" → "Assessment Analysis Used for Generation"
- You'll see exact errors from assessments.json
- Exercises should address these errors

### 2. Difficulty Adapts to User Level
**Check**: View "Impact Analysis"
- See how difficulty changes over time
- Grammar scores correlate with difficulty levels

### 3. Vocabulary Gaps Are Targeted
**Check**: View "Latest Log" → Generated Exercises
- Look for exercises with vocabulary from assessment gaps
- Should see fill_blank and matching for vocabulary

### 4. Grammar Issues Are Addressed
**Check**: View "Latest Log" → Grammar Issues section
- Should see specific grammar problems listed
- Exercises should target these issues

### 5. Focus Areas Match Assessments
**Check**: View "All Logs" → Compare Focus Areas
- Should be consistent with what user needs
- Changes as user's assessment data updates

---

## File Locations

Each lesson generation creates 3 files:

```
data/users/{user_id}/lesson_logs/
├── lesson_log_20251121_120000.json    # Structured log
├── prompt_20251121_120000.txt          # AI prompt sent
└── response_20251121_120000.txt        # AI response received
```

**Why separate files?**
- `.json` = Easy to parse, shows all structured data
- `.txt` (prompt) = See exactly what AI was told to do
- `.txt` (response) = Debug AI response format

---

## API Endpoints (For Advanced Use)

### Get All Logs
```bash
curl http://localhost:8000/api/lesson-generation-logs/tester | jq
```

### Get Latest Log
```bash
curl http://localhost:8000/api/lesson-generation-logs/latest/tester | jq
```

### Get Impact Analysis
```bash
curl http://localhost:8000/api/lesson-generation-impact/tester | jq
```

---

## Interpreting the "Assessment Analysis"

### Error Patterns
Shows top errors from user's assessment responses
- If user got subject-verb agreement wrong, it appears here
- AI will create exercises targeting this

### Focus Areas
Derived from user's performance
- "grammar" = User needs grammar practice
- "vocabulary" = User needs vocabulary practice

### Grammar Issues
Specific grammar problems extracted from errors
- These become fill_blank and word_order exercises

### Vocabulary Gaps
Vocabulary words user doesn't know
- These become matching and typing exercises

### Difficulty Level
Auto-calculated from grammar scores
- 0-5: beginner
- 5-8: intermediate  
- 8-10: advanced

### Grammar Score
Average from all assessments (out of 10)
- Influences exercise complexity
- Affects number of hints shown

---

## How AI Uses Assessment Data

```
assessment.json (user mistakes)
    ↓
LessonGenerator.analyze_assessments()
    ↓
Extracts: errors, focus_areas, grammar_score
    ↓
_build_lesson_prompt()
    ↓
"Create a lesson for {user_level} with focus on {errors}"
    ↓
Call Groq API with enhanced prompt
    ↓
AI generates exercises addressing {errors}
    ↓
Results logged and saved
```

---

## Quick Troubleshooting

### "No logs found"
- ✅ Generate a lesson first (`Start Practice` button in app)
- ✅ Check user ID spelling (case-sensitive)
- ✅ Check file exists: `data/users/{user_id}/assessments.json`

### "Lessons don't match assessments"
- ✅ Check error patterns in latest log
- ✅ Verify assessments.json has proper format
- ✅ Check grammar_score in analysis (should be 0-10)

### "Same lesson generated multiple times"
- ✅ Normal if no new assessments added
- ✅ Update assessments.json to change lesson content
- ✅ Check focus_areas in logs to see what changed

### "How do I know AI is working?"
- ✅ Best check: Compare error patterns in latest log with assessment errors
- ✅ They should match closely
- ✅ Generated exercises should target these exact errors

---

## Summary

The logging system proves that:
1. ✅ Assessments.json **is being read**
2. ✅ Errors **are being extracted**
3. ✅ AI **receives personalized prompts**
4. ✅ Lessons **are customized per user**
5. ✅ Quality **can be audited and verified**

Just visit `http://localhost:8000/lesson-logs` and start checking! 🎉
