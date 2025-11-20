#!/usr/bin/env python3
"""
Application Categorizer for Hypr-Voice
Dynamically categorize applications using .desktop files and user-defined patterns.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Set, Optional
import configparser
import logging
from loguru import logger

class ApplicationCategorizer:
    """Dynamically categorize applications using .desktop files."""
    
    DESKTOP_PATHS = [
        "/usr/share/applications/",
        "/usr/local/share/applications/",
        "~/.local/share/applications/"
    ]
    
    # Freedesktop.org main categories
    MAIN_CATEGORIES = {
        'AudioVideo', 'Development', 'Education', 'Game',
        'Graphics', 'Network', 'Office', 'Science',
        'Settings', 'System', 'Utility'
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the categorizer.
        
        Args:
            config_path: Path to categories.yaml config file
        """
        self.config_path = Path(config_path) if config_path else Path(__file__).parent.parent / "config" / "categories.yaml"
        self.app_database: Dict[str, Dict] = {}  # Maps executable → metadata
        self.category_mapping: Dict[str, str] = {}  # Maps app_class → custom category
        self.user_categories: Dict[str, Dict] = {}  # User-defined categories
        self.cache: Dict[str, Dict] = {}  # Cache categorization results
        
        self._load_desktop_files()
        self._load_custom_mappings()
    
    def _load_desktop_files(self):
        """Parse all .desktop files and build lookup table."""
        logger.info("Loading .desktop files...")
        count = 0
        
        for path in self.DESKTOP_PATHS:
            desktop_dir = Path(path).expanduser()
            if not desktop_dir.exists():
                continue
            
            for desktop_file in desktop_dir.glob("*.desktop"):
                try:
                    self._parse_desktop_file(desktop_file)
                    count += 1
                except Exception as e:
                    logger.debug(f"Error parsing {desktop_file}: {e}")
        
        logger.info(f"Loaded {count} .desktop files, {len(self.app_database)} unique applications")
    
    def _parse_desktop_file(self, filepath: Path):
        """Extract categories, executable, WM_CLASS from desktop file."""
        config = configparser.ConfigParser(strict=False)
        config.read(filepath, encoding='utf-8')
        
        if 'Desktop Entry' not in config:
            return
        
        entry = config['Desktop Entry']
        
        # Extract metadata
        categories = entry.get('Categories', '').split(';')
        exec_cmd = entry.get('Exec', '')
        wm_class = entry.get('StartupWMClass', '')
        name = entry.get('Name', '')
        
        # Get executable name
        executable = self._extract_executable(exec_cmd)
        
        # Store mapping
        main_cats = [c for c in categories if c in self.MAIN_CATEGORIES]
        if executable and main_cats:
            self.app_database[executable] = {
                'categories': main_cats,
                'wm_class': wm_class,
                'name': name,
                'all_categories': categories,
                'exec': exec_cmd
            }
    
    def _extract_executable(self, exec_cmd: str) -> str:
        """Extract executable name from Exec command."""
        if not exec_cmd:
            return ""
        
        # Remove field codes (%f, %F, %u, %U, etc.)
        import re
        exec_cmd = re.sub(r'%[fFuUdDnNickvm]', '', exec_cmd)
        
        # Split and get first part
        parts = exec_cmd.split()
        if not parts:
            return ""
        
        executable = parts[0]
        
        # Handle env vars and paths
        if '=' in executable:
            return ""
        
        # Get basename
        return Path(executable).name
    
    def _load_custom_mappings(self):
        """Load user-defined category mappings from config."""
        if not self.config_path.exists():
            logger.warning(f"Categories config not found: {self.config_path}")
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if not config or 'categories' not in config:
                logger.warning("No categories defined in config")
                return
            
            # Load user categories
            for cat_name, cat_data in config['categories'].items():
                self.user_categories[cat_name] = cat_data
                
                # Build reverse mapping: pattern → category
                for pattern in cat_data.get('patterns', []):
                    self.category_mapping[pattern.lower()] = cat_name
            
            logger.info(f"Loaded {len(self.user_categories)} user-defined categories")
        
        except Exception as e:
            logger.error(f"Error loading categories config: {e}")
    
    def categorize(self, app_class: str, app_title: str = "") -> Dict:
        """
        Categorize an application.
        
        Args:
            app_class: Window class name
            app_title: Window title (optional)
        
        Returns:
            {
                'category': 'development',  # User-defined
                'freedesktop_categories': ['Development', 'IDE'],
                'confidence': 'high'  # high, medium, low
            }
        """
        # Check cache first
        cache_key = f"{app_class}:{app_title}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        result = self._categorize_impl(app_class, app_title)
        
        # Cache result
        self.cache[cache_key] = result
        
        return result
    
    def _categorize_impl(self, app_class: str, app_title: str = "") -> Dict:
        """Internal categorization logic."""
        app_class_lower = app_class.lower()
        
        # 1. Check custom mapping (highest priority)
        for pattern, category in self.category_mapping.items():
            if pattern in app_class_lower:
                return {
                    'category': category,
                    'freedesktop_categories': [],
                    'confidence': 'high',
                    'source': 'user_pattern'
                }
        
        # 2. Try desktop file lookup by WM_CLASS
        for exe, data in self.app_database.items():
            if data['wm_class'] and data['wm_class'].lower() == app_class.lower():
                return {
                    'category': self._map_to_user_category(data['categories'][0]),
                    'freedesktop_categories': data['categories'],
                    'confidence': 'high',
                    'source': 'wm_class'
                }
        
        # 3. Try desktop file lookup by executable name
        for exe, data in self.app_database.items():
            if exe.lower() in app_class_lower:
                return {
                    'category': self._map_to_user_category(data['categories'][0]),
                    'freedesktop_categories': data['categories'],
                    'confidence': 'medium',
                    'source': 'executable'
                }
        
        # 4. Fallback heuristics
        return self._heuristic_categorization(app_class, app_title)
    
    def _map_to_user_category(self, freedesktop_category: str) -> str:
        """Map freedesktop category to user-defined category."""
        # Check each user category's freedesktop_map
        for cat_name, cat_data in self.user_categories.items():
            freedesktop_map = cat_data.get('freedesktop_map', [])
            if freedesktop_category in freedesktop_map:
                return cat_name
        
        # Default mapping
        mapping = {
            'Development': 'development',
            'IDE': 'development',
            'TerminalEmulator': 'development',
            'Network': 'communication',
            'InstantMessaging': 'communication',
            'VideoConference': 'communication',
            'Office': 'productivity',
            'WebBrowser': 'productivity',
            'AudioVideo': 'media',
            'Graphics': 'media',
            'Video': 'media',
            'Audio': 'media',
        }
        
        return mapping.get(freedesktop_category, 'other')
    
    def _heuristic_categorization(self, app_class: str, app_title: str) -> Dict:
        """Fallback heuristic categorization."""
        app_class_lower = app_class.lower()
        app_title_lower = app_title.lower()
        
        # Terminal patterns
        if any(term in app_class_lower for term in ['term', 'console', 'shell', 'tty']):
            return {
                'category': 'development',
                'freedesktop_categories': [],
                'confidence': 'low',
                'source': 'heuristic'
            }
        
        # Browser patterns
        if any(term in app_class_lower for term in ['browser', 'firefox', 'chrome', 'chromium']):
            return {
                'category': 'productivity',
                'freedesktop_categories': [],
                'confidence': 'low',
                'source': 'heuristic'
            }
        
        # Default
        return {
            'category': 'other',
            'freedesktop_categories': [],
            'confidence': 'low',
            'source': 'default'
        }
    
    def get_category_info(self, category: str) -> Optional[Dict]:
        """Get information about a user-defined category."""
        return self.user_categories.get(category)
    
    def clear_cache(self):
        """Clear categorization cache."""
        self.cache.clear()


# Global instance
_categorizer: Optional[ApplicationCategorizer] = None

def get_categorizer(config_path: Optional[str] = None) -> ApplicationCategorizer:
    """Get or create the global categorizer instance."""
    global _categorizer
    if _categorizer is None:
        _categorizer = ApplicationCategorizer(config_path)
    return _categorizer


def main():
    """Test the categorizer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test application categorizer")
    parser.add_argument('--test', action='store_true', help='Run test mode')
    parser.add_argument('--app', type=str, help='Application class to categorize')
    args = parser.parse_args()
    
    categorizer = get_categorizer()
    
    if args.test:
        print("Testing Application Categorizer\n")
        print("=" * 60)
        
        # Test cases
        test_cases = [
            ("cursor", ""),
            ("Cursor", "main.py - Hypr-Voice"),
            ("zen", "GitHub - zen browser"),
            ("Discord", ""),
            ("Alacritty", ""),
            ("vlc", ""),
            ("gimp", ""),
            ("Unknown", ""),
        ]
        
        for app_class, app_title in test_cases:
            result = categorizer.categorize(app_class, app_title)
            print(f"\nApp: {app_class}")
            if app_title:
                print(f"Title: {app_title}")
            print(f"Category: {result['category']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Source: {result['source']}")
            if result['freedesktop_categories']:
                print(f"Freedesktop: {', '.join(result['freedesktop_categories'])}")
        
        print("\n" + "=" * 60)
        print(f"\nTotal apps in database: {len(categorizer.app_database)}")
        print(f"User categories: {len(categorizer.user_categories)}")
        print(f"Pattern mappings: {len(categorizer.category_mapping)}")
    
    elif args.app:
        result = categorizer.categorize(args.app)
        print(f"Category: {result['category']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Freedesktop: {result['freedesktop_categories']}")


if __name__ == '__main__':
    main()

