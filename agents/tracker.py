# agents/tracker.py
import matplotlib.pyplot as plt
import pandas as pd
import os
from tools.utils import load_json, save_json


def run_tracker(user_dir="data/users/alex"):
    progress_path = f"{user_dir}/progress.json"
    progress = load_json(progress_path, {
        "cefr": "A1",
        "vocab": 150,
        "minutes_week": 300,
        "b2_months": 18,
        "total_lessons": 1
    })

    # Realistic progress simulation
    progress["vocab"] += 15  # 15 new words per lesson
    progress["minutes_week"] += 45  # 45 minutes per lesson
    progress["total_lessons"] = progress.get(
        "total_lessons", 0) + 1  # Ensure field exists

    # Calculate B2 timeline based on vocab growth
    vocab_needed_for_b2 = 2500  # Approximate vocab for B2 level
    weekly_vocab_growth = 45  # 3 lessons × 15 words
    weeks_to_b2 = max(
        4, (vocab_needed_for_b2 - progress["vocab"]) / weekly_vocab_growth)
    progress["b2_months"] = round(
        weeks_to_b2 / 4.3, 1)  # Convert weeks to months

    # Update CEFR level based on vocabulary
    if progress["vocab"] < 500:
        progress["cefr"] = "A1"
    elif progress["vocab"] < 1000:
        progress["cefr"] = "A2"
    elif progress["vocab"] < 1500:
        progress["cefr"] = "B1"
    else:
        progress["cefr"] = "B1+"

    # Save
    save_json(progress, progress_path)

    # Create more detailed progress chart
    plt.figure(figsize=(8, 5))
    plt.style.use('default')

    # Generate realistic progress data
    weeks = list(range(1, 9))
    current_vocab = progress["vocab"]
    vocab_history = [max(0, current_vocab - (8-i)*15) for i in range(1, 9)]

    plt.plot(weeks, vocab_history, marker='o',
             linewidth=2.5, markersize=6, color='#27ae60')
    plt.fill_between(weeks, vocab_history, alpha=0.3, color='#27ae60')

    plt.title(
        f'Vocabulary Progress - Current Level: {progress["cefr"]}', fontsize=14, fontweight='bold')
    plt.xlabel('Week', fontsize=12)
    plt.ylabel('Total Vocabulary', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plot_path = f"{user_dir}/progress.png"
    plt.savefig(plot_path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()

    progress["graph"] = plot_path
    return progress
