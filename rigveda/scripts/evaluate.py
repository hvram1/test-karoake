#!/usr/bin/env python3
"""
Evaluate alignment results from Aeneas.
Generates a summary report of the alignment quality.
"""

import json
from pathlib import Path

OUTPUT_DIR = Path("/Users/hvina/projects/rigveda-sanatana/poc/output")

def analyze_alignment(sync_file: Path) -> dict:
    """Analyze a single alignment file."""
    with open(sync_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fragments = data.get('fragments', [])
    
    if not fragments:
        return {'error': 'No fragments found'}
    
    # Calculate statistics
    word_count = len(fragments)
    total_duration = float(fragments[-1]['end'])
    
    durations = []
    for frag in fragments:
        begin = float(frag['begin'])
        end = float(frag['end'])
        duration = end - begin
        durations.append({
            'word': frag['lines'][0],
            'begin': begin,
            'end': end,
            'duration': duration
        })
    
    avg_duration = sum(d['duration'] for d in durations) / word_count
    min_duration = min(d['duration'] for d in durations)
    max_duration = max(d['duration'] for d in durations)
    
    # Flag potential issues
    issues = []
    for d in durations:
        if d['duration'] < 0.1:
            issues.append(f"Very short: '{d['word']}' ({d['duration']:.2f}s)")
        elif d['duration'] > 5.0:
            issues.append(f"Very long: '{d['word']}' ({d['duration']:.2f}s)")
    
    return {
        'word_count': word_count,
        'total_duration': total_duration,
        'avg_duration': avg_duration,
        'min_duration': min_duration,
        'max_duration': max_duration,
        'durations': durations,
        'issues': issues
    }

def main():
    print("=" * 70)
    print("ALIGNMENT EVALUATION REPORT")
    print("Mandala 1, Sukta 1, Riks 1-9")
    print("=" * 70)
    
    all_results = {}
    total_words = 0
    total_issues = 0
    
    for rik in range(1, 10):
        sync_file = OUTPUT_DIR / f"1.1.{rik}_sync.json"
        if not sync_file.exists():
            print(f"\n[1.1.{rik}] File not found!")
            continue
        
        result = analyze_alignment(sync_file)
        all_results[f"1.1.{rik}"] = result
        
        print(f"\n{'─' * 70}")
        print(f"VERSE 1.1.{rik}")
        print(f"{'─' * 70}")
        print(f"  Words: {result['word_count']}")
        print(f"  Total duration: {result['total_duration']:.2f}s")
        print(f"  Avg word duration: {result['avg_duration']:.2f}s")
        print(f"  Min/Max duration: {result['min_duration']:.2f}s / {result['max_duration']:.2f}s")
        
        print(f"\n  Word timings:")
        for i, d in enumerate(result['durations'], 1):
            print(f"    {i}. [{d['begin']:6.2f}s - {d['end']:6.2f}s] ({d['duration']:4.2f}s) {d['word']}")
        
        if result['issues']:
            print(f"\n  ⚠️  Potential issues:")
            for issue in result['issues']:
                print(f"    - {issue}")
            total_issues += len(result['issues'])
        else:
            print(f"\n  ✓ No obvious issues detected")
        
        total_words += result['word_count']
    
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Total verses processed: {len(all_results)}")
    print(f"  Total words aligned: {total_words}")
    print(f"  Total potential issues: {total_issues}")
    
    if total_issues == 0:
        print(f"\n  ✅ All alignments look reasonable!")
        print(f"     Recommend: Manual spot-check by listening to audio")
    else:
        print(f"\n  ⚠️  Found {total_issues} potential issues to review")
    
    print(f"\n{'=' * 70}")
    print("NEXT STEPS")
    print(f"{'=' * 70}")
    print("  1. Open poc/player/index.html in a browser")
    print("  2. Play audio and watch karaoke highlighting")
    print("  3. Note any words that are mis-timed")
    print("  4. If > 80% accurate, proceed to batch processing")

if __name__ == "__main__":
    main()
