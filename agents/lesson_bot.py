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
    max_new_tokens=256,
    do_sample=False,
    trust_remote_code=True,
)


def run_lesson_bot(daily_log: str):
    # Enhanced lesson bot with more comprehensive vocabulary
    import random

    # Expanded vocabulary based on daily activities
    sample_words = [
        "会議 (かいぎ) – meeting",
        "仕事 (しごと) – work",
        "昼食 (ちゅうしょく) – lunch",
        "電話 (でんわ) – phone call",
        "メール (メール) – email",
        "コーヒー (コーヒー) – coffee",
        "友達 (ともだち) – friend",
        "家族 (かぞく) – family",
        "買い物 (かいもの) – shopping",
        "勉強 (べんきょう) – study",
        "朝食 (ちょうしょく) – breakfast",
        "夕食 (ゆうしょく) – dinner",
        "散歩 (さんぽ) – walk",
        "読書 (どくしょ) – reading",
        "映画 (えいが) – movie",
        "音楽 (おんがく) – music",
        "運動 (うんどう) – exercise",
        "料理 (りょうり) – cooking",
        "掃除 (そうじ) – cleaning",
        "洗濯 (せんたく) – laundry"
    ]

    sample_sentences = [
        "今日は忙しい一日でした。",
        "会議が長くて疲れました。",
        "昼食に寿司を食べました。",
        "友達と電話で話しました。",
        "新しい本を買いました。",
        "朝早く起きて散歩しました。",
        "コーヒーを飲みながら勉強しました。",
        "家族と一緒に夕食を食べました。",
        "映画を見てリラックスしました。",
        "音楽を聞きながら料理しました。"
    ]

    try:
        # Return more comprehensive lesson data
        selected_words = random.sample(
            sample_words, min(15, len(sample_words)))
        selected_sentences = random.sample(
            sample_sentences, min(8, len(sample_sentences)))

        print(
            f"Lesson bot generated: {len(selected_words)} words, {len(selected_sentences)} sentences")

        return {
            "words": selected_words,
            "sentences": selected_sentences
        }
    except Exception as e:
        print(f"Lesson bot error: {e}")
        # Return basic fallback content
        return {
            "words": [
                "今日 (きょう) – today",
                "勉強 (べんきょう) – study",
                "日本語 (にほんご) – Japanese",
                "ありがとう (ありがとう) – thank you",
                "こんにちは (こんにちは) – hello"
            ],
            "sentences": [
                "今日は日本語を勉強しました。",
                "ありがとうございます。",
                "こんにちは、元気ですか？"
            ]
        }
