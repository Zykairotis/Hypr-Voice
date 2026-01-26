#!/usr/bin/env python3
"""
Universal Clipboard Module

Provides cross-platform clipboard support for X11 and Wayland primary selection.
"""

from .x11_primary import X11PrimarySelection
from .wayland_primary import WaylandPrimarySelection
from .universal_clipboard import UniversalClipboard
from .programmatic_paste import ProgrammaticPaster
from .selection_monitor import PrimarySelectionMonitor

__all__ = [
    'X11PrimarySelection',
    'WaylandPrimarySelection',
    'UniversalClipboard',
    'ProgrammaticPaster',
    'PrimarySelectionMonitor',
]

__version__ = '1.0.0'
