#!/usr/bin/env python3
"""
Test vocabulary enhancement with custom words.
"""

from vocabulary_manager import get_vocabulary_manager
import sys

def test_vocabulary():
    """Test vocabulary corrections."""
    vm = get_vocabulary_manager()
    vm.update_vocabulary('global')
    
    print("=" * 60)
    print("VOCABULARY TEST")
    print("=" * 60)
    
    # Test cases with common misrecognitions
    test_cases = [
        # Format: (input, expected)
        ("i use docker and kubernetes", None),  # Should enhance
        ("deploy with terraform to aws", None),  # Should enhance
        ("the api uses graphql", None),  # Should enhance
        ("zykairotis is a custom word", None),  # Should pass through
        ("hyprland wayland compositor", None),  # Depends if added
        ("using get hub actions", None),  # Common misrecognition
    ]
    
    print(f"\nActive vocabulary: {vm.current_vocabulary}")
    print(f"Total keywords: {len(vm.active_keywords)}\n")
    
    for test_input, expected in test_cases:
        result = vm.post_process_transcription(test_input)
        
        # Color output
        if result != test_input:
            print(f"✓ Input:  {test_input}")
            print(f"  Output: \033[92m{result}\033[0m")
        else:
            print(f"• Input:  {test_input}")
            print(f"  Output: {result}")
        
        if expected and result != expected:
            print(f"  ⚠ Expected: {expected}")
        print()

def test_specific_word(word: str):
    """Test if a specific word is in vocabulary."""
    vm = get_vocabulary_manager()
    vm.update_vocabulary('global')
    
    match = vm._find_best_vocabulary_match(word.lower())
    
    if match:
        print(f"✓ '{word}' → '{match}' (found in vocabulary)")
    else:
        print(f"✗ '{word}' not found in vocabulary (will pass through unchanged)")
    
    # Test in context
    test_text = f"testing {word} in a sentence"
    result = vm.post_process_transcription(test_text)
    print(f"\nTest: '{test_text}'")
    print(f"Result: '{result}'")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific word
        test_specific_word(sys.argv[1])
    else:
        # Run all tests
        test_vocabulary()
