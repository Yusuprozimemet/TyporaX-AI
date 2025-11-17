# tools/anki.py
import csv
import os


def export_anki(lesson, user_id):
    from src.utils.utils import ensure_dir
    ensure_dir(f"data/users/{user_id}")

    words = lesson.get("words", [])
    sentences = lesson.get("sentences", [])

    path = f"data/users/{user_id}/genelingua_anki.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Front", "Back", "Example"])

        # Process all words, cycling through sentences if needed
        for i, word_entry in enumerate(words):
            try:
                if "–" in word_entry:
                    japanese_part = word_entry.split("–")[0].strip()
                    english_part = word_entry.split("–")[1].strip()

                    # Use sentences cyclically
                    example_sentence = sentences[i % len(
                        sentences)] if sentences else "例文がありません。"

                    writer.writerow(
                        [japanese_part, english_part, example_sentence])
            except Exception as e:
                print(f"Error processing word {word_entry}: {e}")
                continue

    return path
