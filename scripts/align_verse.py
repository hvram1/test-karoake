#!/usr/bin/env python3
"""
Align audio and text using Aeneas for Rigveda verses.
Uses Hindi (hi) as language since eSpeak has better Hindi support
and Devanagari phonetics are close enough for alignment.
"""

import json
import os
from pathlib import Path

from aeneas.executetask import ExecuteTask
from aeneas.task import Task
from aeneas.runtimeconfiguration import RuntimeConfiguration

# Paths
AUDIO_DIR = Path("/Users/hvina/projects/rigveda-sanatana/rigveda-audio")
TEXT_DIR = Path("/Users/hvina/projects/rigveda-sanatana/poc/text")
OUTPUT_DIR = Path("/Users/hvina/projects/rigveda-sanatana/poc/output")

def align_verse(mandala: int, sukta: int, rik: int, word_align: bool = True) -> dict:
    """
    Align audio with text for a single verse.
    
    Args:
        mandala: Mandala number (1-10)
        sukta: Sukta number
        rik: Rik number
        word_align: If True, do word-level alignment; otherwise sentence-level
    
    Returns:
        Alignment data as dictionary
    """
    # File paths
    audio_path = AUDIO_DIR / f"{mandala:03d}" / f"{sukta:03d}" / f"{rik:03d}.mp3"
    text_path = TEXT_DIR / f"{mandala}.{sukta}.{rik}.txt"
    output_path = OUTPUT_DIR / f"{mandala}.{sukta}.{rik}_sync.json"
    
    # Verify files exist
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    if not text_path.exists():
        raise FileNotFoundError(f"Text file not found: {text_path}")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Build aeneas configuration
    # Using Hindi (hi) for Sanskrit since eSpeak has better Hindi support
    config_string = "task_language=hi"
    config_string += "|os_task_file_format=json"
    
    rconf = None
    if word_align:
        # Word-level alignment (mplain = one word per line)
        config_string += "|os_task_file_levels=3"
        config_string += "|is_text_type=mplain"
        rconf = RuntimeConfiguration()
        rconf[RuntimeConfiguration.MFCC_MASK_NONSPEECH] = True
        rconf[RuntimeConfiguration.MFCC_MASK_NONSPEECH_L3] = True
    else:
        # Sentence-level alignment (plain = one sentence per line)
        config_string += "|is_text_type=plain"
    
    # Create and configure task
    task = Task(config_string=config_string)
    task.text_file_path_absolute = str(text_path.absolute())
    task.audio_file_path_absolute = str(audio_path.absolute())
    task.sync_map_file_path_absolute = str(output_path.absolute())
    
    # Execute alignment
    print(f"  Aligning {audio_path.name} with {text_path.name}...")
    ExecuteTask(task, rconf=rconf).execute()
    
    # Write output
    task.output_sync_map_file()
    
    # Clean up JSON (remove escaped unicode, pretty print)
    with open(output_path, 'r', encoding='utf8') as f:
        alignment = json.load(f)
    with open(output_path, 'w', encoding='utf8') as f:
        json.dump(alignment, f, ensure_ascii=False, indent=2)
    
    print(f"  Output saved to {output_path}")
    
    return alignment

def print_alignment_summary(alignment: dict) -> None:
    """Print a summary of the alignment results."""
    fragments = alignment.get('fragments', [])
    print(f"\n  Found {len(fragments)} aligned fragments:")
    
    for i, frag in enumerate(fragments[:10]):  # Show first 10
        text = frag.get('lines', [''])[0]
        begin = float(frag.get('begin', 0))
        end = float(frag.get('end', 0))
        duration = end - begin
        print(f"    {i+1:2d}. [{begin:6.2f}s - {end:6.2f}s] ({duration:.2f}s) {text}")
    
    if len(fragments) > 10:
        print(f"    ... and {len(fragments) - 10} more")

def main():
    """Align all verses for Mandala 1, Sukta 1, Riks 1-9."""
    print("Aligning Rigveda verses with audio...")
    print("=" * 50)
    
    mandala = 1
    sukta = 1
    
    results = {}
    
    for rik in range(1, 10):
        print(f"\nProcessing verse {mandala}.{sukta}.{rik}...")
        try:
            alignment = align_verse(mandala, sukta, rik)
            print_alignment_summary(alignment)
            results[f"{mandala}.{sukta}.{rik}"] = "SUCCESS"
        except Exception as e:
            print(f"  ERROR: {e}")
            results[f"{mandala}.{sukta}.{rik}"] = f"FAILED: {e}"
    
    print("\n" + "=" * 50)
    print("Alignment Summary:")
    for verse_id, status in results.items():
        print(f"  {verse_id}: {status}")

if __name__ == "__main__":
    main()
