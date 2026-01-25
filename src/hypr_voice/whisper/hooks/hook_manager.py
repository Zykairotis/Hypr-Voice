#!/usr/bin/env python3
"""
Hook Manager for Hypr-Voice
Manages hooks that trigger on application changes or keywords.
"""

import asyncio
import subprocess
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import logging
from loguru import logger

from ..paths import get_whisper_config_path


@dataclass
class HookConfig:
    """Configuration for a single hook."""
    name: str
    trigger_type: str  # 'window_change', 'keyword', 'both'
    trigger_patterns: List[str]  # Window classes or keywords
    script_path: str
    timeout: int = 30  # seconds
    pass_context: bool = True
    output_target: str = 'context'  # 'context', 'vocabulary', 'both'
    enabled: bool = True


class HookManager:
    """Manages hooks that trigger on application changes or keywords."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the hook manager.
        
        Args:
            config_path: Path to hooks.yaml config file
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = get_whisper_config_path("hooks.yaml")
        
        self.hooks: Dict[str, HookConfig] = {}
        self.scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
        self._load_hooks()
    
    def _load_hooks(self):
        """Load hook configurations from YAML."""
        if not self.config_path.exists():
            logger.warning(f"Hooks config not found: {self.config_path}")
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if not config or 'hooks' not in config:
                logger.warning("No hooks defined in config")
                return
            
            for hook_name, hook_data in config['hooks'].items():
                try:
                    self.hooks[hook_name] = HookConfig(
                        name=hook_name,
                        **hook_data
                    )
                    logger.debug(f"Loaded hook: {hook_name}")
                except Exception as e:
                    logger.error(f"Error loading hook {hook_name}: {e}")
            
            logger.info(f"Loaded {len(self.hooks)} hooks")
        
        except Exception as e:
            logger.error(f"Error loading hooks config: {e}")
    
    async def trigger_hooks(
        self, 
        trigger_type: str,
        trigger_value: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger hooks matching the criteria.
        
        Args:
            trigger_type: 'window_change' or 'keyword'
            trigger_value: Window class or spoken keyword
            context: Current context to pass to scripts
        
        Returns:
            {
                'context_additions': {},
                'vocabulary_additions': [],
                'hook_results': []
            }
        """
        results = {
            'context_additions': {},
            'vocabulary_additions': [],
            'hook_results': []
        }
        
        # Find matching hooks
        matching_hooks = [
            hook for hook in self.hooks.values()
            if hook.enabled and self._hook_matches(hook, trigger_type, trigger_value)
        ]
        
        if not matching_hooks:
            logger.debug(f"No matching hooks for {trigger_type}: {trigger_value}")
            return results
        
        logger.info(f"Triggering {len(matching_hooks)} hooks for {trigger_type}: {trigger_value}")
        
        # Execute hooks concurrently
        tasks = [
            self._execute_hook(hook, context or {})
            for hook in matching_hooks
        ]
        hook_outputs = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process outputs
        for hook, output in zip(matching_hooks, hook_outputs):
            if isinstance(output, Exception):
                logger.error(f"Hook {hook.name} failed: {output}")
                results['hook_results'].append({
                    'hook_name': hook.name,
                    'error': str(output),
                    'success': False
                })
                continue
            
            self._process_hook_output(hook, output, results)
        
        return results
    
    def _hook_matches(self, hook: HookConfig, trigger_type: str, value: str) -> bool:
        """Check if hook should trigger."""
        # Check trigger type
        if hook.trigger_type not in [trigger_type, 'both']:
            return False
        
        # Pattern matching
        value_lower = value.lower()
        for pattern in hook.trigger_patterns:
            if pattern.lower() in value_lower:
                return True
        
        return False
    
    async def _execute_hook(
        self, 
        hook: HookConfig, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a hook script and capture output."""
        # Resolve script path
        script_path = Path(hook.script_path)
        if not script_path.is_absolute():
            # Try relative to hooks/scripts directory
            script_path = self.scripts_dir / hook.script_path
            if not script_path.exists():
                # Try relative to config directory
                script_path = self.config_path.parent / hook.script_path
        
        if not script_path.exists():
            raise FileNotFoundError(f"Hook script not found: {hook.script_path}")
        
        # Make script executable
        script_path.chmod(0o755)
        
        # Prepare input
        input_data = json.dumps(context if hook.pass_context else {})
        
        # Determine interpreter
        if script_path.suffix == '.py':
            cmd = ['python', str(script_path)]
        elif script_path.suffix == '.sh':
            cmd = ['bash', str(script_path)]
        else:
            # Assume executable
            cmd = [str(script_path)]
        
        logger.debug(f"Executing hook {hook.name}: {' '.join(cmd)}")
        
        # Execute script
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=input_data.encode()),
                timeout=hook.timeout
            )
            
            if stderr:
                logger.debug(f"Hook {hook.name} stderr: {stderr.decode()[:200]}")
            
            # Parse output
            output_text = stdout.decode().strip()
            
            if not output_text:
                return {'text': ''}
            
            # Try to parse as JSON
            try:
                return json.loads(output_text)
            except json.JSONDecodeError:
                # Return as plain text
                return {'text': output_text}
        
        except asyncio.TimeoutError:
            proc.kill()
            raise TimeoutError(f"Hook {hook.name} timed out after {hook.timeout}s")
        except Exception as e:
            logger.error(f"Error executing hook {hook.name}: {e}")
            raise
    
    def _process_hook_output(
        self, 
        hook: HookConfig, 
        output: Dict[str, Any], 
        results: Dict
    ):
        """Process hook output and add to results."""
        # Add to context
        if hook.output_target in ['context', 'both']:
            if 'context' in output:
                results['context_additions'].update(output['context'])
        
        # Add to vocabulary
        if hook.output_target in ['vocabulary', 'both']:
            if 'vocabulary' in output:
                vocab_items = output['vocabulary']
                if isinstance(vocab_items, list):
                    results['vocabulary_additions'].extend(vocab_items)
                elif isinstance(vocab_items, str):
                    results['vocabulary_additions'].append(vocab_items)
        
        # Record result
        results['hook_results'].append({
            'hook_name': hook.name,
            'output': output,
            'target': hook.output_target,
            'success': True
        })
    
    def reload_config(self):
        """Reload hooks configuration from file."""
        self.hooks.clear()
        self._load_hooks()
    
    def get_hook_info(self, hook_name: str) -> Optional[HookConfig]:
        """Get information about a specific hook."""
        return self.hooks.get(hook_name)
    
    def list_hooks(self) -> List[str]:
        """List all loaded hook names."""
        return list(self.hooks.keys())


# Global instance
_hook_manager: Optional[HookManager] = None

def get_hook_manager(config_path: Optional[str] = None) -> HookManager:
    """Get or create the global hook manager instance."""
    global _hook_manager
    if _hook_manager is None:
        _hook_manager = HookManager(config_path)
    return _hook_manager


async def main():
    """Test the hook manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test hook manager")
    parser.add_argument('--test', action='store_true', help='Run test mode')
    parser.add_argument('--trigger', type=str, help='Trigger value (app class or keyword)')
    parser.add_argument('--type', type=str, default='window_change', help='Trigger type')
    args = parser.parse_args()
    
    manager = get_hook_manager()
    
    if args.test:
        print("Testing Hook Manager\n")
        print("=" * 60)
        print(f"\nLoaded hooks: {len(manager.hooks)}")
        
        for hook_name, hook in manager.hooks.items():
            print(f"\n  Hook: {hook_name}")
            print(f"    Type: {hook.trigger_type}")
            print(f"    Patterns: {', '.join(hook.trigger_patterns)}")
            print(f"    Script: {hook.script_path}")
            print(f"    Timeout: {hook.timeout}s")
            print(f"    Output: {hook.output_target}")
            print(f"    Enabled: {hook.enabled}")
        
        if args.trigger:
            print(f"\n{'=' * 60}")
            print(f"\nTriggering hooks for {args.type}: {args.trigger}\n")
            
            context = {
                'workspace': {
                    'application': args.trigger,
                    'window_title': 'Test Window',
                    'category': 'development'
                }
            }
            
            results = await manager.trigger_hooks(args.type, args.trigger, context)
            
            print(f"Context additions: {results['context_additions']}")
            print(f"Vocabulary additions: {results['vocabulary_additions']}")
            print(f"\nHook results:")
            for result in results['hook_results']:
                print(f"  {result['hook_name']}: {'✓' if result['success'] else '✗'}")
                if 'error' in result:
                    print(f"    Error: {result['error']}")
        
        print("\n" + "=" * 60)


if __name__ == '__main__':
    asyncio.run(main())
