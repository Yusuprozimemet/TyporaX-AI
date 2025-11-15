# agents/lesson_bot.py
import re
from transformers import pipeline
import torch

# TINY MODEL: 1.5B → streams, < 200 MB disk, ~3 GB RAM
generator = pipeline(
    "text-generation",
    model="Qwen/Qwen2.5-Coder-1.5B-Instruct",  # ← 1.5B, not 7B
    device_map="auto",
    dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    max_new_tokens=150,  # Reduced for faster generation
    do_sample=False,
    trust_remote_code=True,
)


def extract_contextual_vocabulary(daily_log: str, target_language: str):
    """Extract and translate key terms from daily log"""
    import re

    # Enhanced vocabulary mapping based on common terms
    vocab_maps = {
        "dutch": {
            "job interview": "sollicitatie – job interview",
            "interview": "sollicitatie – job interview",
            "full stack": "full-stack – full stack",
            "developer": "ontwikkelaar – developer",
            "development": "ontwikkeling – development",
            "python": "Python – Python",
            "programming": "programmeren – programming",
            "code": "code – code",
            "software": "software – software",
            "application": "applicatie – application",
            "database": "database – database",
            "frontend": "frontend – frontend",
            "backend": "backend – backend",
            "framework": "framework – framework",
            "api": "API – API",
            "javascript": "JavaScript – JavaScript",
            "react": "React – React",
            "node": "Node.js – Node.js",
            "experience": "ervaring – experience",
            "skills": "vaardigheden – skills",
            "project": "project – project",
            "team": "team – team",
            "company": "bedrijf – company",
            "salary": "salaris – salary",
            "position": "positie – position"
        },
        "japanese": {
            "job interview": "面接 (めんせつ) – job interview",
            "interview": "面接 (めんせつ) – interview",
            "full stack": "フルスタック – full stack",
            "developer": "開発者 (かいはつしゃ) – developer",
            "development": "開発 (かいはつ) – development",
            "python": "Python (パイソン) – Python",
            "programming": "プログラミング – programming",
            "code": "コード – code",
            "software": "ソフトウェア – software",
            "application": "アプリケーション – application",
            "database": "データベース – database",
            "frontend": "フロントエンド – frontend",
            "backend": "バックエンド – backend",
            "framework": "フレームワーク – framework",
            "api": "API (エーピーアイ) – API",
            "javascript": "JavaScript (ジャバスクリプト) – JavaScript",
            "react": "React (リアクト) – React",
            "experience": "経験 (けいけん) – experience",
            "skills": "スキル – skills",
            "project": "プロジェクト – project",
            "team": "チーム – team",
            "company": "会社 (かいしゃ) – company"
        },
        "chinese": {
            "job interview": "面试 (miànshì) – job interview",
            "interview": "面试 (miànshì) – interview",
            "full stack": "全栈 (quánzhàn) – full stack",
            "developer": "开发者 (kāifāzhě) – developer",
            "development": "开发 (kāifā) – development",
            "python": "Python – Python",
            "programming": "编程 (biānchéng) – programming",
            "code": "代码 (dàimǎ) – code",
            "software": "软件 (ruǎnjiàn) – software",
            "application": "应用程序 (yìngyòng chéngxù) – application",
            "database": "数据库 (shùjùkù) – database",
            "frontend": "前端 (qiánduān) – frontend",
            "backend": "后端 (hòuduān) – backend",
            "framework": "框架 (kuàngjià) – framework",
            "api": "API – API",
            "javascript": "JavaScript – JavaScript",
            "react": "React – React",
            "experience": "经验 (jīngyàn) – experience",
            "skills": "技能 (jìnéng) – skills",
            "project": "项目 (xiàngmù) – project",
            "team": "团队 (tuánduì) – team",
            "company": "公司 (gōngsī) – company"
        }
    }

    vocab_map = vocab_maps.get(target_language, vocab_maps["japanese"])
    found_vocab = []

    daily_log_lower = daily_log.lower()
    for key, translation in vocab_map.items():
        if key in daily_log_lower:
            found_vocab.append(translation)
            print(f"Found: '{key}' -> {translation}")

    return found_vocab


def generate_contextual_sentences(daily_log: str, target_language: str):
    """Use AI to generate contextual sentences based on daily log content"""

    print(f"🤖 Generating AI sentences for: '{daily_log}' in {target_language}")

    try:
        # Create a focused prompt for sentence generation
        if target_language.lower() == "dutch":
            prompt = f"""Generate 8 Dutch sentences about these activities: "{daily_log}"

Write sentences in Dutch that describe what someone did based on these activities. Make them personal and specific to the activities mentioned.

Activities: {daily_log}

Dutch sentences:
1. Vandaag had ik"""

        elif target_language.lower() == "japanese":
            prompt = f"""Generate 8 Japanese sentences about these activities: "{daily_log}"

Write sentences in Japanese that describe what someone did based on these activities.

Activities: {daily_log}

Japanese sentences:
1. 今日は"""

        else:  # Chinese
            prompt = f"""Generate 8 Chinese sentences about these activities: "{daily_log}"

Write sentences in Chinese that describe what someone did based on these activities.

Activities: {daily_log}

Chinese sentences:
1. 今天我"""

        # Generate with AI (faster settings for CPU)
        response = generator(
            prompt,
            max_new_tokens=200,
            do_sample=False,
            pad_token_id=generator.tokenizer.eos_token_id
        )[0]['generated_text']

        # Extract generated content
        if prompt in response:
            ai_content = response.split(prompt)[-1].strip()
        else:
            ai_content = response.strip()

        print(f"AI sentence generation: {ai_content[:200]}...")

        # Extract sentences from the response
        sentences = []
        lines = ai_content.split('\n')

        for line in lines:
            line = line.strip()
            # Remove numbering like "1.", "2.", etc.
            if line and not line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.')):
                # Remove any remaining numbering patterns
                import re
                clean_line = re.sub(r'^\d+\.\s*', '', line)
                # Ensure it's a meaningful sentence
                if clean_line and len(clean_line) > 5:
                    sentences.append(clean_line)
            elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.')):
                # Extract sentence after numbering
                clean_line = line[2:].strip()
                if clean_line and len(clean_line) > 5:
                    sentences.append(clean_line)

        if len(sentences) >= 3:
            print(f"✅ AI generated {len(sentences)} contextual sentences")
            return sentences[:8]

    except Exception as e:
        print(f"AI sentence generation failed: {e}")

    # Minimal fallback - just return empty list to force the main function to use AI generation
    print("⚠️ Falling back to main AI generation")
    return []


def run_lesson_bot(daily_log: str, target_language: str = "japanese"):
    """
    Generate personalized vocabulary and sentences based on user's daily activities.
    Uses AI to create contextual content from the daily log.
    """
    import random
    import re
    import json

    print(f"Processing daily log: '{daily_log}' for {target_language}")

    # First, try AI generation for contextual content
    if daily_log and daily_log.strip():
        try:
            print(
                f"🤖 Starting AI generation for: '{daily_log}' in {target_language}")

            # Create contextual vocabulary manually based on keywords
            contextual_vocab = extract_contextual_vocabulary(
                daily_log, target_language)
            contextual_sentences = generate_contextual_sentences(
                daily_log, target_language)

            if len(contextual_vocab) >= 5 and len(contextual_sentences) >= 3:
                print(
                    f"✅ Generated contextual content: {len(contextual_vocab)} words, {len(contextual_sentences)} sentences")
                return {
                    "words": contextual_vocab[:15],
                    "sentences": contextual_sentences[:8],
                    "language": target_language
                }

            # Fallback to AI generation if contextual extraction didn't work well
            lang_example = {
                "dutch": "Dutch with English translations",
                "japanese": "Japanese with romaji and English",
                "chinese": "Chinese with pinyin and English"
            }.get(target_language, "the target language")

            prompt = f"""Based on activities: "{daily_log}"
Create {target_language} vocabulary and sentences for these specific activities.
Make vocabulary relevant to: job interviews, programming, development work.

Format: word – translation

Generate 10 relevant vocabulary words and 5 sentences in {target_language}."""

            print(f"🔄 Using AI model for generation...")

            # Generate with AI (faster settings for CPU)
            response = generator(
                prompt,
                max_new_tokens=300,
                do_sample=False,
                pad_token_id=generator.tokenizer.eos_token_id
            )[0]['generated_text']

            # Extract the generated content after the prompt
            if prompt in response:
                ai_content = response.split(prompt)[-1].strip()
            else:
                ai_content = response.strip()

            print(f"AI raw response: {ai_content[:200]}...")

            # Try to extract JSON from the response
            if '{' in ai_content and '}' in ai_content:
                # Find the JSON part
                json_start = ai_content.find('{')
                json_part = ai_content[json_start:]

                # Find the end of JSON
                brace_count = 0
                json_end = json_start
                for i, char in enumerate(json_part):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break

                json_content = json_part[:json_end]
                print(f"Extracted JSON: {json_content}")

                try:
                    ai_lesson = json.loads(json_content)
                    if isinstance(ai_lesson, dict) and 'words' in ai_lesson and 'sentences' in ai_lesson:
                        # Validate the content
                        words = ai_lesson['words'][:15]  # Limit to 15
                        sentences = ai_lesson['sentences'][:8]  # Limit to 8

                        if len(words) >= 5 and len(sentences) >= 3:  # Minimum viable content
                            print(
                                f"✅ AI generated: {len(words)} words, {len(sentences)} sentences in {target_language}")
                            return {
                                "words": words,
                                "sentences": sentences,
                                "language": target_language
                            }
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")

        except Exception as e:
            print(f"AI generation failed: {e}")

        # Try simpler AI generation as final attempt
        print("🔄 Attempting simpler AI generation...")
        try:
            simple_prompt = f"""Create {target_language} vocabulary for: {daily_log}

Generate 10 vocabulary terms related to these activities.
Create 6 sentences in {target_language} about these activities.

Focus on the specific activities mentioned."""

            response = generator(
                simple_prompt,
                max_new_tokens=250,
                do_sample=False,
                pad_token_id=generator.tokenizer.eos_token_id
            )[0]['generated_text']

            # Extract content
            if simple_prompt in response:
                ai_content = response.split(simple_prompt)[-1].strip()
            else:
                ai_content = response.strip()

            print(f"Simple AI response: {ai_content[:300]}...")

            # Parse the response more flexibly
            lines = ai_content.split('\n')
            words = []
            sentences = []

            for line in lines:
                line = line.strip()
                if '–' in line or '-' in line:  # Likely vocabulary
                    words.append(line)
                elif len(line) > 10 and line.endswith('.'):  # Likely sentence
                    sentences.append(line)

            if len(words) >= 3 and len(sentences) >= 2:
                print(
                    f"✅ Simple AI generated: {len(words)} words, {len(sentences)} sentences")
                return {
                    "words": words[:15],
                    "sentences": sentences[:8],
                    "language": target_language
                }

        except Exception as e:
            print(f"Simple AI generation also failed: {e}")

    # If AI generation fails completely, raise an error instead of falling back to hardcoded content
    print("❌ All AI generation methods failed!")
    raise Exception(
        f"AI generation failed for activities: '{daily_log}'. Please try again with different activities or check your model setup.")
