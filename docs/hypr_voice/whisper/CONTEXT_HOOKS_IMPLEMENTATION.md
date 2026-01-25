# Context & Hooks System Implementation Status

## ✅ Completed

### 1. Application Categorizer (`scripts/app_categorizer.py`)
- Dynamic categorization using `.desktop` files
- Maps executables to freedesktop.org categories
- User-defined category mappings via patterns
- Heuristic fallback for unknown apps
- Caching for performance
- Test mode: `python scripts/app_categorizer.py --test`

### 2. Categories Configuration (`config/categories.yaml`)
- 6 main categories: development, communication, productivity, media, gaming, system
- Pattern-based matching (e.g., "cursor", "zen", "discord")
- Freedesktop category mapping
- Extensive application coverage (100+ apps)
- Heuristic keywords for fallback detection

### 3. Hook Manager (`hooks/hook_manager.py`)
- Async hook execution with timeout protection
- Supports bash, Python, and executable scripts
- JSON context passing via stdin
- Output capture to stdout/stderr
- Pattern matching for window_change and keyword triggers
- Concurrent hook execution
- Error isolation (hook failures don't crash system)
- Test mode: `python hooks/hook_manager.py --test --trigger cursor`

## 🚧 Remaining Tasks

### 4. Hooks Configuration (`config/hooks.yaml`)
Create configuration file defining hooks:

```yaml
hooks:
  git_context:
    trigger_type: "window_change"
    trigger_patterns: ["cursor", "code", "nvim"]
    script_path: "hooks/scripts/git_context.sh"
    timeout: 10
    pass_context: true
    output_target: "context"
    enabled: true
  
  project_vocabulary:
    trigger_type: "window_change"
    trigger_patterns: ["cursor", "code"]
    script_path: "hooks/scripts/extract_project_vocab.py"
    timeout: 15
    pass_context: true
    output_target: "vocabulary"
    enabled: true
  
  browser_research:
    trigger_type: "keyword"
    trigger_patterns: ["search", "research", "look up"]
    script_path: "hooks/scripts/browser_tabs.sh"
    timeout: 5
    pass_context: false
    output_target: "context"
    enabled: true
```

### 5. Hook Scripts

#### `hooks/scripts/git_context.sh`
```bash
#!/bin/bash
# Extract git info from current directory

read -r context

GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)

if [ -n "$GIT_ROOT" ]; then
    BRANCH=$(git branch --show-current 2>/dev/null)
    STATUS=$(git status --short 2>/dev/null | head -5)
    
    jq -n \
        --arg branch "$BRANCH" \
        --arg status "$STATUS" \
        --arg root "$GIT_ROOT" \
        '{
            context: {
                git_branch: $branch,
                git_status: $status,
                project_root: $root
            }
        }'
else
    echo '{"context": {}}'
fi
```

#### `hooks/scripts/extract_project_vocab.py`
```python
#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def extract_vocabulary(context):
    vocabulary = set()
    project_root = context.get('workspace', {}).get('project_root')
    
    if not project_root:
        return []
    
    project_path = Path(project_root)
    
    # Read package.json
    if (project_path / 'package.json').exists():
        with open(project_path / 'package.json') as f:
            data = json.load(f)
            for deps in ['dependencies', 'devDependencies']:
                if deps in data:
                    vocabulary.update(data[deps].keys())
    
    return {'vocabulary': list(vocabulary)[:50]}

if __name__ == '__main__':
    context = json.load(sys.stdin)
    result = extract_vocabulary(context)
    print(json.dumps(result))
```

### 6. Context Manager Enhancement (`context_manager.py`)
Add LLM-ready JSON formatting:

```python
def get_llm_context(self, window_info: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Get organized JSON context for LLM consumption.
    
    Returns:
        {
            "workspace": {
                "application": str,
                "category": str,
                "window_title": str,
                "active_file": str | null
            },
            "recent_activity": {
                "commands": List[str],  # Last 10
                "clipboard": List[str],  # Last 3
                "keywords": List[str]   # Extracted vocabulary
            },
            "project_context": {
                "git_branch": str | null,
                "git_status": str | null,
                "project_root": str | null
            },
            "hooks": {
                "triggered": List[str],
                "context_additions": Dict
            }
        }
    """
    from scripts.app_categorizer import get_categorizer
    
    context = {
        "workspace": {},
        "recent_activity": {},
        "project_context": {},
        "hooks": {}
    }
    
    # Workspace info
    if window_info:
        categorizer = get_categorizer()
        cat_result = categorizer.categorize(
            window_info.get('class', ''),
            window_info.get('title', '')
        )
        
        context["workspace"] = {
            "application": window_info.get('class', ''),
            "category": cat_result['category'],
            "window_title": window_info.get('title', ''),
            "active_file": self._extract_file_from_title(window_info.get('title', ''))
        }
    
    # Recent activity
    commands = self.get_shell_history(10)
    clipboard = self.get_clipboard_history(3)
    vocab = self.extract_vocabulary_from_context(commands, clipboard)
    
    context["recent_activity"] = {
        "commands": commands,
        "clipboard": clipboard,
        "keywords": list(vocab)
    }
    
    return context

def _extract_file_from_title(self, title: str) -> Optional[str]:
    """Extract file path from window title."""
    import re
    # Common patterns: "file.py - Cursor", "~/project/main.ts", etc.
    patterns = [
        r'([~/][\w/.-]+\.\w+)',  # Path with extension
        r'([\w.-]+\.\w+)\s*[-—]',  # Filename before dash
    ]
    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            return match.group(1)
    return None
```

### 7. Integration with Hybrid Server (`hybrid_server.py`)

```python
# At module level
from hooks.hook_manager import get_hook_manager
from scripts.app_categorizer import get_categorizer

# Initialize hooks
hook_manager = get_hook_manager()
app_categorizer = get_categorizer()

# In TranscriptionSession.__init__
self.session_context = {}
self.last_app = None

# In transcribe_audio endpoint (before processing)
# Trigger window_change hooks
if application_detector:
    window_info = application_detector.get_active_window()
    app_class = window_info.get('class', '')
    
    if app_class != sessions[session_id].last_app:
        # Application changed, trigger hooks
        llm_context = vocabulary_manager.context_manager.get_llm_context(window_info)
        
        hook_results = await hook_manager.trigger_hooks(
            'window_change',
            app_class,
            llm_context
        )
        
        # Store context
        sessions[session_id].session_context = hook_results
        sessions[session_id].last_app = app_class
        
        # Add hook vocabulary
        if hook_results['vocabulary_additions']:
            vocabulary_manager.add_custom_words(
                'hook_vocabulary',
                hook_results['vocabulary_additions']
            )
```

## Testing

### Test Categorizer
```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice/src/Hypr-Whisper
python scripts/app_categorizer.py --test
python scripts/app_categorizer.py --app cursor
```

### Test Hook Manager
```bash
python hooks/hook_manager.py --test
python hooks/hook_manager.py --test --trigger cursor --type window_change
```

### Test Full Integration
1. Start server with hooks enabled
2. Switch between applications (Cursor, Zen, Discord)
3. Monitor logs for hook triggers
4. Verify context additions in transcription

## Architecture

```
┌─────────────────────────────────────┐
│   Application Change / Keyword      │
│   Detected by app_detector          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   ApplicationCategorizer            │
│   - .desktop file parsing           │
│   - Pattern matching                │
│   - Returns: category, confidence   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   HookManager                       │
│   - Matches trigger patterns        │
│   - Executes scripts (bash/py/rust) │
│   - Passes JSON context via stdin   │
│   - Captures stdout/stderr          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Hook Scripts                      │
│   - git_context.sh                  │
│   - extract_project_vocab.py        │
│   - browser_tabs.sh                 │
│   - custom user scripts...          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Output Processing                 │
│   - context_additions → LLM context │
│   - vocabulary_additions → Whisper  │
│   - hook_results → logging          │
└─────────────────────────────────────┘
```

## Next Steps

1. ✅ Create hooks.yaml configuration
2. ✅ Create hook scripts (git_context.sh, extract_project_vocab.py)
3. ✅ Add get_llm_context() to context_manager.py
4. ✅ Integrate hooks into hybrid_server.py
5. ⬜ Test hook system end-to-end
6. ⬜ Document hook creation for users
7. ⬜ Update frontend to display context/hooks

## Notes

- Hooks run **asynchronously** to avoid blocking transcription
- **Timeout protection**: Scripts killed after timeout (default 30s)
- **Error isolation**: Hook failures logged, don't crash server
- **Security**: Script paths validated, stdin/stdout sanitized
- **Performance**: Hooks execute concurrently

