# Vocabulary and Context Configuration Guide

Complete reference for vocabulary enhancement and context extraction in Hypr-Voice.

## Table of Contents

- [Overview](#overview)
- [Vocabulary Configuration](#vocabulary-configuration)
- [Context Extraction](#context-extraction)
- [Domain-Specific Vocabularies](#domain-specific-vocabularies)
- [Application Categories](#application-categories)
- [Backend Overlays](#backend-overlays)
- [Custom Dictionary](#custom-dictionary)
- [Best Practices](#best-practices)

---

## Overview

Hypr-Voice uses context-aware vocabulary enhancement to improve transcription accuracy for technical terms and domain-specific language.

### How It Works

1. **Application Detection** - Identify the active application
2. **Context Extraction** - Extract relevant context from shell, clipboard, windows
3. **Vocabulary Selection** - Select appropriate vocabulary based on context
4. **Enhancement** - Apply vocabulary to transcription using initial prompts

### Configuration Files

```
config/hypr_voice/whisper/
├── vocabulary.yaml              # Main vocabulary configuration
├── context.yaml                 # Context extraction settings
├── categories.yaml              # Application categories
├── custom_dictionary.yaml       # Custom terms
├── backend_overlays.yaml        # Backend-specific vocab
├── context_enhanced.yaml        # Enhanced context settings
└── vocabularies/
    ├── development.yaml         # Development vocabulary
    ├── gaming.yaml              # Gaming vocabulary
    └── productivity.yaml        # Productivity vocabulary
```

---

## Vocabulary Configuration

### Main Vocabulary File

```yaml
# config/hypr_voice/whisper/vocabulary.yaml

global:
  technical_terms:
    - CLI
    - API
    - GUI
    - IDE
    - SDK
    - CI/CD
    - DevOps
    # ... more terms

  programming:
    keywords:
      - function
      - variable
      - class
      - method
      # ... more keywords

  common_corrections:
    get hub: GitHub
    pie torch: PyTorch
    hyper land: Hyprland

applications:
  terminal:
    window_class_patterns:
      - Alacritty
      - kitty
      - gnome-terminal
    vocabulary:
      shell_commands:
        - ls
        - cd
        - pwd
        # ... more commands

settings:
  enhancement_method: prompt_engineering
  fuzzy_matching: true
  confidence_threshold: 0.7
```

### Vocabulary Structure

#### Global Vocabulary

| Section | Type | Description |
|---------|------|-------------|
| `technical_terms` | list | General technical terms |
| `programming` | dict | Programming-related keywords |
| `common_corrections` | dict | Common misspellings |

#### Application Vocabulary

| Section | Type | Description |
|---------|------|-------------|
| `window_class_patterns` | list | Application window patterns |
| `vocabulary` | dict | Application-specific terms |

#### Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enhancement_method` | string | `"prompt_engineering"` | Enhancement method |
| `fuzzy_matching` | boolean | `true` | Enable fuzzy matching |
| `confidence_threshold` | float | `0.7` | Match confidence threshold |

---

## Context Extraction

### Context Configuration

```yaml
# config/hypr_voice/whisper/context.yaml

application_detection:
  enabled: true
  method: auto                   # auto, hyprland, sway, gnome, kde, x11
  update_interval: 200           # milliseconds
  fallback_behavior: global

shell_history:
  enabled: true
  count: 40                      # Commands to analyze
  sources:
    - ~/.zsh_history
    - ~/.bash_history
  exclude_patterns:
    - "^cd "
    - "^ls "
    - "^pwd$"
  extract:
    - command_names
    - file_paths
    - flags_and_options
    - technical_terms

clipboard_history:
  enabled: true
  count: 5                       # Entries to analyze
  max_entry_length: 500          # Max characters per entry
  tool: cliphist                 # cliphist or wl-paste
  fallback: wl-paste
  extract:
    - technical_terms
    - camel_case_words
    - snake_case_words
    - file_names
    - urls

window_context:
  enabled: true
  extract_from_title: true
  extract_from_class: true
  patterns:
    file_extensions: true
    paths: true
    technical_terms: true

processing:
  merge_strategy: union          # union, intersection, weighted
  priority:
    - window_context
    - shell_history
    - clipboard_history
  deduplication: true
  max_context_items: 200
```

### Context Sources

#### Application Detection

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable detection |
| `method` | string | `"auto"` | Detection method |
| `update_interval` | integer | `200` | Update interval (ms) |
| `fallback_behavior` | string | `"global"` | Fallback behavior |

#### Shell History

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable analysis |
| `count` | integer | `40` | Commands to analyze |
| `sources` | list | - | History files |
| `exclude_patterns` | list | - | Patterns to exclude |

#### Clipboard History

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable analysis |
| `count` | integer | `5` | Entries to analyze |
| `tool` | string | `"cliphist"` | Clipboard tool |
| `max_entry_length` | integer | `500` | Max entry length |

---

## Domain-Specific Vocabularies

### Development Vocabulary

```yaml
# config/hypr_voice/whisper/vocabularies/development.yaml

name: "Development"
description: "Vocabulary for software development"

keywords:
  languages:
    - "javascript"
    - "typescript"
    - "python"
    - "java"
    # ... more languages

  frameworks:
    - "react"
    - "vue"
    - "angular"
    # ... more frameworks

  tools:
    - "git"
    - "docker"
    - "kubernetes"
    # ... more tools

  concepts:
    - "algorithm"
    - "data structure"
    - "object-oriented"
    # ... more concepts

applications:
  window_classes:
    - "code"
    - "Code"
    - "vim"
    - "nvim"
    # ... more patterns

prompts:
  initial: |
    This is a software development context. Please accurately transcribe technical terms.

  fallback: "Focus on technical and programming terminology."
```

### Gaming Vocabulary

```yaml
# config/hypr_voice/whisper/vocabularies/gaming.yaml

name: "Gaming"
description: "Vocabulary for gaming"

keywords:
  genres:
    - "RPG"
    - "MMORPG"
    - "FPS"
    # ... more genres

  gaming_terms:
    - "noob"
    - "pro"
    - "nerf"
    # ... more terms

  games:
    - "World of Warcraft"
    - "League of Legends"
    # ... more games

applications:
  window_classes:
    - "steam"
    - "lutris"
    # ... more patterns
```

### Productivity Vocabulary

```yaml
# config/hypr_voice/whisper/vocabularies/productivity.yaml

name: "Productivity"
description: "Vocabulary for business and productivity"

keywords:
  business:
    - "meeting"
    - "presentation"
    # ... more terms

  project_management:
    - "agile"
    - "scrum"
    - "sprint"
    # ... more terms

applications:
  window_classes:
    - "libreoffice"
    - "firefox"
    # ... more patterns
```

---

## Application Categories

### Categories Configuration

```yaml
# config/hypr_voice/whisper/categories.yaml

categories:
  development:
    description: "Coding, terminals, IDEs"
    patterns:
      - cursor
      - code
      - nvim
      # ... more patterns
    freedesktop_map:
      - Development
      - IDE
      - TerminalEmulator

  communication:
    description: "Chat, email, video calls"
    patterns:
      - discord
      - slack
      # ... more patterns
    freedesktop_map:
      - Network
      - InstantMessaging

  productivity:
    description: "Browsers, documents, notes"
    patterns:
      - firefox
      - chromium
      # ... more patterns
    freedesktop_map:
      - Office
      - WebBrowser

  media:
    description: "Audio players, video players"
    patterns:
      - vlc
      - mpv
      # ... more patterns

  gaming:
    description: "Games, game launchers"
    patterns:
      - steam
      - lutris
      # ... more patterns

  system:
    description: "System utilities"
    patterns:
      - dolphin
      - nautilus
      # ... more patterns

detection:
  use_desktop_files: true
  fallback_to_heuristics: true
  cache_results: true
  cache_ttl: 3600                # seconds
```

### Category Mappings

| Category | Description | Examples |
|----------|-------------|----------|
| `development` | Coding, IDEs | VSCode, vim, IntelliJ |
| `communication` | Chat, email | Discord, Slack, Thunderbird |
| `productivity` | Browsers, docs | Firefox, LibreOffice, Obsidian |
| `media` | Audio/video players | VLC, mpv, Audacity |
| `gaming` | Games, launchers | Steam, Lutris, Minecraft |
| `system` | System utilities | File managers, monitors |

---

## Backend Overlays

### Backend-Specific Vocabulary

```yaml
# config/hypr_voice/whisper/backend_overlays.yaml

backends:
  hyprland:
    keywords:
      - Hyprland
      - wlroots
      - hyprctl

  sway:
    keywords:
      - Sway
      - wlroots
      - swaymsg

  gnome:
    keywords:
      - GNOME
      - Mutter
      - gdbus

  kde:
    keywords:
      - KDE
      - Plasma
      - KWin
      - kdotool

  x11:
    keywords:
      - Xorg
      - EWMH
      - xdotool

  manual:
    keywords: []
```

### Backend Keywords

| Backend | Keywords | Description |
|---------|----------|-------------|
| `hyprland` | Hyprland, wlroots, hyprctl | Hyprland compositor |
| `sway` | Sway, wlroots, swaymsg | Sway compositor |
| `gnome` | GNOME, Mutter, gdbus | GNOME desktop |
| `kde` | KDE, Plasma, KWin | KDE desktop |
| `x11` | Xorg, EWMH, xdotool | X11 window system |

---

## Custom Dictionary

### Custom Terms

```yaml
# config/hypr_voice/whisper/custom_dictionary.yaml

project_terms:
  - "Zykairotis"
  - "Hypr-Voice"
  - "Hyprland"
  - "Whisper"
  - "Wayland"

domains:
  ai_ml:
    - "transformer"
    - "attention mechanism"
    - "neural network"
    # ... more terms

  databases:
    - "PostgreSQL"
    - "vector database"
    # ... more terms

  cloud_infrastructure:
    - "Kubernetes"
    - "Docker"
    - "Terraform"
    # ... more terms

products:
  - "Anthropic"
  - "Claude"
  - "OpenAI"
  # ... more products

programming:
  - "async"
  - "await"
  - "callback"
  # ... more terms

shell_commands:
  - "systemctl"
  - "journalctl"
  - "hyprctl"
  # ... more commands
```

### Domain Sections

| Domain | Description | Examples |
|--------|-------------|----------|
| `project_terms` | Project-specific terms | Zykairotis, Hypr-Voice |
| `ai_ml` | AI/ML terminology | transformer, embedding |
| `databases` | Database terms | PostgreSQL, MongoDB |
| `cloud_infrastructure` | Cloud/DevOps | Kubernetes, Docker |
| `products` | Company/product names | Anthropic, Claude |
| `programming` | Programming keywords | async, await |

---

## Enhanced Context

### Enhanced Context Manager

```yaml
# config/hypr_voice/whisper/context_enhanced.yaml

sources:
  chat_history:
    enabled: true
    max_sessions: 10
    logs_dir: "/home/mewtwo/Zykairotis/Hypr-Voice/logs"
    extract_from:
      - user                      # From user messages

  clipboard:
    enabled: true
    max_entries: 10
    tool: "cliphist"

  window:
    enabled: true
    backend: "auto"
    monitor_events: false
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
    path: "custom_dictionary.yaml"

extractor:
  target_vocabulary_size: 100
  min_word_length: 2
  enable_compound_patterns: true
  cache_size: 1000

performance:
  use_lru_cache: true
  parallel_extraction: false
  early_exit: true

cache:
  ttl_seconds: 5
```

### Enhanced Context Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `chat_history.enabled` | boolean | `true` | Enable chat analysis |
| `clipboard.max_entries` | integer | `10` | Clipboard entries |
| `shell.command_count` | integer | `40` | Commands to analyze |
| `extractor.target_vocabulary_size` | integer | `100` | Target vocab size |
| `cache.ttl_seconds` | integer | `5` | Cache TTL |

---

## Best Practices

### Adding Custom Vocabulary

1. **Identify Domain** - Determine the domain (development, gaming, etc.)
2. **Add Terms** - Add to appropriate vocabulary file
3. **Test** - Test transcription with domain-specific terms
4. **Iterate** - Refine based on results

### Vocabulary Size

| Context | Recommended Size | Reason |
|---------|------------------|--------|
| General | 50-100 terms | Broad coverage |
| Domain-specific | 100-200 terms | Focused coverage |
| Project-specific | 20-50 terms | Narrow coverage |

### Common Mistakes

1. **Too many terms** - Can cause hallucinations
2. **Overlapping terms** - Use deduplication
3. **Poor formatting** - Use consistent comma-separated format
4. **Context mismatch** - Ensure vocabulary matches application

### Performance Tips

1. **Cache vocabularies** - Enable caching for faster loading
2. **Use fuzzy matching** - Improves recognition accuracy
3. **Set appropriate thresholds** - Balance accuracy vs. recall
4. **Regular updates** - Keep vocabularies current

---

## See Also

- [Whisper Configuration](whisper-config.md)
- [Configuration Reference](configuration-reference.md)
- [Environment Variables](environment-variables.md)
