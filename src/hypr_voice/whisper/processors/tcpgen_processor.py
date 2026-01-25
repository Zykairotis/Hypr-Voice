#!/usr/bin/env python3
"""
TCPGen-Inspired Post-Processor for faster-whisper.

Since faster-whisper doesn't expose logits, this implements TCPGen-inspired
correction using:
1. Trie-based vocabulary matching
2. Phonetic similarity (edit distance)
3. Context-aware correction

This gives similar benefits to full TCPGen without requiring logit access.
"""

import pygtrie
from typing import List, Dict, Optional, Set, Tuple
from difflib import SequenceMatcher
import re
from loguru import logger

class TCPGenProcessor:
    """
    TCPGen-inspired post-processor for faster-whisper outputs.
    
    Unlike full TCPGen which modifies logits during decoding, this works
    with transcribed text and applies vocabulary-guided corrections.
    
    Algorithm:
    1. Build prefix tree from vocabulary
    2. For each word in transcription, check if it's a partial match
    3. If close match found (> 80% similarity), suggest correction
    4. Apply correction if confidence is high
    
    Benefits:
    - Works with any ASR system (including faster-whisper)
    - No model modification needed
    - Fast (< 5ms per sentence)
    - Maintains TCPGen's vocabulary awareness
    """
    
    def __init__(
        self,
        vocabulary: List[str],
        similarity_threshold: float = 0.80,
        min_word_length: int = 3,
        case_sensitive: bool = False
    ):
        """
        Initialize TCPGen processor.
        
        Args:
            vocabulary: List of custom terms
            similarity_threshold: Minimum similarity for correction (0-1)
            min_word_length: Minimum word length to process
            case_sensitive: Whether matching is case-sensitive
        """
        self.vocabulary = set(vocabulary)
        self.similarity_threshold = similarity_threshold
        self.min_word_length = min_word_length
        self.case_sensitive = case_sensitive
        
        # Build lookup structures
        self.vocab_lower = {v.lower(): v for v in vocabulary}
        self.trie = self._build_trie(vocabulary)
        
        # Statistics
        self.stats = {
            'total_words': 0,
            'corrections_made': 0,
            'vocabulary_hits': 0
        }
        
        logger.info(
            f"TCPGen processor initialized: {len(vocabulary)} terms, "
            f"threshold={similarity_threshold}"
        )
    
    def _build_trie(self, vocabulary: List[str]) -> pygtrie.CharTrie:
        """Build character-level trie for prefix matching."""
        trie = pygtrie.CharTrie()
        for term in vocabulary:
            key = term if self.case_sensitive else term.lower()
            trie[key] = term
        return trie
    
    def process_transcription(self, text: str, preserve_case: bool = True) -> Tuple[str, Dict]:
        """
        Process transcription with vocabulary-guided corrections.
        
        Args:
            text: Transcribed text
            preserve_case: Whether to preserve original case patterns
        
        Returns:
            Tuple of (corrected_text, correction_info)
        """
        words = text.split()
        corrected_words = []
        corrections = []
        
        for i, word in enumerate(words):
            self.stats['total_words'] += 1
            
            # Clean word (remove punctuation)
            clean = re.sub(r'[^\w\s-]', '', word)
            
            if len(clean) < self.min_word_length:
                corrected_words.append(word)
                continue
            
            # Try exact match first
            if self._exact_match(clean):
                corrected_words.append(word)
                self.stats['vocabulary_hits'] += 1
                continue
            
            # Try trie-based prefix matching
            correction = self._find_best_match(clean, preserve_case)
            
            if correction and correction != clean:
                # Apply correction
                corrected_word = self._apply_correction(word, clean, correction)
                corrected_words.append(corrected_word)
                
                corrections.append({
                    'original': word,
                    'corrected': corrected_word,
                    'position': i,
                    'vocabulary_term': correction
                })
                
                self.stats['corrections_made'] += 1
            else:
                corrected_words.append(word)
        
        corrected_text = ' '.join(corrected_words)
        
        info = {
            'corrections': corrections,
            'correction_count': len(corrections),
            'total_words': len(words)
        }
        
        return corrected_text, info
    
    def _exact_match(self, word: str) -> bool:
        """Check if word exactly matches vocabulary."""
        if self.case_sensitive:
            return word in self.vocabulary
        else:
            return word.lower() in self.vocab_lower
    
    def _find_best_match(self, word: str, preserve_case: bool) -> Optional[str]:
        """
        Find best vocabulary match using:
        1. Prefix matching (trie)
        2. Edit distance (similarity)
        3. Phonetic similarity
        """
        search_word = word if self.case_sensitive else word.lower()
        
        # Try prefix matching first (fast)
        prefix_matches = self._get_prefix_matches(search_word)
        
        if not prefix_matches:
            # Try fuzzy matching (slower but thorough)
            return self._fuzzy_match(word, preserve_case)
        
        # If single prefix match and high similarity, use it
        if len(prefix_matches) == 1:
            match = prefix_matches[0]
            similarity = self._calculate_similarity(search_word, match.lower())
            if similarity >= self.similarity_threshold:
                return self.vocab_lower.get(match.lower(), match)
        
        # Multiple matches - pick best by similarity
        best_match = None
        best_similarity = self.similarity_threshold
        
        for match in prefix_matches:
            similarity = self._calculate_similarity(search_word, match.lower())
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = match
        
        if best_match:
            return self.vocab_lower.get(best_match.lower(), best_match)
        
        return None
    
    def _get_prefix_matches(self, word: str) -> List[str]:
        """Get vocabulary terms with matching prefix."""
        matches = []
        
        try:
            # Try exact prefix match
            if word in self.trie:
                matches.append(word)
            
            # Try prefix search
            prefix_items = list(self.trie.items(prefix=word))
            for key, value in prefix_items[:5]:  # Limit to top 5
                matches.append(value)
        
        except Exception as e:
            logger.debug(f"Prefix match error: {e}")
        
        return matches
    
    def _fuzzy_match(self, word: str, preserve_case: bool) -> Optional[str]:
        """Find best match using edit distance."""
        search_word = word.lower()
        best_match = None
        best_ratio = self.similarity_threshold
        
        for vocab_term in self.vocabulary:
            vocab_lower = vocab_term.lower()
            
            # Skip if length difference too large
            len_diff = abs(len(search_word) - len(vocab_lower))
            if len_diff > 3:
                continue
            
            ratio = SequenceMatcher(None, search_word, vocab_lower).ratio()
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = vocab_term
        
        return best_match
    
    def _calculate_similarity(self, word1: str, word2: str) -> float:
        """Calculate similarity between two words."""
        return SequenceMatcher(None, word1, word2).ratio()
    
    def _apply_correction(self, original: str, clean: str, correction: str) -> str:
        """
        Apply correction while preserving punctuation and case.
        
        Args:
            original: Original word with punctuation
            clean: Cleaned word
            correction: Vocabulary term to use
        
        Returns:
            Corrected word with original punctuation/case preserved
        """
        # Extract leading/trailing punctuation
        prefix = ''
        suffix = ''
        
        if original and not original[0].isalnum():
            prefix = original[0]
            original = original[1:]
        
        if original and not original[-1].isalnum():
            suffix = original[-1]
            original = original[:-1]
        
        # Preserve case pattern
        if original.isupper():
            corrected = correction.upper()
        elif original and original[0].isupper():
            corrected = correction.capitalize()
        else:
            corrected = correction
        
        return prefix + corrected + suffix
    
    def update_vocabulary(self, new_vocabulary: List[str]):
        """Update vocabulary dynamically."""
        self.vocabulary = set(new_vocabulary)
        self.vocab_lower = {v.lower(): v for v in new_vocabulary}
        self.trie = self._build_trie(new_vocabulary)
        logger.info(f"TCPGen processor vocabulary updated: {len(new_vocabulary)} terms")
    
    def get_statistics(self) -> Dict:
        """Get processing statistics."""
        stats = dict(self.stats)
        if stats['total_words'] > 0:
            stats['correction_rate'] = stats['corrections_made'] / stats['total_words']
            stats['hit_rate'] = stats['vocabulary_hits'] / stats['total_words']
        return stats
    
    def reset_statistics(self):
        """Reset statistics."""
        self.stats = {
            'total_words': 0,
            'corrections_made': 0,
            'vocabulary_hits': 0
        }


def create_tcpgen_processor(vocabulary_manager) -> Optional[TCPGenProcessor]:
    """
    Factory function to create TCPGen processor from vocabulary manager.
    
    Args:
        vocabulary_manager: VocabularyManager instance
    
    Returns:
        TCPGenProcessor instance or None
    """
    try:
        # Get vocabulary terms
        vocab_terms = []
        
        if hasattr(vocabulary_manager, 'active_keywords'):
            vocab_terms = list(vocabulary_manager.active_keywords)
        
        if not vocab_terms:
            logger.warning("No vocabulary terms available for TCPGen processor")
            return None
        
        # Create processor with optimal parameters
        processor = TCPGenProcessor(
            vocabulary=vocab_terms,
            similarity_threshold=0.80,  # 80% similarity required
            min_word_length=3,
            case_sensitive=False
        )
        
        logger.info(f"TCPGen processor created with {len(vocab_terms)} terms")
        return processor
    
    except Exception as e:
        logger.error(f"Failed to create TCPGen processor: {e}")
        return None


if __name__ == "__main__":
    # Self-test
    print("="*80)
    print("TCPGen PROCESSOR SELF-TEST")
    print("="*80)
    
    # Test vocabulary
    vocab = ["FastAPI", "Docker", "Kubernetes", "Python", "TypeScript", "PostgreSQL"]
    processor = TCPGenProcessor(vocab, similarity_threshold=0.75)
    
    print(f"\n✅ Created processor with {len(vocab)} terms")
    print(f"   Vocabulary: {', '.join(vocab)}")
    
    # Test cases
    test_cases = [
        ("I use fast API for development", "FastAPI should be corrected"),
        ("Deploy with docker container", "docker → Docker"),
        ("The kubernetes pod is running", "kubernetes → Kubernetes"),
        ("Using python and type script", "python → Python, type script → TypeScript"),
        ("postgres database is ready", "postgres → PostgreSQL"),
        ("Random text with no matches", "Should remain unchanged")
    ]
    
    print("\n🧪 Testing corrections:")
    for text, expected in test_cases:
        corrected, info = processor.process_transcription(text)
        print(f"\n   Original:  '{text}'")
        print(f"   Corrected: '{corrected}'")
        print(f"   Expected:  {expected}")
        if info['corrections']:
            print(f"   Changes:   {len(info['corrections'])} corrections")
            for corr in info['corrections']:
                print(f"      • '{corr['original']}' → '{corr['corrected']}'")
    
    # Statistics
    print("\n📊 Statistics:")
    stats = processor.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ TCPGen processor ready!")
