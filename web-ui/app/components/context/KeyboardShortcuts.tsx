/**
 * Keyboard shortcuts for Context Manager
 * Global keyboard shortcuts that work across the application
 */

import { useEffect } from 'react';

interface ShortcutHandlers {
  onClearContext?: () => void;
  onExportContext?: () => void;
  onRefreshContext?: () => void;
  onFocusSearch?: () => void;
}

export function KeyboardShortcuts(handlers: ShortcutHandlers) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Check if Ctrl+Shift is pressed
      if (!event.ctrlKey || !event.shiftKey) {
        return;
      }

      const key = event.key.toLowerCase();

      switch (key) {
        case 'c':
          event.preventDefault();
          handlers.onClearContext?.();
          console.log('[Context] Clear context shortcut triggered');
          break;

        case 'e':
          event.preventDefault();
          handlers.onExportContext?.();
          console.log('[Context] Export context shortcut triggered');
          break;

        case 'r':
          event.preventDefault();
          handlers.onRefreshContext?.();
          console.log('[Context] Refresh context shortcut triggered');
          break;

        case 'f':
          event.preventDefault();
          handlers.onFocusSearch?.();
          console.log('[Context] Focus search shortcut triggered');
          break;

        default:
          break;
      }
    };

    // Add event listener
    document.addEventListener('keydown', handleKeyDown);

    // Cleanup
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handlers]);

  return null; // This component doesn't render anything
}

/**
 * Display keyboard shortcuts help dialog
 */
export function ShortcutsHelp() {
  const shortcuts = [
    {
      key: 'Ctrl+Shift+C',
      action: 'Clear all context data',
      category: 'Context'
    },
    {
      key: 'Ctrl+Shift+E',
      action: 'Export context data',
      category: 'Context'
    },
    {
      key: 'Ctrl+Shift+R',
      action: 'Refresh context',
      category: 'Context'
    },
    {
      key: 'Ctrl+Shift+F',
      action: 'Focus search',
      category: 'Search'
    },
    {
      key: '?',
      action: 'Show this help',
      category: 'Help'
    }
  ];

  const categories = {
    Context: shortcuts.filter(s => s.category === 'Context'),
    Search: shortcuts.filter(s => s.category === 'Search'),
    Help: shortcuts.filter(s => s.category === 'Help')
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold mb-2">Keyboard Shortcuts</h3>
        <p className="text-sm text-muted-foreground">
          Use these keyboard shortcuts to quickly access Context Manager features
        </p>
      </div>

      <div className="space-y-3">
        {Object.entries(categories).map(([category, items]) => (
          <div key={category}>
            <h4 className="text-sm font-semibold mb-2">{category}</h4>
            <div className="space-y-1.5">
              {items.map((shortcut, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-2 bg-muted/50 rounded text-sm"
                >
                  <span className="font-mono">{shortcut.key}</span>
                  <span className="text-muted-foreground">{shortcut.action}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 p-3 bg-muted/30 rounded-lg">
        <p className="text-xs text-muted-foreground">
          <strong>Tip:</strong> Keyboard shortcuts work globally across the application.
          Press the key combination at any time to trigger the action.
        </p>
      </div>
    </div>
  );
}

/**
 * Hook to register keyboard shortcuts with auto-disposal
 */
export function useContextShortcuts(handlers: ShortcutHandlers) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!event.ctrlKey || !event.shiftKey) {
        return;
      }

      const key = event.key.toLowerCase();

      switch (key) {
        case 'c':
          event.preventDefault();
          handlers.onClearContext?.();
          break;
        case 'e':
          event.preventDefault();
          handlers.onExportContext?.();
          break;
        case 'r':
          event.preventDefault();
          handlers.onRefreshContext?.();
          break;
        case 'f':
          event.preventDefault();
          handlers.onFocusSearch?.();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handlers]);
}

/**
 * Show keyboard shortcut badges in UI
 */
export function ShortcutBadge({ shortcut, className = '' }: { shortcut: string; className?: string }) {
  const [ctrl, shift, key] = shortcut.split('+');

  return (
    <kbd className={`inline-flex items-center gap-0.5 px-2 py-1 bg-muted rounded text-xs font-mono ${className}`}>
      {ctrl && <span>⌘</span>}
      {shift && <span>⇧</span>}
      <span className="ml-0.5">{key}</span>
    </kbd>
  );
}

/**
 * Shortcut documentation component
 */
export function ShortcutsDocumentation() {
  return (
    <div className="prose prose-sm dark:prose-invert max-w-none">
      <h2>Keyboard Shortcuts Reference</h2>

      <h3>Context Manager Shortcuts</h3>
      <table>
        <thead>
          <tr>
            <th>Shortcut</th>
            <th>Action</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>Ctrl+Shift+C</code></td>
            <td>Clear Context</td>
            <td>Clear all context data (shell history, clipboard, etc.)</td>
          </tr>
          <tr>
            <td><code>Ctrl+Shift+E</code></td>
            <td>Export Context</td>
            <td>Export context data to JSON file</td>
          </tr>
          <tr>
            <td><code>Ctrl+Shift+R</code></td>
            <td>Refresh Context</td>
            <td>Manually refresh context data from backend</td>
          </tr>
          <tr>
            <td><code>Ctrl+Shift+F</code></td>
            <td>Focus Search</td>
            <td>Focus the search input in the current view</td>
          </tr>
          <tr>
            <td><code>?</code></td>
            <td>Show Help</td>
            <td>Display keyboard shortcuts help</td>
          </tr>
        </tbody>
      </table>

      <h3>Usage</h3>
      <p>
        Keyboard shortcuts work globally across the Context Manager interface.
        Simply press the key combination at any time to trigger the action.
      </p>

      <h3>Customization</h3>
      <p>
        Shortcuts can be customized by modifying the event handlers in the
        KeyboardShortcuts component or by using the useContextShortcuts hook.
      </p>
    </div>
  );
}
