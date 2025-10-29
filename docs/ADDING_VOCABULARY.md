# Adding Custom Words to Hypr-Voice Vocabulary

## Quick Answer

**New words pass through unchanged** - the system only corrects words it recognizes with 85%+ confidence.

## Adding Words - 3 Methods

### Method 1: Direct Edit (Fastest)

Edit `src/Hypr-Whisper/config/vocabulary.yaml`:

```yaml
global:
  technical_terms:
    - "YourNewWord"  # Add here
```

**No restart needed!** Changes apply immediately.

### Method 2: Interactive Script

```bash
cd src/Hypr-Whisper
./add_vocabulary.py

# Choose option:
# 1 = Technical terms (Docker, Kubernetes, etc.)
# 2 = Product names (OpenAI, GitHub, etc.)
# 3 = Common mistakes (get hub -> GitHub)
```

### Method 3: Programmatic

```python
from vocabulary_manager import get_vocabulary_manager
vm = get_vocabulary_manager()

# The vocabulary is loaded from YAML files
# To add permanently, edit the YAML files
```

## Examples

### Adding a New Technical Term

```bash
# Option 1: Direct edit
nano src/Hypr-Whisper/config/vocabulary.yaml
# Add "Zykairotis" under technical_terms

# Option 2: Interactive
./add_vocabulary.py
# Choose 1, type "Zykairotis", press Enter twice
```

### Fixing Common Whisper Mistakes

If Whisper often hears "hyper land" instead of "Hyprland":

```bash
./add_vocabulary.py
# Choose 3 (common misspellings)
# Type: hyper land -> Hyprland
# Press Enter twice
```

## How It Works

1. **Exact Match First**: Checks if word exists in vocabulary (case-insensitive)
2. **Fuzzy Match**: If no exact match, looks for 85%+ similar words
3. **Preserve Case**: Keeps vocabulary's capitalization (Docker, not docker)
4. **Skip Common Words**: Ignores "the", "and", "with", etc. to avoid false matches

## Test Your Vocabulary

```bash
# Test all vocabulary
./test_vocabulary.py

# Test specific word
./test_vocabulary.py docker

# Output shows:
# ✓ 'docker' → 'Docker' (corrected)
# • 'zykairotis' → 'zykairotis' (passed through)
```

## Common Patterns

### Company/Product Names
```yaml
technical_terms:
  - "OpenAI"
  - "Anthropic"
  - "GitHub"
  - "GitLab"
```

### Technical Acronyms
```yaml
technical_terms:
  - "API"      # Not "api"
  - "REST"     # Not "rest"
  - "GraphQL"  # Not "graphql"
  - "CI/CD"    # Not "ci/cd"
```

### Framework Names
```yaml
technical_terms:
  - "PyTorch"    # Not "pytorch"
  - "TensorFlow" # Not "tensorflow"
  - "Node.js"    # Not "nodejs"
```

### Common Corrections
```yaml
common_corrections:
  "get hub": "GitHub"
  "pie torch": "PyTorch"
  "hyper land": "Hyprland"
  "kates": "k8s"
```

## File Structure

```
config/
├── vocabulary.yaml          # Main vocabulary
└── vocabularies/
    ├── development.yaml    # Dev-specific
    ├── productivity.yaml   # Business terms
    └── gaming.yaml        # Gaming terms
```

## Tips

1. **Use Proper Capitalization**: Add "Docker" not "docker"
2. **Test After Adding**: Run `test_vocabulary.py` to verify
3. **Group Related Terms**: Keep vocabulary organized by category
4. **Handle Variations**: Add common misspellings Whisper makes

## Vocabulary Stats

Check what's loaded:
```python
from vocabulary_manager import get_vocabulary_manager
vm = get_vocabulary_manager()
vm.update_vocabulary('global')
print(f"Total keywords: {len(vm.active_keywords)}")
print(f"Vocabularies: {list(vm.vocabularies.keys())}")
```

## When Words Don't Correct

If a word isn't being corrected:

1. **Check it's in vocabulary**:
   ```bash
   grep -i "yourword" config/vocabulary.yaml
   ```

2. **Test directly**:
   ```bash
   ./test_vocabulary.py yourword
   ```

3. **Verify threshold**: Word must match 85%+ to be corrected

4. **Check stop words**: Common words like "use", "the" are skipped

## Live Updates

The vocabulary system **reloads on every transcription**, so:
- Edit YAML file
- Next transcription uses new vocabulary
- No server restart needed!
