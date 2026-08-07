"""
Text Column Analysis Service.
Analyzes free-form text columns for length statistics, vocabulary size, and most common words.
"""

from collections import Counter
import re
import pandas as pd


def analyze_text_columns(df: pd.DataFrame) -> dict:
    text_results = {}
    obj_cols = df.select_dtypes(include=["object"]).columns.tolist()

    for col in obj_cols:
        series = df[col].dropna().astype(str)
        if series.empty:
            continue

        avg_len = series.str.len().mean()
        avg_words = series.str.split().str.len().mean()

        # Only process as text column if avg character length > 20 or avg words > 3
        if avg_len < 20 and avg_words < 3:
            continue

        char_lengths = series.str.len()
        words = []
        for text in series:
            tokens = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
            words.extend(tokens)

        word_counts = Counter(words)
        vocab_size = len(word_counts)
        top_words = [
            {"word": word, "count": count} for word, count in word_counts.most_common(10)
        ]

        text_results[col] = {
            "avg_length": round(float(avg_len), 2),
            "min_length": int(char_lengths.min()),
            "max_length": int(char_lengths.max()),
            "vocabulary_size": vocab_size,
            "most_common_words": top_words,
        }

    return text_results
