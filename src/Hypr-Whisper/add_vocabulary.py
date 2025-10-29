#!/usr/bin/env python3
"""
Quick utility to add new words to the vocabulary system.
Usage: python add_vocabulary.py
"""

import yaml
import sys
from pathlib import Path
from typing import List, Tuple

def add_words_to_vocabulary(words: List[Tuple[str, str]], category: str = "technical_terms"):
    """
    Add new words to vocabulary.yaml
    
    Args:
        words: List of (incorrect, correct) tuples
        category: Category to add words to
    """
    config_path = Path(__file__).parent / "config" / "vocabulary.yaml"
    
    # Load existing vocabulary
    with open(config_path, 'r') as f:
        vocab = yaml.safe_load(f)
    
    # Ensure structure exists
    if 'global' not in vocab:
        vocab['global'] = {}
    if category not in vocab['global']:
        vocab['global'][category] = []
    
    # Add new words (avoid duplicates)
    existing = set(vocab['global'][category])
    for incorrect, correct in words:
        if correct not in existing:
            vocab['global'][category].append(correct)
            print(f"✓ Added: {correct}")
        else:
            print(f"⚠ Already exists: {correct}")
    
    # Save back
    with open(config_path, 'w') as f:
        yaml.dump(vocab, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"\n✓ Vocabulary updated in {config_path}")

def add_custom_corrections(corrections: dict):
    """
    Add words that need specific corrections.
    
    Args:
        corrections: Dict of {misspelled: correct} mappings
    """
    config_path = Path(__file__).parent / "config" / "vocabulary.yaml"
    
    with open(config_path, 'r') as f:
        vocab = yaml.safe_load(f)
    
    # Add to common_corrections section
    if 'global' not in vocab:
        vocab['global'] = {}
    if 'common_corrections' not in vocab['global']:
        vocab['global']['common_corrections'] = {}
    
    vocab['global']['common_corrections'].update(corrections)
    
    with open(config_path, 'w') as f:
        yaml.dump(vocab, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"✓ Added {len(corrections)} corrections")

def interactive_add():
    """Interactive mode to add words."""
    print("=" * 60)
    print("ADD WORDS TO VOCABULARY")
    print("=" * 60)
    print("\nChoose an option:")
    print("1. Add technical terms")
    print("2. Add product/company names")
    print("3. Add common misspellings")
    print("4. Add custom corrections")
    print("5. Exit")
    
    choice = input("\nChoice (1-5): ").strip()
    
    if choice == "1":
        print("\nEnter technical terms (one per line, empty line to finish):")
        terms = []
        while True:
            term = input("> ").strip()
            if not term:
                break
            terms.append((term.lower(), term))
        if terms:
            add_words_to_vocabulary(terms, "technical_terms")
    
    elif choice == "2":
        print("\nEnter product/company names (one per line, empty line to finish):")
        names = []
        while True:
            name = input("> ").strip()
            if not name:
                break
            names.append((name.lower(), name))
        if names:
            add_words_to_vocabulary(names, "product_names")
    
    elif choice == "3":
        print("\nEnter common misspellings (format: 'wrong -> correct', empty line to finish):")
        corrections = {}
        while True:
            line = input("> ").strip()
            if not line:
                break
            if ' -> ' in line:
                wrong, correct = line.split(' -> ', 1)
                corrections[wrong.strip()] = correct.strip()
        if corrections:
            add_custom_corrections(corrections)
    
    elif choice == "4":
        print("\nEnter custom corrections (format: 'whisper_hears -> should_be'):")
        corrections = {}
        while True:
            line = input("> ").strip()
            if not line:
                break
            if ' -> ' in line:
                wrong, correct = line.split(' -> ', 1)
                corrections[wrong.strip().lower()] = correct.strip()
        if corrections:
            add_custom_corrections(corrections)

# Quick examples to add words programmatically
def add_examples():
    """Add example words to show how it works."""
    
    # Example 1: Add technical terms
    tech_terms = [
        ("zykairotis", "Zykairotis"),
        ("hyprland", "Hyprland"),
        ("wayland", "Wayland"),
        ("pipewire", "PipeWire"),
        ("wireplumber", "WirePlumber"),
    ]
    
    # Example 2: Add product names
    products = [
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic"),
        ("claude", "Claude"),
        ("gpt4", "GPT-4"),
    ]
    
    # Example 3: Common corrections
    corrections = {
        "hyphen": "Hypr",  # If Whisper often hears "hyphen" instead of "Hypr"
        "kates": "k8s",    # Kubernetes shorthand
        "get hub": "GitHub",
        "pie torch": "PyTorch",
    }
    
    print("Adding example words...")
    add_words_to_vocabulary(tech_terms, "technical_terms")
    add_words_to_vocabulary(products, "product_names")
    add_custom_corrections(corrections)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--examples":
        add_examples()
    else:
        interactive_add()
