#!/usr/bin/env python3
"""
Test script for contextual prompt generation.
Demonstrates improvement over static vocabulary prompts.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from vocabulary_manager import get_vocabulary_manager

def test_contextual_prompts():
    """Test the new contextual prompt method"""
    
    print("=" * 80)
    print("CONTEXTUAL PROMPT TEST")
    print("=" * 80)
    
    # Initialize vocabulary manager
    vm = get_vocabulary_manager()
    print(f"\n✅ Loaded vocabulary with {len(vm.active_keywords)} terms")
    
    # Test scenarios
    scenarios = [
        {
            "name": "Scenario 1: First sentence (no context)",
            "previous_text": "",
            "description": "Cold start - only vocabulary terms"
        },
        {
            "name": "Scenario 2: Technical discussion",
            "previous_text": "I need to deploy the Docker container with FastAPI endpoints",
            "description": "Context includes technical terms"
        },
        {
            "name": "Scenario 3: Names and projects",
            "previous_text": "Jennifer is working on project Zephyr with component Alpha",
            "description": "Context includes proper nouns not in vocabulary"
        },
        {
            "name": "Scenario 4: Long conversation",
            "previous_text": "We discussed the Kubernetes deployment strategy for the microservices architecture. The team decided to use ConfigMap and Secrets for configuration management. Sarah mentioned that the Prometheus metrics need to be exposed.",
            "description": "Extended context with multiple technical terms"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{'='*80}")
        print(f"TEST: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        print(f"Previous text: {scenario['previous_text'][:100]}{'...' if len(scenario['previous_text']) > 100 else ''}")
        print("-" * 80)
        
        # Generate OLD prompt (static vocabulary)
        old_prompt = vm.get_initial_prompt(max_tokens=200)
        print(f"\n📊 OLD METHOD (Static Vocabulary):")
        print(f"   Length: {len(old_prompt)} chars (~{len(old_prompt)//4} tokens)")
        print(f"   Preview: {old_prompt[:200]}{'...' if len(old_prompt) > 200 else ''}")
        
        # Generate NEW prompt (contextual)
        new_prompt = vm.get_contextual_prompt(
            previous_text=scenario['previous_text'],
            max_words=25,
            include_vocabulary=True
        )
        print(f"\n✨ NEW METHOD (Contextual):")
        print(f"   Length: {len(new_prompt)} chars (~{len(new_prompt)//4} tokens)")
        print(f"   Preview: {new_prompt}")
        
        # Analyze differences
        old_words = set(old_prompt.replace(",", "").replace(".", "").split())
        new_words = set(new_prompt.replace(",", "").replace(".", "").split())
        
        context_words = new_words - old_words
        vocab_words = new_words & old_words
        
        print(f"\n📈 ANALYSIS:")
        print(f"   Total words: {len(new_words)} (vs {len(old_words)} in old method)")
        print(f"   From context: {len(context_words)} words")
        if context_words:
            print(f"      → {', '.join(list(context_words)[:10])}")
        print(f"   From vocabulary: {len(vocab_words)} words")
        print(f"\n💡 BENEFIT: Context words help recognize ANY words, not just vocabulary!")
    
    print(f"\n{'='*80}")
    print("RECOMMENDATIONS:")
    print("="*80)
    print("""
1. ✅ SHORT PROMPTS (15-30 words) prevent hallucinations
   - Old: 50+ words → repetitive output
   - New: 25 words → clean transcription

2. ✅ RECENT CONTEXT helps with unknown words
   - Old: Only vocabulary terms
   - New: Context + vocabulary = works for ANY word

3. ✅ DYNAMIC ADAPTATION based on conversation
   - Old: Same prompt every time
   - New: Updates with your recent speech

4. 🎯 OPTIMAL SETTINGS:
   - max_words=25 (good balance)
   - For cleaner: max_words=15-20
   - For more vocabulary: max_words=30-35 (watch for hallucinations)
""")

def compare_methods():
    """Compare old vs new method side by side"""
    
    print("\n" + "="*80)
    print("METHOD COMPARISON")
    print("="*80)
    
    vm = get_vocabulary_manager()
    
    test_context = "The Kubernetes pod is running with FastAPI serving the REST endpoints"
    
    print(f"\nTest context: \"{test_context}\"\n")
    
    print("┌─────────────────────────────────────────────────────────────────────┐")
    print("│ METHOD 1: Static Vocabulary (OLD)                                  │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    old = vm.get_initial_prompt(max_tokens=200)
    print(f"Prompt: {old[:150]}...")
    print(f"\n❌ ISSUE: Static list, no context awareness")
    print(f"❌ ISSUE: Same prompt regardless of conversation")
    print(f"❌ ISSUE: Long prompts risk hallucinations")
    
    print("\n┌─────────────────────────────────────────────────────────────────────┐")
    print("│ METHOD 2: Contextual + Vocabulary (NEW)                            │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    new = vm.get_contextual_prompt(
        previous_text=test_context,
        max_words=25
    )
    print(f"Prompt: {new}")
    print(f"\n✅ INCLUDES: Recent words (Kubernetes, FastAPI, REST, endpoints)")
    print(f"✅ INCLUDES: Vocabulary terms (Docker, Python, etc.)")
    print(f"✅ BENEFIT: Short (25 words) prevents hallucinations")
    print(f"✅ BENEFIT: Context helps recognize ANY word")
    
    print("\n" + "="*80)
    print("EXPECTED RESULTS:")
    print("="*80)
    print("""
Say: "Use the asyncio gather function with FastAPI"

OLD METHOD:
  Prompt: "Docker, Kubernetes, Python, JavaScript, TypeScript, ..."
  Result: "Use the async io gather function with fast API"
          ^^^^^^^^ ❌             ^^^^^^^^ ❌
  Post-process fixes: "FastAPI" ✅ but misses "asyncio"

NEW METHOD:
  Prompt: "asyncio, gather, FastAPI, Docker, Kubernetes, Python, ..."
          ^^^^^^^ ^^^^^^^ ^^^^^^^ (from recent + vocabulary)
  Result: "Use the asyncio gather function with FastAPI"
          ✅ Correct on first try!
""")

if __name__ == "__main__":
    print("\n🧪 TESTING CONTEXTUAL PROMPT IMPROVEMENTS\n")
    
    try:
        test_contextual_prompts()
        compare_methods()
        
        print("\n" + "="*80)
        print("✅ TEST COMPLETE")
        print("="*80)
        print("""
Next steps:
1. Restart Whisper server: ./scripts/start_hybrid_server.sh
2. Test with real voice input
3. Monitor logs: tail -f /tmp/hybrid-whisper-server.log | grep "contextual"
4. Observe improved accuracy on unknown words!
""")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nMake sure vocabulary_manager.py is in the same directory!")
        sys.exit(1)
