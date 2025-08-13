#!/usr/bin/env python3
"""
Multi-Provider Improvement Engine - LiteLLM integration
Providers: xAI (default), OpenAI, Anthropic, Google (Gemini), Ollama
- Model routing via LiteLLM prefixes: xai/, openai/, anthropic/, google/, ollama/
- Primary model from LLM_MODEL (env); ordered fallbacks via LLM_FALLBACKS
- Reads provider keys via env (XAI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY)
"""

import os
import yaml
import json
import asyncio
import subprocess
import contextlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from loguru import logger
from dotenv import load_dotenv

import litellm  # LiteLLM SDK
from litellm import acompletion

load_dotenv()

@dataclass
class AppProfile:
    """Application profile configuration"""
    app_name: str
    app_class: str
    writing_style: str = "natural"
    context_rules: Optional[List[str]] = None
    abbreviations: Optional[Dict[str, str]] = None
    terminology: Optional[List[str]] = None
    extra_context: Optional[List[str]] = None
    llm_config: Optional[Dict[str, Any]] = None
    output_format: str = "text"
    memory_scope: str = "session"
    system_prompt: str = ""
    
    def __post_init__(self):
        self.context_rules = self.context_rules or []
        self.abbreviations = self.abbreviations or {}
        self.terminology = self.terminology or []
        self.extra_context = self.extra_context or []
        self.llm_config = self.llm_config or {}


class SimpleImprovementEngine:
    """
    Improvement engine using LiteLLM across multiple providers.
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize the Simple Improvement Engine"""
        load_dotenv()
        
        self.config_dir = config_dir or (Path(__file__).parent / "config")
        self.profiles: Dict[str, AppProfile] = {}
        self.current_profile: Optional[AppProfile] = None
        
        # Multi-provider LiteLLM model routing
        self.primary_model = os.getenv("LLM_MODEL", "xai/grok-3-mini")
        fallbacks = os.getenv("LLM_FALLBACKS", "xai/grok-3-mini,openai/gpt-4o-mini,anthropic/claude-3-5-sonnet-20241022")
        self.fallback_models: List[str] = [m.strip() for m in fallbacks.split(",") if m.strip()]
        
        # Extract model name without provider for logging
        model_name = self.primary_model.split("/")[-1] if "/" in self.primary_model else self.primary_model
        
        # Timeouts & limits
        try:
            self._client_timeout = float(os.getenv("LLM_TIMEOUT", os.getenv("XAI_TIMEOUT", "12.0")))
        except Exception:
            self._client_timeout = 12.0
        try:
            self._connect_timeout = float(os.getenv("XAI_CONNECT_TIMEOUT", "5.0"))
            self._write_timeout = float(os.getenv("XAI_WRITE_TIMEOUT", "10.0"))
        except Exception:
            self._connect_timeout = 5.0
            self._write_timeout = 10.0
        try:
            self._retries = int(os.getenv("XAI_RETRIES", "2"))
        except Exception:
            self._retries = 2
        try:
            self._backoff_base = float(os.getenv("XAI_BACKOFF_BASE", "1.0"))
        except Exception:
            self._backoff_base = 1.0
        try:
            self._max_tokens_cap = int(os.getenv("XAI_MAX_TOKENS_CAP", "8192"))
        except Exception:
            self._max_tokens_cap = 8192

        # Reasoning effort (optional, used by xAI and others if supported)
        self._default_reasoning_effort = os.getenv("LLM_REASONING_EFFORT", "")

        # Optional per-provider base URLs (for OpenAI-compatible or custom deployments)
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "")
        self.anthropic_base_url = os.getenv("ANTHROPIC_BASE_URL", "")
        self.google_base_url = os.getenv("GOOGLE_BASE_URL", "")
        self.xai_base_url = os.getenv("XAI_BASE_URL", "")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "")

        # Configure LiteLLM base URLs if provided (OpenAI-compatible endpoints etc.)
        if self.openai_base_url:
            os.environ["OPENAI_BASE_URL"] = self.openai_base_url
        if self.anthropic_base_url:
            os.environ["ANTHROPIC_BASE_URL"] = self.anthropic_base_url
        if self.google_base_url:
            os.environ["GOOGLE_BASE_URL"] = self.google_base_url
        # xAI base not required by LiteLLM, but keep for compatibility
        if self.ollama_base_url:
            os.environ["OLLAMA_API_BASE"] = self.ollama_base_url  # used by LiteLLM Ollama driver

        # Retain last explanation for logs
        self._last_xai_explanation: str = ""

        self._load_profiles()
        logger.info(f"✅ Improvement Engine initialized. Primary: {self.primary_model} | Fallbacks: {self.fallback_models}")
    
    def _load_profiles(self):
        """Load application profiles from YAML"""
        profiles_path = self.config_dir / "app_profiles.yaml"
        
        if not profiles_path.exists():
            logger.warning(f"No profiles found at {profiles_path}")
            return
        
        try:
            with open(profiles_path, 'r') as f:
                profiles_data = yaml.safe_load(f) or {}
            
            loaded = 0
            # Support nested 'applications' block in YAML
            apps_block = profiles_data.get('applications')
            if isinstance(apps_block, dict):
                for app_name, config in apps_block.items():
                    if isinstance(config, dict):
                        profile = AppProfile(
                            app_name=app_name,
                            app_class=str(config.get('app_class') or app_name.lower()),
                            writing_style=config.get('writing_style', 'natural'),
                            context_rules=config.get('context_rules', []),
                            abbreviations=config.get('abbreviations', {}),
                            terminology=config.get('terminology', []),
                            extra_context=config.get('extra_context', []),
                            llm_config=config.get('llm_config', {}),
                            output_format=config.get('output_format', 'text'),
                            memory_scope=config.get('memory_scope', 'session'),
                            system_prompt=config.get('system_prompt', '')
                        )
                        self.profiles[app_name.lower()] = profile
                        loaded += 1
            
            # Load explicit top-level 'default' profile if present
            default_cfg = profiles_data.get('default')
            if isinstance(default_cfg, dict):
                default_profile = AppProfile(
                    app_name='default',
                    app_class=str(default_cfg.get('app_class') or 'default'),
                    writing_style=default_cfg.get('writing_style', 'natural'),
                    context_rules=default_cfg.get('context_rules', []),
                    abbreviations=default_cfg.get('abbreviations', {}),
                    terminology=default_cfg.get('terminology', []),
                    extra_context=default_cfg.get('extra_context', []),
                    llm_config=default_cfg.get('llm_config', {}),
                    output_format=default_cfg.get('output_format', 'text'),
                    memory_scope=default_cfg.get('memory_scope', 'session'),
                    system_prompt=default_cfg.get('system_prompt', '')
                )
                self.profiles['default'] = default_profile
                loaded += 1
            
            # Back-compat: any other top-level profiles (excluding templates/applications/default)
            for app_name, config in profiles_data.items():
                if app_name in ('templates', 'applications', 'default'):
                    continue
                if isinstance(config, dict):
                    profile = AppProfile(
                        app_name=app_name,
                        app_class=str(config.get('app_class') or app_name.lower()),
                        writing_style=config.get('writing_style', 'natural'),
                        context_rules=config.get('context_rules', []),
                        abbreviations=config.get('abbreviations', {}),
                        terminology=config.get('terminology', []),
                        extra_context=config.get('extra_context', []),
                        llm_config=config.get('llm_config', {}),
                        output_format=config.get('output_format', 'text'),
                        memory_scope=config.get('memory_scope', 'session'),
                        system_prompt=config.get('system_prompt', '')
                    )
                    self.profiles[app_name.lower()] = profile
                    loaded += 1
            
            logger.info(f"Loaded {loaded} app profiles")
            
        except Exception as e:
            logger.error(f"Error in loading profiles: {e}")
    
    def _get_generic_context_description(self, profile: AppProfile) -> str:
        """Get a generic description of the context based on app_class, not app_name"""
        # Map app_class to generic descriptions to avoid confusing the LLM
        context_map = {
            'code_editor': 'code editing and software development',
            'web_browser': 'web browsing and online research',
            'terminal_interface': 'terminal commands and system administration',
            'instant_messaging': 'instant messaging and chat',
            'terminal': 'command-line operations',
            'default': 'general text improvement'
        }
        
        # Use app_class if available, otherwise derive from writing style
        app_class = profile.app_class.lower() if profile.app_class else 'default'
        
        # Check for known app classes
        for key in context_map:
            if key in app_class:
                return context_map[key]
        
        # Fallback based on writing style
        style_map = {
            'technical_precise': 'technical documentation',
            'casual': 'casual communication',
            'formal': 'formal writing',
            'concise': 'brief and direct communication',
            'natural': 'general text improvement'
        }
        
        writing_style = profile.writing_style.lower() if profile.writing_style else 'natural'
        return style_map.get(writing_style, 'general text improvement')

    def _build_system_prompt(self, profile: AppProfile, extra_context: Optional[str] = None) -> str:
        """Build system prompt for the LLM"""
        # Use generic context description instead of app_name
        context_desc = self._get_generic_context_description(profile)
        
        system_prompt = profile.system_prompt or (
            f"You are an AI assistant helping with {context_desc}.\n"
            f"Writing style: {profile.writing_style}\n"
            f"Output format: {profile.output_format}"
        )
        if profile.context_rules:
            rules_text = "\n".join(f"- {rule}" for rule in profile.context_rules)
            system_prompt += f"\n\nContext rules:\n{rules_text}"
        # Only add extra context if it's actually provided and not empty
        if extra_context and extra_context.strip():
            system_prompt += f"\n\nCurrent context:\n{extra_context}"
        return system_prompt

    def _build_user_prompt(self, text: str, profile: AppProfile) -> str:
        """Build user prompt for text improvement"""
        # Use generic context description instead of app_name
        context_desc = self._get_generic_context_description(profile)
        
        return (
            "Improve the following text while maintaining its core intent.\n"
            "Apply any relevant abbreviations, terminology, and context rules.\n"
            f"Make it more {profile.writing_style} and appropriate for {context_desc}.\n\n"
            f"Original text: {text}\n\n"
            "Return a single JSON object with these fields (no markdown fences):\n"
            "{\n"
            '  "improved_text": string,\n'
            '  "xai_explanation": string\n'
            "}"
        )
    
    def set_active_application(self, app_class: Optional[str]) -> Optional[AppProfile]:
        """Set the active application profile by window class"""
        if not app_class:
            # Fall back early if None/empty
            if 'default' in self.profiles:
                self.current_profile = self.profiles['default']
                logger.info("Using default profile (no app_class provided)")
                return self.current_profile
            logger.warning("No app_class provided and no default profile available")
            self.current_profile = None
            return None
        app_class_lower = app_class.lower()
        
        # Try exact match first
        if app_class_lower in self.profiles:
            self.current_profile = self.profiles[app_class_lower]
            logger.info(f"✅ Active profile set: {self.current_profile.app_name}")
            return self.current_profile
        
        # Try matching by app_class field
        for profile in self.profiles.values():
            if profile.app_class.lower() == app_class_lower:
                self.current_profile = profile
                logger.info(f"✅ Active profile set: {profile.app_name}")
                return profile
        
        # Fall back to default
        if 'default' in self.profiles:
            self.current_profile = self.profiles['default']
            logger.info(f"Using default profile for {app_class}")
            return self.current_profile
        
        logger.warning(f"No profile found for {app_class}")
        self.current_profile = None
        return None
    
    async def execute_extra_context(self, profile: AppProfile) -> str:
        """Execute extra context commands and collect output (non-blocking)"""
        if not profile.extra_context:
            return ""
        
        async def run_cmd(cmd: str) -> str:
            try:
                proc = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                try:
                    stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=2.5)
                except asyncio.TimeoutError:
                    with contextlib.suppress(ProcessLookupError):
                        proc.kill()
                    return ""
                if stdout:
                    out = stdout.decode().strip()
                    if out:
                        return f"[{cmd}]: {out}"
            except Exception as e:
                logger.debug(f"Context command failed: {cmd}: {e}")
            return ""
        
        # Run commands concurrently with a small limit to avoid overload
        sem = asyncio.Semaphore(4)
        async def guarded(cmd: str) -> str:
            async with sem:
                return await run_cmd(cmd)
        
        results = await asyncio.gather(*(guarded(c) for c in profile.extra_context), return_exceptions=False)
        return "\n".join([r for r in results if r])
    
    def _resolve_model_list(self, llm_cfg: Dict[str, Any]) -> List[str]:
        """
        Build an ordered model list: profile override -> primary -> fallbacks.
        Models must include LiteLLM provider prefix (e.g., xai/, openai/, anthropic/, google/, ollama/).
        """
        models: List[str] = []
        override = llm_cfg.get('model')
        if override:
            # Ensure provider prefix exists
            override_str = str(override)
            if "/" not in override_str:
                # Default to xai provider for backward compatibility
                override_str = f"xai/{override_str}"
            models.append(override_str)
        if self.primary_model and self.primary_model not in models:
            models.append(self.primary_model)
        for fb in self.fallback_models:
            if fb not in models:
                models.append(fb)
        # As a last resort, include a local model if defined env-side
        env_ollama_default = os.getenv("OLLAMA_DEFAULT_MODEL", "")
        if env_ollama_default:
            # Ensure ollama prefix for local models
            if "/" not in env_ollama_default:
                env_ollama_default = f"ollama/{env_ollama_default}"
            if env_ollama_default not in models:
                models.append(env_ollama_default)
        return models

    async def _litellm_chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        read_timeout: float,
        reasoning_effort: Optional[str] = None,
        stream: bool = False,
    ) -> str:
        """Call LiteLLM with retry logic"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},  # encourage JSON when supported
        }
        if reasoning_effort:
            kwargs["reasoning_effort"] = reasoning_effort  # xAI supports this

        def _do_call() -> str:
            attempts = self._retries + 1
            last_exc: Optional[BaseException] = None
            for attempt in range(1, attempts + 1):
                try:
                    if stream:
                        # Use streaming for real-time response
                        response = litellm.completion(stream=True, **kwargs)
                        buffer: List[str] = []
                        for chunk in response:
                            delta = chunk.choices[0].delta
                            if hasattr(delta, 'content') and delta.content:
                                buffer.append(delta.content)
                        return "".join(buffer).strip()
                    else:
                        # Use async completion for better performance
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            resp = loop.run_until_complete(litellm.acompletion(**kwargs))
                            return resp.choices[0].message.content.strip()
                        finally:
                            loop.close()
                except Exception as e:
                    last_exc = e
                    logger.warning(f"LiteLLM request error (model={model}, attempt {attempt}/{attempts}): {e}")
                    if attempt < attempts:
                        import time
                        time.sleep(self._backoff_base * attempt)
                        continue
                    break
            if last_exc:
                raise last_exc
            return ""

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(_do_call),
                timeout=read_timeout + self._connect_timeout + self._write_timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"⏱️ LiteLLM timeout after ~{read_timeout}s (model={model})")
            return ""
        except Exception as e:
            logger.error(f"❌ LiteLLM unexpected error: {type(e).__name__}: {e}")
            return ""

    async def _call_with_fallbacks(
        self,
        system_prompt: str,
        user_prompt: str,
        models: List[str],
        temperature: float,
        max_tokens: int,
        read_timeout: float,
        reasoning_effort: Optional[str],
    ) -> str:
        """
        Try each model in order until a non-empty response is returned.
        """
        for m in models:
            content = await self._litellm_chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=m,
                temperature=temperature,
                max_tokens=max_tokens,
                read_timeout=read_timeout,
                reasoning_effort=reasoning_effort,
                stream=False,
            )
            if content:
                logger.info(f"✅ Response received from model: {m}")
                return content
            logger.warning(f"Model returned empty/failed: {m}. Trying next fallback.")
        return ""

    async def improve_with_xai(self, text: str, profile: AppProfile, extra_context: Optional[str] = None) -> str:
        """Legacy compatibility alias for improve_with_providers"""
        return await self.improve_with_providers(text, profile, extra_context)
    
    async def improve_with_providers(self, text: str, profile: AppProfile, extra_context: Optional[str] = None) -> str:
        """Improve text using LiteLLM with multi-provider fallbacks"""
        logger.info(f"🔧 improve_with_providers for profile: {profile.app_name}")
        llm_cfg: Dict[str, Any] = profile.llm_config or {}
        models = self._resolve_model_list(llm_cfg)
        temperature = float(llm_cfg.get('temperature', float(os.getenv('LLM_TEMPERATURE', '0.3'))))
        max_tokens_cfg = llm_cfg.get('max_tokens', int(os.getenv('LLM_MAX_TOKENS', '5000')))
        try:
            max_tokens = min(int(max_tokens_cfg), int(self._max_tokens_cap))
        except Exception:
            max_tokens = min(5000, int(self._max_tokens_cap))
        read_timeout = float(llm_cfg.get('timeout', self._client_timeout))
        reasoning_effort = llm_cfg.get('reasoning_effort', self._default_reasoning_effort) or None

        logger.info(f"Model order: {models}")
        logger.info(f"Temp={temperature}, MaxTokens={max_tokens}, Timeout={read_timeout}, Reasoning={reasoning_effort}")
        system_prompt = self._build_system_prompt(profile, extra_context)
        user_prompt = self._build_user_prompt(text, profile)
        content = await self._call_with_fallbacks(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            models=models,
            temperature=temperature,
            max_tokens=max_tokens,
            read_timeout=read_timeout,
            reasoning_effort=reasoning_effort,
        )

        if not content:
            logger.warning("All providers failed or returned empty. Returning original text.")
            return text

        improved = content
        xai_expl = ""
        try:
            data = json.loads(content)
            if isinstance(data, dict) and 'improved_text' in data:
                improved = str(data.get('improved_text') or "").strip()
                xai_expl = str(data.get('xai_explanation') or "").strip()
        except Exception:
            pass

        if not xai_expl and improved:
            explain_user_prompt = (
                "Provide a comprehensive explanation of the edits and rationale applied to improve the text.\n"
                "Return ONLY a JSON object with field 'xai_explanation' (no markdown).\n\n"
                f"Original: {text}\n\nImproved: {improved}"
            )
            exp_content = await self._call_with_fallbacks(
                system_prompt="You are an expert writing assistant that explains edits precisely.",
                user_prompt=explain_user_prompt,
                models=models,
                temperature=max(0.1, float(temperature) * 0.5),
                max_tokens=min(int(max_tokens), 8192),
                read_timeout=min(read_timeout, max(3.0, read_timeout * 0.75)),
                reasoning_effort=reasoning_effort,
            )
            if exp_content:
                try:
                    exp_data = json.loads(exp_content)
                    xai_expl = str(exp_data.get('xai_explanation') or "").strip()
                except Exception:
                    xai_expl = exp_content.strip()
                if xai_expl:
                    logger.info(f"🧠 Explanation length: {len(xai_expl)}")

        self._last_xai_explanation = xai_expl
        logger.success(f"✅ Processed: '{text[:30]}...' -> '{improved[:30]}...'")
        return improved or text
    
    async def process_transcription(self, transcription: str, app_class: Optional[str] = None) -> str:
        """Process transcription for text improvement (legacy)"""
        # Legacy method for backwards compatibility
        logger.info(f"🎯 Starting process_transcription: text='{transcription[:50]}...', app_class={app_class}")
        
        # Set active profile if app_class provided
        if app_class:
            logger.info(f"Setting active application: {app_class}")
            self.set_active_application(app_class)
        
        if not self.current_profile:
            logger.warning("No active profile, returning raw text")
            return transcription
        
        profile = self.current_profile
        logger.info(f"Processing with profile: {profile.app_name} (class: {profile.app_class})")
        logger.debug(f"Profile config: writing_style={profile.writing_style}, llm_config={profile.llm_config}")
        
        # Apply shortcuts/abbreviations
        processed_text = transcription
        abbr_count = 0
        for abbr, expansion in (profile.abbreviations or {}).items():
            if abbr in processed_text.lower():
                processed_text = processed_text.replace(abbr, expansion)
                abbr_count += 1
                logger.debug(f"Applied abbreviation: {abbr} -> {expansion}")
        
        if abbr_count > 0:
            logger.info(f"Applied {abbr_count} abbreviations")
        
        # Execute extra context commands only if defined
        extra_context = None
        if profile.extra_context and len(profile.extra_context) > 0:
            logger.info(f"Executing {len(profile.extra_context)} extra context commands")
            extra_context = await self.execute_extra_context(profile)
            if extra_context:
                logger.info(f"Gathered {len(extra_context)} chars of extra context")
                logger.debug(f"Extra context preview: {extra_context[:200]}...")
            else:
                logger.warning("No extra context gathered")
                extra_context = None  # Reset to None if nothing gathered
        else:
            logger.debug("No extra_context defined for this profile")
        
        # Improve with LiteLLM
        logger.info(f"🤖 Calling LiteLLM for improvement")
        improved_text = await self.improve_with_providers(
            text=processed_text,
            profile=profile,
            extra_context=extra_context
        )
        logger.success(f"✅ Text improved! Original: {len(transcription)} chars, Improved: {len(improved_text)} chars")
        logger.debug(f"Original: '{transcription[:100]}...'")
        logger.debug(f"Improved: '{improved_text[:100]}...'")
        # If we have an XAI explanation from the last call, log a concise summary
        xai_expl = getattr(self, "_last_xai_explanation", "")
        if xai_expl:
            logger.info(f"🧠 XAI explanation captured ({len(xai_expl)} chars)")
            logger.debug(f"XAI explanation: '{xai_expl[:300]}...'")
        
        return improved_text


# Test function
async def test_improvement():
    """Test the simple improvement engine"""
    engine = SimpleImprovementEngine()
    
    # Test with Windsurf profile
    engine.set_active_application("windsurf")
    
    test_text = "help me make a great ignore file for this project"
    improved = await engine.process_transcription(test_text)
    
    print(f"Original: {test_text}")
    print(f"Improved: {improved}")
    
    return improved != test_text  # Should be different if improvement worked


if __name__ == "__main__":
    asyncio.run(test_improvement())
