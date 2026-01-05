# Vocabulary Manager Integration Guide

## Overview

This document explains how to integrate the enhanced context manager into the existing `vocabulary_manager.py` system with backward compatibility.

## Integration Approach

### Option 1: Feature Flag (Recommended)

Add a feature flag to control which context manager to use:

```python
# In vocabulary_manager.py, around line 23-29

# Import ContextManager (existing)
try:
    from context_manager import ContextManager
    HAVE_CONTEXT_MANAGER = True
except ImportError:
    HAVE_CONTEXT_MANAGER = False
    logger.warning("ContextManager not available")

# Import EnhancedContextManager (NEW)
try:
    from enhanced_context_manager import EnhancedContextManager
    HAVE_ENHANCED_CONTEXT = True
except ImportError:
    HAVE_ENHANCED_CONTEXT = False
    logger.info("Enhanced ContextManager not available, using basic version")
```

### Option 2: Environment Variable Control

```python
# In __init__ method of VocabularyManager

use_enhanced = os.environ.get('HYPR_VOICE_ENHANCED_CONTEXT', '').lower() in ('true', '1', 'yes')

if use_enhanced and HAVE_ENHANCED_CONTEXT:
    logger.info("Using Enhanced Context Manager")
    self.context_manager = EnhancedContextManager()
    self._use_enhanced = True
elif HAVE_CONTEXT_MANAGER:
    logger.info("Using Basic Context Manager")
    self.context_manager = ContextManager()
    self._use_enhanced = False
else:
    self.context_manager = None
    self._use_enhanced = False
```

## Modified Methods

### 1. `_get_active_keywords()` - Line 243

**Current Implementation:**
```python
def _get_active_keywords(self, vocab_name: str) -> Set[str]:
    keywords = set()

    # Add global keywords
    # ...

    # Add vocabulary-specific keywords
    # ...

    # Add context-aware keywords from shell history and clipboard
    if self.context_manager:
        try:
            commands = self.context_manager.get_shell_history(40)
            clipboard = self.context_manager.get_clipboard_history(5)
            context_vocab = self.context_manager.extract_vocabulary_from_context(
                commands, clipboard
            )
            keywords.update(context_vocab)
            logger.debug(f"Added {len(context_vocab)} context-aware keywords")
        except Exception as e:
            logger.error(f"Error getting context-aware keywords: {e}")
```

**Enhanced Implementation:**
```python
def _get_active_keywords(self, vocab_name: str) -> Set[str]:
    keywords = set()

    # Add global keywords
    # ...

    # Add vocabulary-specific keywords
    # ...

    # Add context-aware keywords (NEW: Check if enhanced or basic)
    if self.context_manager:
        try:
            if self._use_enhanced:
                # Use enhanced context manager
                result = self.context_manager.extract_comprehensive_vocabulary()
                enhanced_vocab = result.get('vocabulary', [])
                keywords.update(enhanced_vocab)
                logger.info(
                    f"Added {len(enhanced_vocab)} enhanced keywords "
                    f"from {len(result.get('sources', {}))} sources "
                    f"in {result.get('extraction_time_ms', 0):.2f}ms"
                )
            else:
                # Use basic context manager
                commands = self.context_manager.get_shell_history(40)
                clipboard = self.context_manager.get_clipboard_history(5)
                context_vocab = self.context_manager.extract_vocabulary_from_context(
                    commands, clipboard
                )
                keywords.update(context_vocab)
                logger.debug(f"Added {len(context_vocab)} basic context-aware keywords")
        except Exception as e:
            logger.error(f"Error getting context-aware keywords: {e}")

    # Add backend overlay keywords
    # ...

    return keywords
```

### 2. `get_initial_prompt()` - Line 297

**No changes needed** - This method uses `self.active_keywords` which is populated by `_get_active_keywords()`, so it automatically benefits from the enhanced extraction.

## Configuration

### Environment Variables

Add to `.env` or system environment:

```bash
# Enable enhanced context manager
HYPR_VOICE_ENHANCED_CONTEXT=true

# Optional: Custom config path
HYPR_VOICE_ENHANCED_CONFIG_PATH=/path/to/context_enhanced.yaml
```

### Enable Permanently

Add to user profile (`~/.bashrc`, `~/.zshrc`):

```bash
export HYPR_VOICE_ENHANCED_CONTEXT=true
```

## Testing the Integration

### 1. Test Basic Functionality

```python
from vocabulary_manager import VocabularyManager

vm = VocabularyManager()
vm.update_vocabulary(app_name="cursor")

# Check which context manager is being used
print(f"Using enhanced: {vm._use_enhanced}")
print(f"Active keywords: {len(vm.active_keywords)}")
print(f"Prompt: {vm.get_initial_prompt()[:100]}...")
```

### 2. Test Enhanced Manager Directly

```python
from enhanced_context_manager import EnhancedContextManager

ecm = EnhancedContextManager()
result = ecm.extract_comprehensive_vocabulary()

print(f"Vocabulary size: {len(result['vocabulary'])}")
print(f"Sources: {list(result['sources'].keys())}")
print(f"Extraction time: {result['extraction_time_ms']:.2f}ms")

# Get Whisper prompt
prompt = ecm.get_vocabulary_for_whisper()
print(f"Prompt: {prompt[:200]}...")
```

### 3. Benchmark Performance

```python
import time

from vocabulary_manager import VocabularyManager

vm = VocabularyManager()

# Warm up
vm.update_vocabulary(app_name="cursor")

# Benchmark
iterations = 10
times = []

for _ in range(iterations):
    start = time.perf_counter()
    vm.update_vocabulary(app_name="cursor")
    keywords = vm.active_keywords
    elapsed = (time.perf_counter() - start) * 1000
    times.append(elapsed)

avg_time = sum(times) / len(times)
print(f"Average time: {avg_time:.2f}ms")
print(f"Vocabulary size: {len(keywords)}")
```

## Rollback Procedure

If issues occur, simply disable the enhanced context manager:

```bash
# Disable enhanced context manager
export HYPR_VOICE_ENHANCED_CONTEXT=false

# Or unset to use basic
unset HYPR_VOICE_ENHANCED_CONTEXT
```

## Monitoring and Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Statistics

```python
from enhanced_context_manager import get_enhanced_context_manager

ecm = get_enhanced_context_manager()
result = ecm.extract_comprehensive_vocabulary(force_refresh=True)

# Print detailed statistics
print(json.dumps(result['stats'], indent=2))
print("\nSource breakdown:")
for source, stats in result['sources'].items():
    print(f"  {source}: {stats}")
```

## Performance Expectations

| Metric | Basic Manager | Enhanced Manager |
|--------|---------------|------------------|
| Extraction Time | ~200ms | <100ms |
| Vocabulary Size | 50-100 terms | 100-200 terms |
| Data Sources | 3 (shell, clipboard, window) | 5 (+chat, custom dict) |
| Pattern Matching | Basic (CamelCase only) | Advanced (8+ patterns) |
| Clipboard Entries | 5 | 10 |
| Chat History | ❌ No | ✅ Yes (10 sessions) |

## Migration Checklist

- [ ] Install dependencies: `pip install pyyaml` (already installed)
- [ ] Copy new files to `src/Hypr-Whisper/`:
  - [ ] `ultrafast_vocabulary_extractor.py`
  - [ ] `enhanced_context_manager.py`
- [ ] Copy configuration to `src/Hypr-Whisper/config/`:
  - [ ] `context_enhanced.yaml`
  - [ ] `custom_dictionary.yaml`
- [ ] Update `vocabulary_manager.py` with integration code
- [ ] Set environment variable: `export HYPR_VOICE_ENHANCED_CONTEXT=true`
- [ ] Restart hybrid server: `./scripts/start_hybrid_server.sh restart`
- [ ] Test transcription accuracy
- [ ] Monitor performance metrics

## Troubleshooting

### Import Error

```
ImportError: cannot import name 'EnhancedContextManager'
```

**Solution:** Ensure `enhanced_context_manager.py` is in the same directory as `vocabulary_manager.py`

### Configuration Not Found

```
Custom dictionary not found: config/custom_dictionary.yaml
```

**Solution:** Check that configuration files are in `src/Hypr-Whisper/config/`

### Slow Performance

```
Extraction time: 500ms+
```

**Solution:**
1. Check cache is working: `'cached': True` in results
2. Reduce `max_sessions` in configuration
3. Reduce `command_count` in configuration
4. Disable unused data sources

### Missing Vocabulary

If expected vocabulary terms are missing:

1. Check if data sources are enabled in `context_enhanced.yaml`
2. Verify chat history files exist in `logs/`
3. Test clipboard: `cliphist list | head`
4. Test shell history: `tail ~/.zsh_history`
5. Check custom dictionary format is valid YAML

## Next Steps

1. **Integration Testing:** Run comprehensive tests with real transcriptions
2. **Performance Tuning:** Adjust cache TTL and extraction parameters
3. **Accuracy Testing:** Compare transcription accuracy before/after
4. **User Documentation:** Create user guide for customizing vocabulary
5. **Monitoring:** Add metrics to hybrid server logs

---

**Status:** Integration Guide Complete
**Estimated Integration Time:** 30 minutes
**Risk Level:** Low (backward compatible with fallback)
