#!/usr/bin/env python3
"""
Ultra-Fast Context-Aware Vocabulary Extractor for Whisper STT
Optimized for <100ms performance using regex and set-based lookups
"""

import re
import json
from typing import List, Set, FrozenSet
from functools import lru_cache
import time

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


class FastVocabularyExtractor:
    """Ultra-fast vocabulary extractor optimized for <100ms performance"""
    
    def __init__(self):
        self.stopwords = STOPWORDS
        # Cache for repeated extractions
        self._cache = {}
    
    @lru_cache(maxsize=1000)
    def _is_technical(self, word: str) -> bool:
        """Cached check if word is technical (O(1) after first call)"""
        # Has internal uppercase
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
        target_count: int = 50,
        min_length: int = 2
    ) -> List[str]:
        """
        Ultra-fast vocabulary extraction using pure regex and sets
        Target: <100ms for typical context text
        """
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
        
        # 9. Extract all words and filter
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
        
        # Sort for deterministic output (longer terms first)
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
        
        return unique_terms


class BatchVocabularyExtractor(FastVocabularyExtractor):
    """
    Batch processor for multiple text sources with caching
    Use this when processing multiple context sources (clipboard, terminal, UI)
    """
    
    def __init__(self):
        super().__init__()
        self.global_vocabulary: Set[str] = set()
    
    def add_context(self, text: str, target_count: int = 50) -> List[str]:
        """
        Add context and extract vocabulary incrementally
        Maintains a global vocabulary set across all contexts
        """
        terms = self.extract_unique_vocabulary(text, target_count=target_count)
        self.global_vocabulary.update(terms)
        return terms
    
    def get_vocabulary(self, max_terms: int = 100) -> List[str]:
        """Get deduplicated vocabulary from all contexts"""
        sorted_vocab = sorted(
            self.global_vocabulary, 
            key=lambda x: (-len(x), x.lower())
        )
        return sorted_vocab[:max_terms]
    
    def reset(self):
        """Clear global vocabulary"""
        self.global_vocabulary.clear()


def benchmark_extraction(text: str, iterations: int = 10):
    """Benchmark the extraction speed"""
    extractor = FastVocabularyExtractor()
    
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        vocab = extractor.extract_unique_vocabulary(text, target_count=50)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"# Performance Benchmark ({iterations} iterations):")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  Min: {min_time:.2f}ms")
    print(f"  Max: {max_time:.2f}ms")
    print(f"  Terms extracted: {len(vocab)}")
    print()
    
    return vocab


def main():
    example_context = """
    Merkle tree-based change detection: SHA-256 file hashing, Efficient change detection,
    Stores snapshots in ~/.context/merkle/, Only re-indexes modified files.
    
    Project-Aware Storage (Island Architecture). Three-level hierarchy for organizing content:
    Global - Cross-project content, Project - Project-specific content, Dataset - Subdivisions within projects.
    Collection naming: {scope}:{project}:{dataset} (e.g., dataset:myproject:repo1)
    
    MCP Server Integration (mcp-server.js). Model Context Protocol server exposing tools to Claude Desktop:
    Tools: claudeContext.index - Index codebases, claudeContext.search - Semantic search,
    claudeContext.ingestCrawl - Ingest crawled web pages, claudeContext.init - Set default project/dataset,
    claudeContext.defaults - View current settings.
    
    Features: Auto-compiles TypeScript in watch mode, TOON format - Token-efficient responses,
    Progress tracking with callbacks, Persistent defaults in ~/.context/claude-mcp.json
    
    API Services: REST API + WebSocket for real-time progress, Endpoints: ingest, query, smart-query,
    Project-aware APIs with provenance metadata.
    
    Crawl4AI Runner: Python-based web crawler, Extracts and chunks web content,
    Feeds into ingestCrawlPages() API, Dockerized service for distributed crawling.
    
    SPLADE Runner: Sparse lexical embeddings for hybrid search,
    Combines dense (vector) + sparse (keyword) retrieval.
    
    Database Services: PostgreSQL - Metadata + vectors (pgvector), Qdrant - Optional cloud vector DB,
    Neo4j - Knowledge graphs (Cognee integration - being removed).
    
    Technology Stack: TypeScript 5.0, Node.js (runtime), MCP SDK (Model Context Protocol),
    Embeddings: OpenAI, VoyageAI, Gemini, Ollama, Vector DBs: PostgreSQL + pgvector, Qdrant, Milvus, FAISS,
    Code Parsing: Tree-sitter (multi-language AST parsing), Frontend: React 18, Vite, Material-UI, ReactFlow,
    Utilities: chokidar (file watching), fs-extra, glob, ignore.
    """
    
    print("="*60)
    print("FAST VOCABULARY EXTRACTOR - Performance Test")
    print("="*60)
    print()
    
    # Benchmark performance
    vocabulary = benchmark_extraction(example_context, iterations=10)
    
    # Output results
    output = json.dumps(vocabulary, indent=2)
    print("Extracted Vocabulary:")
    print(output)
    print()
    print(f"Total unique terms: {len(vocabulary)}")
    
    # Save to file
    with open('whisper_custom_vocabulary.json', 'w') as f:
        json.dump(vocabulary, f, indent=2)
    print("Saved to: whisper_custom_vocabulary.json")
    
    # Example: Batch processing multiple contexts
    print()
    print("="*60)
    print("BATCH PROCESSING EXAMPLE")
    print("="*60)
    print()
    
    batch_extractor = BatchVocabularyExtractor()
    
    # Simulate multiple context sources
    contexts = {
        'clipboard': 'TypeScript code with React hooks useState useEffect',
        'terminal': 'npm run build && docker compose up -d',
        'ui_elements': 'PostgreSQL connection string API key configuration'
    }
    
    start = time.perf_counter()
    for source, text in contexts.items():
        terms = batch_extractor.add_context(text, target_count=20)
        print(f"{source}: {len(terms)} terms extracted")
    
    final_vocab = batch_extractor.get_vocabulary(max_terms=50)
    elapsed = (time.perf_counter() - start) * 1000
    
    print(f"\nBatch processing time: {elapsed:.2f}ms")
    print(f"Total unique vocabulary: {len(final_vocab)}")


if __name__ == "__main__":
    main()
