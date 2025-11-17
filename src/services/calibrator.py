# agents/calibrator.py
def run_calibrator(dna_percentile, mbti):
    if dna_percentile > 70:
        focus = "Immersion-Heavy"
        blocks = ["90min input", "20min SRS"]
    elif dna_percentile < 30:
        focus = "Structured + Phonics"
        blocks = ["60min explicit", "30min drill"]
    else:
        focus = "Balanced"
        blocks = ["70min input", "20min SRS"]
    return {"focus": focus, "blocks": blocks, "dna_tip": f"DNA: {dna_percentile}th %ile"}
