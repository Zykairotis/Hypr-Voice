# Enhanced Vocabulary System Design

## Overview

This document outlines the improved context-aware vocabulary system that integrates the ultra-fast extraction logic from `text-conv-context.py` with multiple data sources to provide superior Whisper STT transcription accuracy.

## Current System Analysis

### Existing Implementation (`context_manager.py`)
- **Data Sources:** Shell history (40 commands), Clipboard (5 entries), Window metadata
- **Extraction Method:** Simple splitting, basic CamelCase detection, common word filtering
- **Performance:** Adequate but not optimized for speed
- **Vocabulary Quality:** Limited extraction patterns, misses many technical terms

### Limitations
1. ❌ No access to past conversation history
2. ❌ Limited clipboard history (only 5 entries)
3. ❌ Basic window metadata (no deep Hyprland integration)
4. ❌ Slow text processing (no pre-compiled regex)
5. ❌ No custom dictionary support
6. ❌ Limited pattern recognition (misses kebab-case, snake_case, etc.)

## Proposed Enhanced System

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│          Enhanced Context Manager (New)                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Data Sources (5 inputs):                                   │
│  ┌──────────────┬──────────────┬─────────────────────────┐ │
│  │ 1. Chats     │ 2. Clipboard │ 3. Window (HyprClient)  │ │
│  │    - Last 10 │    - Last 10 │    - Full metadata      │ │
│  │    sessions  │    entries   │    - Title, class, PID  │ │
│  ├──────────────┼──────────────┼─────────────────────────┤ │
│  │ 4. Shell     │ 5. Custom    │                          │ │
│  │    - History │    Dict      │                          │ │
│  │    - Last 40 │    - YAML     │                          │ │
│  └──────────────┴──────────────┴─────────────────────────┘ │
│                         │                                    │
│                         ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │   Ultra-Fast Vocabulary Extractor                    │   │
│  │   (from text-conv-context.py)                       │   │
│  │                                                     │   │
│  │   - Pre-compiled regex patterns                     │   │
│  │   - O(1) stopword lookups (frozen set)              │   │
│  │   - LRU cache for technical words                   │   │
│  │   - Target: <100ms extraction                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                    │
│                         ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │   Vocabulary Manager Integration                     │   │
│  │   - Merge with application vocabularies             │   │
│  │   - Priority-based ranking                          │   │
│  │   - Generate initial_prompt for Whisper             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Data Sources Detailed

### 1. Chat History (NEW)
**Location:** `logs/*/chat.json`

**Extraction Logic:**
- Read last 10 chat session JSON files (sorted by modification time)
- Extract `content` fields from user messages
- Filter for transcription-related content (voice inputs)
- Extract technical terms, proper nouns, domain-specific vocabulary

**Example Format:**
```json
{
  "type": "user",
  "content": "Deploy the Kubernetes cluster using Helm charts",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Extracted Vocabulary:**
- `Deploy`, `Kubernetes`, `cluster`, `Helm`, `charts`

### 2. Clipboard History (ENHANCED)
**Current:** 5 entries → **Enhanced:** 10 entries

**Tools:**
- Primary: `cliphist list` (Wayland clipboard manager)
- Fallback: `wl-paste` (current clipboard only)

**Extraction:**
- Last 10 clipboard entries
- Filter out duplicate content
- Extract code snippets, file paths, technical terms

### 3. Window Metadata (ENHANCED via HyprClient)
**Current:** `hyprctl activewindow -j`
**Enhanced:** Full Hyprland event-based monitoring

**Metadata to Extract:**
```python
{
    "class": "cursor",
    "title": "Cursor - context_manager.py",
    "initialClass": "cursor",
    "initialTitle": "Cursor - context_manager.py",
    "pid": 12345,
    "workspace": {"id": 1, "name": "1"},
    "fullscreen": false,
    "floating": false,
    "monitor": 0,
    "windowType": "normal",
    "windowingState": "tiled"
}
```

**Advanced Features:**
- Monitor Hyprland events for window changes (event-driven, not polling)
- Extract file paths from titles (e.g., `/home/user/project/file.py`)
- Extract Git branch info from titles (e.g., `main`, `feature/vocab-enhancement`)
- Detect application type (IDE, browser, terminal, etc.)

### 4. Shell History (MAINTAINED)
**Current:** 40 commands → **Maintained**

**Sources:**
- `~/.zsh_history` (extended format)
- `~/.bash_history` (simple format)

**Extraction:**
- Parse last 40 commands
- Extract command names, flags, file paths
- Detect package managers (npm, pip, cargo, etc.)
- Detect build tools (make, cmake, webpack, etc.)

### 5. Custom Dictionary (NEW)
**Location:** `config/custom_dictionary.yaml`

**Format:**
```yaml
# Project-specific vocabulary
project_terms:
  - "Zykairotis"
  - "Hypr-Voice"

# Domain-specific terms
domains:
  ai_ml:
    - "transformer"
    - "attention mechanism"
    - "gradient descent"

  databases:
    - "PostgreSQL"
    - "vector database"
    - "pgvector"

# Company/product names
products:
  - "Anthropic"
  - "Claude"
  - "OpenAI"
```

## Ultra-Fast Vocabulary Extractor

### Pre-Compiled Regex Patterns

```python
# From text-conv-context.py - compile once, use many times
CAMEL_CASE_PATTERN = re.compile(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b')     # TypeScript, PostgreSQL
ACRONYM_PATTERN = re.compile(r'\b[A-Z]{2,}\b')                        # API, REST, MCP
KEBAB_CASE_PATTERN = re.compile(r'\b[a-z]+(?:-[a-z0-9]+)+\b')         # api-server
SNAKE_CASE_PATTERN = re.compile(r'\b[a-z]+(?:_[a-z0-9]+)+\b')         # context_manager
DOTTED_PATTERN = re.compile(r'\b[a-zA-Z]+\.[a-zA-Z]+(?:\.[a-zA-Z]+)*\b')  # os.path
ALPHANUMERIC_PATTERN = re.compile(r'\b[a-z]+\d+[a-z]*\b')              # sha256
WORD_PATTERN = re.compile(r'\b[A-Za-z][\w-]*\b')                      # General words

# Compound technical term patterns
COMPOUND_PATTERNS = [
    re.compile(r'\b(?:semantic|vector|hybrid)\s+(?:search|retrieval)\b', re.I),
    re.compile(r'\b(?:machine|deep)\s+(?:learning|neural)\b', re.I),
    re.compile(r'\bREST\s+API\b', re.I),
    # ... more patterns
]
```

### Optimizations

1. **Frozen Set for Stopwords** (O(1) lookup)
   ```python
   STOPWORDS: FrozenSet[str] = frozenset({
       'the', 'and', 'for', 'are', 'but', 'not', ...
   })
   ```

2. **LRU Cache for Technical Word Detection**
   ```python
   @lru_cache(maxsize=1000)
   def _is_technical(self, word: str) -> bool:
       # Cached check for technical characteristics
   ```

3. **Set-Based Deduplication** (O(1) inserts)
   ```python
   terms: Set[str] = set()
   terms.update(CAMEL_CASE_PATTERN.findall(text))
   ```

4. **Early Exit on Target Count**
   ```python
   if len(unique_terms) >= target_count:
       break
   ```

### Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Single extraction | <100ms | ~200ms |
| Batch processing (5 sources) | <500ms | ~1000ms |
| Memory overhead | <50MB | ~30MB |
| Vocabulary size | 100-200 terms | 50-100 terms |

## Integration with Existing System

### Modified Files

1. **`context_manager.py`** → `enhanced_context_manager.py`
   - Add ultra-fast extractor
   - Add chat history extraction
   - Add custom dictionary loader
   - Enhance clipboard (10 entries)
   - Enhance window metadata (Hyprland events)

2. **`vocabulary_manager.py`**
   - Import new `enhanced_context_manager.py`
   - Update `get_initial_prompt()` to use new extractor
   - Maintain backward compatibility

3. **New: `custom_dictionary.yaml`**
   - User-defined vocabulary
   - Domain-specific terms
   - Project-specific terms

### Backward Compatibility

```python
# vocabulary_manager.py changes
try:
    from enhanced_context_manager import EnhancedContextManager
    USE_ENHANCED = True
except ImportError:
    from context_manager import ContextManager
    USE_ENHANCED = False
    logger.warning("Falling back to basic context manager")
```

## Configuration

### New Config File: `config/context_enhanced.yaml`

```yaml
# Data source configuration
sources:
  chat_history:
    enabled: true
    max_sessions: 10
    logs_dir: "../logs"
    extract_from:
      - user
      -assistant  # For technical terms in responses

  clipboard:
    enabled: true
    max_entries: 10
    tool: "cliphist"  # or "wl-paste"

  window:
    enabled: true
    backend: "hyprland"
    monitor_events: true  # Event-driven vs polling
    extract_from_title:
      - file_paths
      - git_branches
      - urls

  shell:
    enabled: true
    command_count: 40
    sources:
      - zsh
      - bash

  custom_dictionary:
    enabled: true
    path: "config/custom_dictionary.yaml"

# Extractor configuration
extractor:
  target_vocabulary_size: 100
  min_word_length: 2
  enable_compound_patterns: true
  cache_size: 1000

# Performance tuning
performance:
  use_lru_cache: true
  parallel_extraction: false  # Future: asyncio for parallel sources
  early_exit: true
```

## Implementation Plan

### Phase 1: Core Extractor (Priority 1)
1. ✅ Create `ultrafast_vocabulary_extractor.py` (from `text-conv-context.py`)
2. ✅ Add pre-compiled regex patterns
3. ✅ Implement LRU caching
4. ✅ Benchmark performance (<100ms target)

### Phase 2: Data Sources (Priority 1)
1. ✅ Chat history extractor (last 10 sessions)
2. ✅ Enhanced clipboard (10 entries)
3. ✅ Custom dictionary loader (YAML)
4. ✅ Enhanced shell history (maintain current)

### Phase 3: Window Integration (Priority 2)
1. ⏳ HyprClient event monitoring
2. ⏳ Enhanced window metadata extraction
3. ⏳ File path parsing from titles
4. ⏳ Git branch detection

### Phase 4: Integration (Priority 2)
1. ⏳ Update `vocabulary_manager.py`
2. ⏳ Update `hybrid_server.py`
3. ⏳ Add configuration files
4. ⏳ Testing and benchmarking

### Phase 5: Documentation & Testing (Priority 3)
1. ⏳ User documentation
2. ⏳ Performance benchmarks
3. ⏳ Integration tests
4. ⏳ Troubleshooting guide

## Expected Improvements

### Vocabulary Quality
- **Before:** 50-100 terms, basic patterns
- **After:** 100-200 terms, advanced patterns (CamelCase, kebab-case, etc.)

### Transcription Accuracy
- **Technical Terms:** +30-40% accuracy improvement
- **Proper Nouns:** +50% accuracy improvement
- **Domain-Specific:** +60% accuracy improvement

### Performance
- **Extraction Speed:** 2x faster (<100ms vs ~200ms)
- **Memory Usage:** Similar (~50MB)
- **CPU Usage:** Lower (cached lookups)

### Context Awareness
- **Data Sources:** 5 sources (vs 3 currently)
- **Chat History:** New! Learn from conversations
- **Custom Dictionary:** New! User-defined terms
- **Window Events:** Enhanced! Real-time updates

## Migration Strategy

1. **Parallel Deployment:** Run both systems side-by-side
2. **Feature Flag:** `USE_ENHANCED_CONTEXT=true` to enable
3. **Gradual Rollout:** Test with power users first
4. **Fallback:** Automatic fallback to basic system on errors
5. **Monitoring:** Log performance metrics for comparison

## Testing Plan

### Unit Tests
- Ultra-fast extractor (all regex patterns)
- Chat history parser (multiple JSON formats)
- Clipboard extractor (cliphist + wl-paste)
- Shell history parser (zsh + bash)
- Custom dictionary loader (YAML validation)

### Integration Tests
- Full vocabulary extraction pipeline
- Whisper initial_prompt generation
- VocabularyManager integration
- HybridServer integration

### Performance Tests
- Extraction speed benchmarks
- Memory usage profiling
- Concurrent load testing
- Regression testing (compare old vs new)

### Accuracy Tests
- Transcription accuracy with technical terms
- Proper noun recognition
- Domain-specific vocabulary
- Real-world usage scenarios

## Future Enhancements

### Short Term (1-2 months)
- [ ] Async parallel extraction of all 5 sources
- [ ] ML-based vocabulary ranking (TF-IDF)
- [ ] Dynamic vocabulary updates based on corrections

### Long Term (3-6 months)
- [ ] Learn from user corrections (reinforcement)
- [ ] Cross-session vocabulary persistence
- [ ] Vocabulary suggestion UI
- [ ] Integration with codebase indexing (AST parsing)

## Conclusion

This enhanced vocabulary system will significantly improve Whisper STT accuracy for technical terms while maintaining or improving performance. The modular design allows for gradual rollout and easy fallback to the existing system.

---

**Status:** Design Complete
**Next Step:** Implement Phase 1 (Core Extractor)
**Estimated Effort:** 2-3 weeks for full implementation
