#!/usr/bin/env python3
"""
Post-process Aeneas sync files using svara markers from original text.

Svara markers in the Rigveda data:
  {0} = anudatta (low tone) - normal duration
  {1} = udatta (high/raised tone) - normal duration  
  {2} = svarita (circumflex/falling tone) - slightly extended
  {5} = pluta/kampa (prolonged) - significantly extended

This script adjusts word timing boundaries based on the relative
svara "weight" of each word compared to its neighbors.
"""

import json
import re
import os
from pathlib import Path
from typing import List, Dict, Tuple

# Paths
DATA_DIR = Path("/Users/hvina/projects/rigveda-sanatana/rigveda-app/src/data")
SYNC_DIR = Path("/Users/hvina/projects/rigveda-sanatana/poc/output")
OUTPUT_DIR = Path("/Users/hvina/projects/rigveda-sanatana/poc/output_adjusted")

# Svara duration weights (relative contribution to word duration)
# These values represent how much "extra" time a svara type adds
SVARA_WEIGHTS = {
    '0': 0.0,    # anudatta - baseline
    '1': 0.0,    # udatta - baseline (same as anudatta for duration)
    '2': 0.08,   # svarita - adds ~80ms per occurrence
    '5': 0.20,   # pluta/kampa - adds ~200ms per occurrence
}

def parse_svara_to_unicode(text_with_markers: str) -> str:
    """
    Convert svara markers to Unicode diacritics.
    {1} = anudatta (॒) - horizontal line below
    {2} = svarita (᳚) - double vertical line above  
    {5} = udatta (॑) - vertical line above
    {0} = no mark (remove)
    """
    return (text_with_markers
        .replace('{1}', '॒')
        .replace('{2}', '᳚')
        .replace('{5}', '॑')
        .replace('{0}', ''))

def extract_svara_info(text_with_markers: str) -> Dict:
    """
    Extract svara counts from text with markers.
    Returns dict with counts of each svara type, clean text, and text with Unicode svaras.
    """
    svara_counts = {'0': 0, '1': 0, '2': 0, '5': 0}
    
    # Count each svara marker
    for match in re.finditer(r'\{(\d)\}', text_with_markers):
        svara_type = match.group(1)
        if svara_type in svara_counts:
            svara_counts[svara_type] += 1
    
    # Remove markers to get clean text
    clean_text = re.sub(r'\{[0-9]+\}', '', text_with_markers)
    
    # Convert to Unicode svara marks
    text_with_unicode_svaras = parse_svara_to_unicode(text_with_markers)
    
    return {
        'clean_text': clean_text,
        'text_with_svaras': text_with_unicode_svaras,
        'svara_counts': svara_counts,
        'total_svaras': sum(svara_counts.values())
    }

def calculate_svara_weight(svara_counts: Dict) -> float:
    """Calculate the total duration weight from svara counts."""
    weight = 0.0
    for svara_type, count in svara_counts.items():
        weight += SVARA_WEIGHTS.get(svara_type, 0.0) * count
    return weight

def extract_words_with_svaras(samhita_lines: List[str]) -> List[Dict]:
    """
    Extract words from samhita lines preserving svara information.
    Returns list of dicts with clean_text, svara_counts, weight.
    """
    words = []
    
    for line in samhita_lines:
        if isinstance(line, str):
            # Split on spaces (preserving markers within words)
            raw_words = line.split()
            for raw_word in raw_words:
                info = extract_svara_info(raw_word)
                info['weight'] = calculate_svara_weight(info['svara_counts'])
                info['raw'] = raw_word
                words.append(info)
    
    return words

def load_verse_data(mandala: int, sukta: int, rik: int) -> Dict:
    """Load verse JSON data."""
    verse_path = DATA_DIR / f"{mandala:03d}" / f"{sukta:03d}" / f"{rik:03d}.json"
    with open(verse_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_sync_data(mandala: int, sukta: int, rik: int) -> Dict:
    """Load Aeneas sync JSON data."""
    sync_path = SYNC_DIR / f"{mandala}.{sukta}.{rik}_sync.json"
    with open(sync_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def adjust_timing(sync_data: Dict, words_with_svaras: List[Dict]) -> Dict:
    """
    Adjust sync timing based on svara weights.
    
    Strategy:
    1. Calculate total svara weight for each word
    2. Redistribute time within the total duration proportionally
    3. Words with more svarita/pluta get more time
    """
    fragments = sync_data.get('fragments', [])
    
    if len(fragments) != len(words_with_svaras):
        print(f"  WARNING: Fragment count ({len(fragments)}) != word count ({len(words_with_svaras)})")
        # Try to match by text
        matched = []
        for frag in fragments:
            frag_text = frag['lines'][0] if frag.get('lines') else ''
            for word_info in words_with_svaras:
                if word_info['clean_text'].strip() == frag_text.strip():
                    matched.append((frag, word_info))
                    break
        if len(matched) != len(fragments):
            print(f"  WARNING: Could not match all fragments, skipping adjustment")
            return sync_data
        words_with_svaras = [m[1] for m in matched]
    
    # Calculate base duration and total weight
    total_duration = float(fragments[-1]['end']) - float(fragments[0]['begin'])
    
    # Calculate weight for each word (base + svara bonus)
    base_weight_per_char = 0.1  # Base weight per character
    word_weights = []
    
    for i, (frag, word_info) in enumerate(zip(fragments, words_with_svaras)):
        # Base weight from character count
        char_count = len(word_info['clean_text'])
        base_weight = char_count * base_weight_per_char
        
        # Add svara bonus
        svara_bonus = word_info['weight']
        
        total_weight = base_weight + svara_bonus
        word_weights.append({
            'index': i,
            'text': word_info['clean_text'],
            'text_with_svaras': word_info.get('text_with_svaras', word_info['clean_text']),
            'base_weight': base_weight,
            'svara_bonus': svara_bonus,
            'total_weight': total_weight,
            'svara_counts': word_info['svara_counts']
        })
    
    # Calculate total weight
    total_weight = sum(w['total_weight'] for w in word_weights)
    
    # Redistribute timing proportionally
    adjusted_fragments = []
    current_time = float(fragments[0]['begin'])
    
    for i, (frag, weight_info) in enumerate(zip(fragments, word_weights)):
        original_begin = float(frag['begin'])
        original_end = float(frag['end'])
        original_duration = original_end - original_begin
        
        # Calculate new duration based on weight proportion
        weight_ratio = weight_info['total_weight'] / total_weight
        new_duration = total_duration * weight_ratio
        
        # Create adjusted fragment
        adjusted_frag = frag.copy()
        adjusted_frag['begin'] = f"{current_time:.3f}"
        adjusted_frag['end'] = f"{current_time + new_duration:.3f}"
        
        # Add text with svara Unicode marks
        adjusted_frag['lines_with_svaras'] = [weight_info['text_with_svaras']]
        
        # Add svara metadata
        adjusted_frag['svara_info'] = {
            'counts': weight_info['svara_counts'],
            'bonus': weight_info['svara_bonus'],
            'original_duration': original_duration,
            'adjusted_duration': new_duration
        }
        
        adjusted_fragments.append(adjusted_frag)
        current_time += new_duration
    
    return {'fragments': adjusted_fragments}

def process_verse(mandala: int, sukta: int, rik: int) -> Tuple[bool, str]:
    """Process a single verse and save adjusted sync."""
    try:
        # Load data
        verse_data = load_verse_data(mandala, sukta, rik)
        sync_data = load_sync_data(mandala, sukta, rik)
        
        # Extract words with svara info
        samhita_lines = verse_data.get('samhita', {}).get('lines', [])
        words_with_svaras = extract_words_with_svaras(samhita_lines)
        
        # Adjust timing
        adjusted_sync = adjust_timing(sync_data, words_with_svaras)
        
        # Save adjusted sync
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = OUTPUT_DIR / f"{mandala}.{sukta}.{rik}_sync.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(adjusted_sync, f, ensure_ascii=False, indent=2)
        
        return True, str(output_path)
    
    except Exception as e:
        return False, str(e)

def compare_timing(original: Dict, adjusted: Dict) -> None:
    """Print comparison of original vs adjusted timing."""
    orig_frags = original.get('fragments', [])
    adj_frags = adjusted.get('fragments', [])
    
    print("\n  Timing Comparison:")
    print("  " + "-" * 70)
    print(f"  {'Word':<20} {'Original':>15} {'Adjusted':>15} {'Diff':>10} {'Svara':<10}")
    print("  " + "-" * 70)
    
    for orig, adj in zip(orig_frags, adj_frags):
        text = orig['lines'][0][:18] if orig.get('lines') else '?'
        orig_dur = float(orig['end']) - float(orig['begin'])
        adj_dur = float(adj['end']) - float(adj['begin'])
        diff = adj_dur - orig_dur
        
        svara_info = adj.get('svara_info', {})
        svara_bonus = svara_info.get('bonus', 0)
        
        diff_str = f"+{diff:.2f}" if diff >= 0 else f"{diff:.2f}"
        print(f"  {text:<20} {orig_dur:>12.2f}s {adj_dur:>12.2f}s {diff_str:>10}s {svara_bonus:>8.2f}")
    
    print("  " + "-" * 70)

def main():
    """Process all verses in the POC."""
    print("=" * 70)
    print("POST-PROCESSING SYNC FILES WITH SVARA ADJUSTMENTS")
    print("=" * 70)
    
    print("\nSvara weight configuration:")
    for svara, weight in SVARA_WEIGHTS.items():
        print(f"  {{{svara}}} = +{weight:.2f}s per occurrence")
    
    mandala = 1
    sukta = 1
    
    for rik in range(1, 10):
        print(f"\n{'─' * 70}")
        print(f"Processing verse {mandala}.{sukta}.{rik}...")
        
        success, result = process_verse(mandala, sukta, rik)
        
        if success:
            print(f"  ✓ Saved to {result}")
            
            # Load and compare
            original = load_sync_data(mandala, sukta, rik)
            with open(result, 'r', encoding='utf-8') as f:
                adjusted = json.load(f)
            compare_timing(original, adjusted)
        else:
            print(f"  ✗ Error: {result}")
    
    print(f"\n{'=' * 70}")
    print("Post-processing complete!")
    print(f"Adjusted files saved to: {OUTPUT_DIR}")
    print("\nTo test, update the player to use './output_adjusted/' instead of './output/'")

if __name__ == "__main__":
    main()
