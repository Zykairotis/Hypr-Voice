# Cross-Desktop Implementation Report (November 20, 2025)

This report captures what was implemented to make Hypr-Whisper's window
introspection work across popular Linux desktops without breaking the existing
Hyprland flow. Everything is additive and guarded by capability checks so
Hyprland users keep the exact behavior they had before.

## What changed (code)
- Added `src/Hypr-Whisper/window_backends.py` with backends for Hyprland, Sway/wlroots, GNOME (Mutter), KDE (KWin via kdotool), generic X11 (xdotool), plus a manual/no-op fallback.
- Added `src/Hypr-Whisper/input_backends.py` to pick a safe typing backend (prefers ydotool → kdotool → wtype → xdotool) and return graceful no-ops on locked-down systems.
- `hypr-voice-type.py` now uses the input dispatcher, preserving ydotool-first behavior but falling back automatically when unavailable.
- Vocabulary is backend-aware: `vocabulary_manager` accepts backend context, loads optional overlays from `config/backend_overlays.yaml`, and emits hook events on backend/vocab changes.
- Hook bus added (`hook_bus.py`) with events for backend_change, window_change, and vocab_change; default emitters are wired in app_detector and vocab_manager.
- `scripts/app_detector.py` now selects a backend via `detect_backend()` and returns normalized window dicts (`backend`, `class`, `title`, `app_id`, `pid`, `workspace`, `raw`, etc.). Hyprland remains first in the priority list.
- `context_manager.py` gained `extract_context_from_window()` (backend-agnostic) while keeping the legacy Hyprland wrapper. Context keywords and metadata now work for all backends.
- `context_websocket_server.py` and `scripts/context_processor.py` now use the backend-agnostic window data instead of hard-coded `hyprctl` calls.
- `config/context.yaml` documents the new `method: auto` setting and the expanded backend list; new optional `config/backend_overlays.yaml` supplies backend-specific keywords.
- New sanity helper: `scripts/backend_health.py` prints detected window/input backends and optionally issues a small typing test (`--type-test`).
- Convenience launcher: `scripts/start_everything.sh start` spins up hybrid server (9099), context WS (9091), and web UI + bridge (8933/8934). Use `stop`/`status` for lifecycle.

## How detection works (runtime flow)
1) On first run, `detect_backend()` auto-detects in order Hyprland → Sway → GNOME → KDE → X11 → manual, writes the result to `~/.cache/hypr-voice/backend.json`, and reuses it on later runs if still available.
2) Each backend is considered only if its CLI is present **and** a quick command succeeds (short timeouts, safe failures).
3) You can force a backend with `HYPR_VOICE_WINDOW_BACKEND` (e.g., `sway`, `gnome`, `kde`, `x11`, `hyprland`, `manual`). If the requested backend is not usable, it falls back to auto and updates the cache.

## How to smoke-test (no extra dependencies)
- Run `python src/Hypr-Whisper/scripts/app_detector.py --test -v` while a window is focused. Expected: prints backend name, class/title, and the vocabulary/context preview. If nothing is detected, it will say "No active window detected" but will not crash.
- Run `python src/Hypr-Whisper/scripts/context_processor.py` in a terminal; it now logs window updates even outside Hyprland when a supported backend is present.
- Run `python src/Hypr-Whisper/scripts/backend_health.py` to see which window/input backends are active. Add `--type-test` if you want it to actually type "Hello" using the selected input backend.

## Safety and compatibility notes
- Hyprland: unchanged behavior; still uses `hyprctl activewindow -j` as the primary path.
- Optional deps: swaymsg, gdbus, kdotool, xdotool are probed but never required; absence only downgrades capability.
- Timeouts: every probe uses ≤1.5s timeouts to avoid hangs on systems where a compositor socket exists but is unreachable.
- Output shape: Returned window dicts keep `class/title/initialClass/initialTitle` so downstream code that expected Hyprland keys continues to work.

## Known limitations / follow-ups
- KDE path relies on `kdotool`; if unavailable, KDE falls back to later backends. A qdbus-based fallback can be added later.
- GNOME DBus Eval may be blocked by corporate lockdown policies; in that case we gracefully return `None` and fall back.
- Input synthesis now dispatches across ydotool/kdotool/wtype/xdotool but cannot overcome compositor-level security policies that fully block synthetic input; in that case we log and no-op rather than crash.

## Files touched
- `src/Hypr-Whisper/window_backends.py` (new)
- `src/Hypr-Whisper/scripts/app_detector.py`
- `src/Hypr-Whisper/context_manager.py`
- `src/Hypr-Whisper/context_websocket_server.py`
- `src/Hypr-Whisper/scripts/context_processor.py`
- `src/Hypr-Whisper/config/context.yaml`

## Next steps recommended
1) Add an injection dispatcher choosing between ydotool/kdotool/wtype/xdotool based on the same backend matrix.
2) Ship minimal distro-specific install snippets for optional tools (apt/dnf/pacman/zypper) and setcap guidance for ydotool/kdotool.
3) Add CI lint to ensure `detect_backend()` never raises and always returns a dict with `class/title` keys.
