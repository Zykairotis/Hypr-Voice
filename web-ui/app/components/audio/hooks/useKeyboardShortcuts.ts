import { useEffect, useRef } from 'react';

interface KeyboardShortcuts {
  [key: string]: () => void;
}

export const useKeyboardShortcuts = (shortcuts: KeyboardShortcuts) => {
  const shortcutsRef = useRef(shortcuts);

  useEffect(() => {
    shortcutsRef.current = shortcuts;

    const handleKeyDown = (event: KeyboardEvent) => {
      const key = event.key.toLowerCase();
      const ctrl = event.ctrlKey || event.metaKey;
      const shift = event.shiftKey;
      const alt = event.altKey;

      let shortcutKey = '';

      if (ctrl) shortcutKey += 'ctrl+';
      if (shift) shortcutKey += 'shift+';
      if (alt) shortcutKey += 'alt+';
      shortcutKey += key;

      if (shortcutsRef.current[shortcutKey]) {
        event.preventDefault();
        shortcutsRef.current[shortcutKey]();
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);
};

export const KEYBOARD_SHORTCUTS = {
  'ctrl+r': 'Record/Pause',
  'ctrl+s': 'Stop',
  'ctrl+m': 'Mute/Unmute',
  'ctrl+space': 'Play/Pause',
  'escape': 'Stop All',
  'f1': 'Help',
  'f11': 'Fullscreen',
  '1': 'Monitor Tab',
  '2': 'Waveform Tab',
  '3': 'Spectrum Tab',
  '4': '3D Visual Tab',
  '5': 'Mixer Tab',
  '6': 'Settings Tab',
};
