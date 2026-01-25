#!/usr/bin/env python3
"""
Ultra-Fast Vocabulary Extractor for Hypr-Voice
Optimized for <100ms performance using pre-compiled regex and set-based lookups
Based on text-conv-context.py with integration for Hypr-Voice context system
"""

import re
import json
import logging
from typing import List, Set, FrozenSet, Dict, Optional
from functools import lru_cache
from pathlib import Path
import time

logger = logging.getLogger(__name__)

# Pre-compiled regex patterns (compile once, use many times)
CAMEL_CASE_PATTERN = re.compile(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b')
ACRONYM_PATTERN = re.compile(r'\b[A-Z]{2,}\b')
KEBAB_CASE_PATTERN = re.compile(r'\b[a-z]+(?:-[a-z0-9]+)+\b')
SNAKE_CASE_PATTERN = re.compile(r'\b[a-z]+(?:_[a-z0-9]+)+\b')
DOTTED_PATTERN = re.compile(r'\b[a-zA-Z]+\.[a-zA-Z]+(?:\.[a-zA-Z]+)*\b')
ALPHANUMERIC_PATTERN = re.compile(r'\b[a-z]+\d+[a-z]*\b')
WORD_PATTERN = re.compile(r'\b[A-Za-z][\w-]*\b')
UPPERCASE_WORD_PATTERN = re.compile(r'\b[A-Z][a-zA-Z]*\b')

# Compound technical term patterns (pre-compiled)
COMPOUND_PATTERNS = [
    re.compile(r'\b(?:semantic|vector|hybrid|sparse|dense)\s+(?:search|retrieval|embeddings?)\b', re.I),
    re.compile(r'\b(?:machine|deep|artificial)\s+(?:learning|intelligence)\b', re.I),
    re.compile(r'\b(?:natural|programming)\s+language\b', re.I),
    re.compile(r'\b(?:knowledge|vector|graph)\s+(?:base|database|store)\b', re.I),
    re.compile(r'\b(?:REST|GraphQL|WebSocket)\s+API\b', re.I),
    re.compile(r'\bmerkle\s+tree\b', re.I),
    re.compile(r'\bAST\s+parsing\b', re.I),
    re.compile(r'\btoken\s+(?:efficient|aware|window)\b', re.I),
    re.compile(r'\b(?:Kubernetes|Docker|PostgreSQL)\s+(?:cluster|container|database)\b', re.I),
]

# Minimal high-frequency English words (frozen set for O(1) lookup)
STOPWORDS: FrozenSet[str] = frozenset({
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
    'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
    'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
    'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their',
    'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go',
    'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know',
    'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them',
    'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over',
    'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first',
    'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day',
    'most', 'us', 'is', 'was', 'are', 'been', 'has', 'had', 'were', 'said', 'did',
    'file', 'files', 'data', 'using', 'used', 'based', 'via', 'default'
})


class UltraFastVocabularyExtractor:
    """
    Ultra-fast vocabulary extractor optimized for <100ms performance

    Features:
    - Pre-compiled regex patterns for all common code/technical patterns
    - O(1) stopword lookups using frozen set
    - LRU cache for technical word detection
    - Set-based deduplication
    - Early exit on target count
    """

    def __init__(self, target_count: int = 100, min_length: int = 2):
        """
        Initialize the ultra-fast vocabulary extractor

        Args:
            target_count: Target number of vocabulary terms to extract
            min_length: Minimum word length to consider
        """
        self.target_count = target_count
        self.min_length = min_length
        self.stopwords = STOPWORDS

        # Statistics for debugging
        self.stats = {
            'extractions': 0,
            'total_terms': 0,
            'avg_time_ms': 0.0
        }

    @lru_cache(maxsize=1000)
    def _is_technical(self, word: str) -> bool:
        """
        Cached check if word is technical (O(1) after first call)

        Technical indicators:
        - Has internal uppercase (CamelCase)
        - Contains special chars (-, _, .)
        - Mixed alphanumeric (sha256, pgvector)

        Args:
            word: Word to check

        Returns:
            True if word appears technical
        """
        # Has internal uppercase (CamelCase)
        if len(word) > 1 and any(c.isupper() for c in word[1:]):
            return True

        # Contains special chars
        if '-' in word or '_' in word or '.' in word:
            return True

        # Mixed alphanumeric
        has_digit = False
        has_alpha = False
        for c in word:
            if c.isdigit():
                has_digit = True
            elif c.isalpha():
                has_alpha = True
            if has_digit and has_alpha:
                return True

        return False

    def extract_unique_vocabulary(
        self,
        text: str,
        target_count: Optional[int] = None,
        min_length: Optional[int] = None
    ) -> List[str]:
        """
        Ultra-fast vocabulary extraction using pure regex and sets
        Target: <100ms for typical context text

        Args:
            text: Text to extract vocabulary from
            target_count: Override default target count
            min_length: Override default minimum length

        Returns:
            List of unique vocabulary terms sorted by length (desc)
        """
        start_time = time.perf_counter()

        target_count = target_count or self.target_count
        min_length = min_length or self.min_length

        # Use set for O(1) lookups and automatic deduplication
        terms: Set[str] = set()

        # 1. Extract CamelCase/PascalCase (e.g., TypeScript, PostgreSQL)
        terms.update(CAMEL_CASE_PATTERN.findall(text))

        # 2. Extract acronyms (e.g., API, REST, MCP)
        terms.update(ACRONYM_PATTERN.findall(text))

        # 3. Extract kebab-case (e.g., api-server, mcp-server)
        terms.update(KEBAB_CASE_PATTERN.findall(text))

        # 4. Extract snake_case (e.g., ingest_crawl)
        terms.update(SNAKE_CASE_PATTERN.findall(text))

        # 5. Extract dotted names (e.g., claudeContext.index)
        terms.update(DOTTED_PATTERN.findall(text))

        # 6. Extract alphanumeric terms (e.g., sha256, pgvector)
        terms.update(ALPHANUMERIC_PATTERN.findall(text))

        # 7. Extract compound technical terms
        for pattern in COMPOUND_PATTERNS:
            terms.update(pattern.findall(text))

        # 8. Extract capitalized words (likely proper nouns/tech terms)
        uppercase_words = UPPERCASE_WORD_PATTERN.findall(text)
        terms.update(w for w in uppercase_words if len(w) >= min_length)

        # 9. Extract all words and filter intelligently
        all_words = WORD_PATTERN.findall(text)
        for word in all_words:
            if len(word) >= min_length:
                word_lower = word.lower()
                # Fast filtering: not stopword AND (technical OR long)
                if word_lower not in self.stopwords:
                    if self._is_technical(word) or len(word) >= 6:
                        terms.add(word)

        # Convert to list and deduplicate case-insensitively
        unique_terms = []
        seen_lower = set()

        # Sort for deterministic output (longer terms first - more specific)
        sorted_terms = sorted(terms, key=lambda x: (-len(x), x.lower()))

        for term in sorted_terms:
            term_lower = term.lower()
            # Skip if seen, is stopword, or too short
            if (term_lower not in seen_lower and
                term_lower not in self.stopwords and
                len(term) >= min_length):
                unique_terms.append(term)
                seen_lower.add(term_lower)

                # Early exit if we have enough
                if len(unique_terms) >= target_count:
                    break

        # Update statistics
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        self.stats['extractions'] += 1
        self.stats['total_terms'] += len(unique_terms)
        self.stats['avg_time_ms'] = (
            (self.stats['avg_time_ms'] * (self.stats['extractions'] - 1) + elapsed_ms) /
            self.stats['extractions']
        )

        logger.debug(
            f"Extracted {len(unique_terms)} terms in {elapsed_ms:.2f}ms "
            f"(avg: {self.stats['avg_time_ms']:.2f}ms)"
        )

        return unique_terms


class BatchVocabularyExtractor:
    """
    Batch processor for multiple text sources with caching
    Use this when processing multiple context sources (clipboard, terminal, UI, etc.)
    """

    def __init__(self, target_count: int = 100, min_length: int = 2):
        """
        Initialize batch vocabulary extractor

        Args:
            target_count: Target vocabulary size
            min_length: Minimum word length
        """
        self.extractor = UltraFastVocabularyExtractor(target_count, min_length)
        self.global_vocabulary: Set[str] = set()
        self.source_stats: Dict[str, int] = {}

    def add_context(
        self,
        source_name: str,
        text: str,
        target_count: Optional[int] = None
    ) -> List[str]:
        """
        Add context and extract vocabulary incrementally
        Maintains a global vocabulary set across all contexts

        Args:
            source_name: Name of the source (e.g., 'clipboard', 'shell')
            text: Text to extract from
            target_count: Max terms for this source

        Returns:
            List of terms extracted from this source
        """
        terms = self.extractor.extract_unique_vocabulary(
            text,
            target_count=target_count or self.extractor.target_count
        )
        self.global_vocabulary.update(terms)
        self.source_stats[source_name] = len(terms)
        return terms

    def get_vocabulary(self, max_terms: Optional[int] = None) -> List[str]:
        """
        Get deduplicated vocabulary from all contexts

        Args:
            max_terms: Maximum terms to return (sorted by length)

        Returns:
            Sorted vocabulary list
        """
        max_terms = max_terms or self.extractor.target_count
        sorted_vocab = sorted(
            self.global_vocabulary,
            key=lambda x: (-len(x), x.lower())
        )
        return sorted_vocab[:max_terms]

    def reset(self):
        """Clear global vocabulary and stats"""
        self.global_vocabulary.clear()
        self.source_stats.clear()

    def get_stats(self) -> Dict:
        """Get extraction statistics"""
        return {
            'total_unique_terms': len(self.global_vocabulary),
            'source_stats': self.source_stats.copy(),
            'extractor_stats': self.extractor.stats.copy()
        }


def benchmark_extraction(text: str, iterations: int = 10) -> Dict:
    """
    Benchmark the extraction speed

    Args:
        text: Text to extract from
        iterations: Number of iterations

    Returns:
        Benchmark results dictionary
    """
    extractor = UltraFastVocabularyExtractor()

    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        vocab = extractor.extract_unique_vocabulary(text, target_count=50)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        times.append(elapsed)

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    results = {
        'iterations': iterations,
        'avg_time_ms': avg_time,
        'min_time_ms': min_time,
        'max_time_ms': max_time,
        'terms_extracted': len(vocab),
        'target_met': avg_time < 100  # Target is <100ms
    }

    logger.info(
        f"Benchmark ({iterations} iterations): "
        f"Avg={avg_time:.2f}ms, Min={min_time:.2f}ms, "
        f"Max={max_time:.2f}ms, Terms={len(vocab)}, "
        f"Target_met={results['target_met']}"
    )

    return results


# Singleton instance for easy access
_extractor_instance: Optional[UltraFastVocabularyExtractor] = None


def get_vocabulary_extractor(
    target_count: int = 100,
    min_length: int = 2
) -> UltraFastVocabularyExtractor:
    """
    Get or create the global vocabulary extractor instance

    Args:
        target_count: Target vocabulary size
        min_length: Minimum word length

    Returns:
        Vocabulary extractor instance
    """
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = UltraFastVocabularyExtractor(target_count, min_length)
    return _extractor_instance
