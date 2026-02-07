#!/usr/bin/env python3
"""
Extract words from Rigveda verse JSON for forced alignment.
Outputs one word per line (mplain format for aeneas).
"""

import json
import re
import os
from pathlib import Path

# Paths
DATA_DIR = Path("/Users/hvina/projects/rigveda-sanatana/rigveda-app/src/data")
OUTPUT_DIR = Path("/Users/hvina/projects/rigveda-sanatana/poc/text")

def clean_svara_markers(text: str) -> str:
    """Remove svara markers {0}, {1}, {2}, {5} from text."""
    return re.sub(r'\{[0-9]+\}', '', text)

def extract_words_from_samhita(verse_data: dict) -> list[str]:
    """Extract words from Samhita patha lines."""
    lines = verse_data.get('samhita', {}).get('lines', [])
    words = []
    
    for line in lines:
        if isinstance(line, str):
            clean = clean_svara_markers(line)
            # Split on spaces and filter empty strings
            line_words = [w.strip() for w in clean.split() if w.strip()]
            words.extend(line_words)
        elif isinstance(line, list):
            for part in line:
                if isinstance(part, str):
                    clean = clean_svara_markers(part)
                    line_words = [w.strip() for w in clean.split() if w.strip()]
                    words.extend(line_words)
    
    return words

def process_verse(mandala: int, sukta: int, rik: int) -> tuple[list[str], str]:
    """Process a single verse and return words and output path."""
    # Build path to verse JSON
    verse_path = DATA_DIR / f"{mandala:03d}" / f"{sukta:03d}" / f"{rik:03d}.json"
    
    if not verse_path.exists():
        raise FileNotFoundError(f"Verse file not found: {verse_path}")
    
    with open(verse_path, 'r', encoding='utf-8') as f:
        verse_data = json.load(f)
    
    words = extract_words_from_samhita(verse_data)
    
    # Output file path
    output_path = OUTPUT_DIR / f"{mandala}.{sukta}.{rik}.txt"
    
    return words, str(output_path)

def save_words(words: list[str], output_path: str) -> None:
    """Save words to file, one per line."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(words))
    print(f"  Saved {len(words)} words to {output_path}")

def main():
    """Extract text for Mandala 1, Sukta 1, Riks 1-9."""
    print("Extracting text from Rigveda verses...")
    print("=" * 50)
    
    mandala = 1
    sukta = 1
    
    # Process riks 1-9 (that's what we have audio for)
    for rik in range(1, 10):
        print(f"\nProcessing verse {mandala}.{sukta}.{rik}...")
        try:
            words, output_path = process_verse(mandala, sukta, rik)
            save_words(words, output_path)
            print(f"  Words: {' | '.join(words)}")
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("Text extraction complete!")

if __name__ == "__main__":
    main()
