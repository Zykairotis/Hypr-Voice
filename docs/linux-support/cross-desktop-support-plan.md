# Cross-Desktop Support Plan for Hypr-Whisper

Goal: make Hypr-Whisper window-introspection and input-synthesis work on the top Linux desktops beyond Hyprland (GNOME, KDE Plasma, Sway/wlroots, mainstream X11 WMs such as XFCE/Cinnamon/MATE, plus Hyprland as the current baseline).

## 1) Detect session + capabilities
- Add a lightweight `session_probe` helper that inspects `XDG_SESSION_TYPE`, `XDG_CURRENT_DESKTOP`, `WAYLAND_DISPLAY`, presence of `swaymsg`, `gdbus/org.gnome.Shell`, `qdbus org.kde.KWin`, `wmctrl`, and `hyprctl` to classify runtime into one of: `hyprland`, `sway/wlroots`, `gnome-wayland`, `kde-wayland`, `x11-ewmh`, `unknown`.
- Record a capability matrix (introspect windows? inject input? requires setcap/root?) and expose it so the app can pick viable back-ends instead of failing hard.
- Keep detection pure-Python with no DBus bindings requirement; shell out using non-blocking reads and cache results per session.

## 2) Window introspection adapters
- Define a `WindowInspector` interface that returns: focused window id/title/app_id/class/pid, list of windows, workspace/desktop if available.
- Implement adapters:
  - Hyprland: reuse existing `hyprctl activewindow/clients` parser.
  - Sway/wlroots: `swaymsg -t get_tree` → parse JSON; extract `.focused==true` node, list nodes with `.type=="con"`.
  - GNOME Shell: `gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell --method org.gnome.Shell.Eval '<JS>'` to enumerate `global.get_window_actors()` and find `has_focus()`.
  - KDE Plasma: preferred path via `kdotool` (D-Bus to KWin); fallback tiny KWin JS loaded through `qdbus org.kde.KWin /Scripting loadScript` to query active window properties.
  - X11/EWMH: `wmctrl -lpx` for window list; `xdotool getactivewindow getwindowname getwindowpid` for focus details.
- Normalize outputs (title, app_id/class, pid, workspace) so downstream logic stays compositor-agnostic.

## 3) Input synthesis back-ends
- (Implemented) Dispatcher chooses `ydotool` → `kdotool` → `wtype` → `xdotool` based on availability and window backend hint; falls back to no-op with warnings.
- Keep `ydotool` for uinput-based Wayland injection (works on wlroots/Hyprland and most GNOME/KDE sessions when uinput permissions are set).
- Add `kdotool` for KDE Wayland to avoid KWin security blocks on generic uinput.
- Add `wtype`/`ydotool` preference for wlroots (Sway/Hyprland) depending on availability.
- Add `xdotool` for X11 sessions; include copy/paste fallback to handle compositions where synthetic key events are blocked.
- Provide a dispatcher that chooses the highest-fidelity backend from the capability matrix and surfaces clear errors when injection is impossible (e.g., corporate GNOME with uinput denied).

## 4) Packaging, permissions, and distro notes
- Document per-distro install commands (Debian/Ubuntu apt, Fedora dnf, Arch pacman, openSUSE zypper) for `ydotool`, `kdotool`, `swaymsg`, `wmctrl`, `xdotool`, `jq`.
- Ship a script to apply `setcap 'cap_uinput+ep' $(command -v ydotool)` and similar for `kdotool` when required, with guidance for PolicyKit rules if needed.
- Add configuration toggles to force a specific backend or disable input injection for hardened environments.
- Ensure new dependencies are optional (lazy import + command existence check) to avoid breaking minimal installs.

## 5) QA and rollout
- Create an automated smoke-test script that exercises detection, focused-window query, and a no-op input dry-run for each backend (mock mode where possible).
- Build a manual test matrix covering: GNOME (Wayland/Xorg), KDE Plasma (Wayland/X11), Sway, Hyprland, XFCE (X11), Cinnamon (X11); run on Debian/Ubuntu, Fedora, Arch, openSUSE.
- Add logging around backend selection and failures to aid user support; redact titles/content where privacy is a concern.
- Update README/QUICK_START with a “Non-Hyprland desktops” section pointing to this plan, with links to backend-specific instructions once implemented.
