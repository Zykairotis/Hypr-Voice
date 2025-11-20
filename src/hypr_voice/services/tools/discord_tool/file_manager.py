"""
Discord File Manager for Helper Agent

This module provides comprehensive file handling for Discord Bot integration,
enabling download, upload, and processing of various file types.
"""

import asyncio
import logging
import tempfile
import os
import csv
import json
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import discord

logger = logging.getLogger(__name__)


class DiscordFileManager:
    """
    File manager for Discord Bot integration.

    Handles:
    - File downloads from Discord
    - File uploads to Discord
    - File processing and analysis
    - File type validation
    """

    def __init__(self, bot: discord.Client, temp_dir: Optional[str] = None):
        """
        Initialize Discord file manager.

        Args:
            bot: Discord bot client
            temp_dir: Temporary directory for file storage
        """
        self.bot = bot
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "discord_files"
        self.max_file_size_mb = 8  # Discord standard limit
        self.allowed_extensions = {'.txt', '.md', '.csv', '.json', '.xml', '.yaml', '.yml', '.log', '.py', '.js', '.html', '.css'}

        # Create temp directory if it doesn't exist
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # File processing configuration
        self.max_text_length = 50000  # Max characters to process
        self.csv_max_rows = 1000  # Max CSV rows to process

    async def download_file(self, attachment: discord.Attachment) -> Optional[str]:
        """
        Download a file from Discord attachment.

        Args:
            attachment: Discord attachment object

        Returns:
            Local file path or None if download failed
        """
        try:
            # Validate file
            if not self._validate_attachment(attachment):
                logger.error(f"Attachment validation failed: {attachment.filename}")
                return None

            # Create local file path
            local_path = self.temp_dir / f"{attachment.id}_{attachment.filename}"

            # Download file
            await attachment.save(local_path)

            logger.info(f"Downloaded file: {attachment.filename} -> {local_path}")
            return str(local_path)

        except Exception as e:
            logger.error(f"Failed to download file {attachment.filename}: {e}")
            return None

    async def upload_file(self, channel_id: int, file_path: str, content: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Upload a file to a Discord channel.

        Args:
            channel_id: Target channel ID
            file_path: Path to file to upload
            content: Optional message content

        Returns:
            Upload result or None if failed
        """
        try:
            # Validate file
            if not self._validate_local_file(file_path):
                logger.error(f"Local file validation failed: {file_path}")
                return None

            channel = self.bot.get_channel(channel_id)
            if not channel or not isinstance(channel, discord.TextChannel):
                logger.error(f"Invalid channel: {channel_id}")
                return None

            # Create Discord file object
            discord_file = discord.File(file_path)

            # Send file
            message = await channel.send(content=content, file=discord_file)

            return {
                "message_id": message.id,
                "channel_id": message.channel.id,
                "file_name": discord_file.filename,
                "content": message.content,
                "attachments": [att.url for att in message.attachments],
                "timestamp": message.created_at
            }

        except Exception as e:
            logger.error(f"Failed to upload file {file_path} to channel {channel_id}: {e}")
            return None

    async def analyze_file(self, file_path: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a file and extract information.

        Args:
            file_path: Path to file to analyze
            filename: Original filename (optional)

        Returns:
            Analysis result dictionary
        """
        try:
            if not filename:
                filename = Path(file_path).name

            file_ext = Path(filename).suffix.lower()
            file_size = os.path.getsize(file_path)

            analysis = {
                "filename": filename,
                "file_size": file_size,
                "file_type": file_ext,
                "mime_type": mimetypes.guess_type(filename)[0],
                "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)),
                "analysis_timestamp": datetime.utcnow()
            }

            # Analyze based on file type
            if file_ext in ['.txt', '.md', '.log']:
                analysis.update(await self._analyze_text_file(file_path))
            elif file_ext == '.csv':
                analysis.update(await self._analyze_csv_file(file_path))
            elif file_ext == '.json':
                analysis.update(await self._analyze_json_file(file_path))
            elif file_ext in ['.yaml', '.yml']:
                analysis.update(await self._analyze_yaml_file(file_path))
            elif file_ext in ['.py', '.js', '.html', '.css']:
                analysis.update(await self._analyze_code_file(file_path))
            else:
                analysis.update(await self._analyze_binary_file(file_path))

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze file {file_path}: {e}")
            return {"error": f"File analysis failed: {str(e)}"}

    async def process_file_content(self, file_path: str, max_length: int = None) -> Dict[str, Any]:
        """
        Process and extract content from a file.

        Args:
            file_path: Path to file
            max_length: Maximum content length to return

        Returns:
            Content processing result
        """
        try:
            if max_length is None:
                max_length = self.max_text_length

            file_ext = Path(file_path).suffix.lower()
            file_size = os.path.getsize(file_path)

            # Check if file is too large
            if file_size > max_length * 10:  # Rough estimate
                return {
                    "error": f"File too large ({file_size} bytes). Maximum size: {max_length * 10} bytes",
                    "file_size": file_size
                }

            # Extract content based on file type
            if file_ext in ['.txt', '.md', '.log', '.py', '.js', '.html', '.css']:
                content = await self._extract_text_content(file_path, max_length)
            elif file_ext == '.csv':
                content = await self._extract_csv_content(file_path, max_length)
            elif file_ext == '.json':
                content = await self._extract_json_content(file_path, max_length)
            else:
                content = await self._extract_binary_content(file_path, max_length)

            return {
                "content": content,
                "content_length": len(content) if content else 0,
                "file_type": file_ext,
                "truncated": len(content) >= max_length if content else False
            }

        except Exception as e:
            logger.error(f"Failed to process file content {file_path}: {e}")
            return {"error": f"Content processing failed: {str(e)}"}

    async def create_summary_report(self, file_path: str) -> Dict[str, Any]:
        """
        Create a summary report for a file.

        Args:
            file_path: Path to file

        Returns:
            Summary report dictionary
        """
        try:
            analysis = await self.analyze_file(file_path)
            content_result = await self.process_file_content(file_path, 1000)

            report = {
                "file_info": {
                    "filename": analysis.get("filename"),
                    "size": analysis.get("file_size"),
                    "type": analysis.get("file_type"),
                    "mime_type": analysis.get("mime_type")
                },
                "summary": analysis.get("summary", ""),
                "statistics": analysis.get("statistics", {}),
                "preview": content_result.get("content", "")[:500],
                "content_length": content_result.get("content_length", 0),
                "analysis_timestamp": analysis.get("analysis_timestamp")
            }

            return report

        except Exception as e:
            logger.error(f"Failed to create summary report for {file_path}: {e}")
            return {"error": f"Summary report creation failed: {str(e)}"}

    async def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up temporary files older than specified age."""
        try:
            current_time = datetime.now()
            cleaned_count = 0

            for file_path in self.temp_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_age.total_seconds() > max_age_hours * 3600:
                        file_path.unlink()
                        cleaned_count += 1

            logger.info(f"Cleaned up {cleaned_count} temporary files")

        except Exception as e:
            logger.error(f"Failed to cleanup temporary files: {e}")

    def _validate_attachment(self, attachment: discord.Attachment) -> bool:
        """Validate Discord attachment."""
        # Check file size
        if attachment.size > self.max_file_size_mb * 1024 * 1024:
            logger.error(f"File too large: {attachment.size} bytes > {self.max_file_size_mb * 1024 * 1024}")
            return False

        # Check file extension
        file_ext = Path(attachment.filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            logger.error(f"File type not allowed: {file_ext}")
            return False

        return True

    def _validate_local_file(self, file_path: str) -> bool:
        """Validate local file."""
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            return False

        if not os.path.isfile(file_path):
            logger.error(f"Path is not a file: {file_path}")
            return False

        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size_mb * 1024 * 1024:
            logger.error(f"File too large: {file_size} bytes")
            return False

        return True

    async def _analyze_text_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze text file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            lines = content.splitlines()
            words = content.split()

            return {
                "file_category": "text",
                "lines": len(lines),
                "characters": len(content),
                "words": len(words),
                "non_empty_lines": len([line for line in lines if line.strip()]),
                "summary": f"Text file with {len(lines)} lines, {len(words)} words",
                "statistics": {
                    "avg_line_length": sum(len(line) for line in lines) / len(lines) if lines else 0,
                    "max_line_length": max(len(line) for line in lines) if lines else 0,
                    "word_count": len(words)
                }
            }

        except Exception as e:
            logger.error(f"Failed to analyze text file {file_path}: {e}")
            return {"error": f"Text file analysis failed: {str(e)}"}

    async def _analyze_csv_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze CSV file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                rows = list(reader)

            if not rows:
                return {"error": "CSV file is empty"}

            headers = rows[0]
            data_rows = rows[1:]

            return {
                "file_category": "csv",
                "total_rows": len(rows),
                "data_rows": len(data_rows),
                "columns": len(headers),
                "headers": headers,
                "summary": f"CSV file with {len(data_rows)} rows and {len(headers)} columns",
                "statistics": {
                    "columns": len(headers),
                    "data_rows": len(data_rows),
                    "headers": headers[:10]  # First 10 headers
                }
            }

        except Exception as e:
            logger.error(f"Failed to analyze CSV file {file_path}: {e}")
            return {"error": f"CSV file analysis failed: {str(e)}"}

    async def _analyze_json_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)

            def analyze_structure(obj, depth=0, max_depth=3):
                if depth > max_depth:
                    return {"type": type(obj).__name__, "depth_exceeded": True}

                if isinstance(obj, dict):
                    return {
                        "type": "object",
                        "keys": list(obj.keys())[:10],  # First 10 keys
                        "key_count": len(obj),
                        "children": {k: analyze_structure(v, depth + 1) for k, v in list(obj.items())[:5]}
                    }
                elif isinstance(obj, list):
                    return {
                        "type": "array",
                        "length": len(obj),
                        "sample_items": [analyze_structure(item, depth + 1) for item in obj[:5]]
                    }
                else:
                    return {"type": type(obj).__name__, "value": str(obj)[:100]}

            structure = analyze_structure(data)

            return {
                "file_category": "json",
                "root_type": structure.get("type"),
                "summary": f"JSON file with root type: {structure.get('type')}",
                "structure": structure,
                "statistics": {
                    "root_type": structure.get("type"),
                    "keys_count": structure.get("key_count", 0) if structure.get("type") == "object" else None,
                    "array_length": structure.get("length", 0) if structure.get("type") == "array" else None
                }
            }

        except Exception as e:
            logger.error(f"Failed to analyze JSON file {file_path}: {e}")
            return {"error": f"JSON file analysis failed: {str(e)}"}

    async def _analyze_yaml_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze YAML file."""
        try:
            # Try to import yaml
            try:
                import yaml
            except ImportError:
                return {"error": "PyYAML not installed. Cannot analyze YAML files."}

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = yaml.safe_load(f)

            if isinstance(data, dict):
                return {
                    "file_category": "yaml",
                    "summary": f"YAML configuration file with {len(data)} top-level keys",
                    "keys": list(data.keys())[:10],
                    "statistics": {"key_count": len(data)}
                }
            else:
                return {
                    "file_category": "yaml",
                    "summary": f"YAML file with root type: {type(data).__name__}",
                    "statistics": {"root_type": type(data).__name__}
                }

        except Exception as e:
            logger.error(f"Failed to analyze YAML file {file_path}: {e}")
            return {"error": f"YAML file analysis failed: {str(e)}"}

    async def _analyze_code_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze code file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            lines = content.splitlines()

            # Simple code metrics
            comment_lines = 0
            empty_lines = 0
            code_lines = 0

            file_ext = Path(file_path).suffix.lower()

            # Comment patterns for different languages
            comment_patterns = {
                '.py': ['#'],
                '.js': ['//', '/*', '*'],
                '.html': ['<!--', '-->'],
                '.css': ['/*', '*']
            }

            comment_indicators = comment_patterns.get(file_ext, ['#', '//'])

            for line in lines:
                stripped = line.strip()
                if not stripped:
                    empty_lines += 1
                elif any(stripped.startswith(indicator) for indicator in comment_indicators):
                    comment_lines += 1
                else:
                    code_lines += 1

            return {
                "file_category": "code",
                "language": file_ext[1:],  # Remove the dot
                "lines": len(lines),
                "code_lines": code_lines,
                "comment_lines": comment_lines,
                "empty_lines": empty_lines,
                "summary": f"Code file ({file_ext[1:]}) with {len(lines)} lines",
                "statistics": {
                    "total_lines": len(lines),
                    "code_lines": code_lines,
                    "comment_lines": comment_lines,
                    "empty_lines": empty_lines
                }
            }

        except Exception as e:
            logger.error(f"Failed to analyze code file {file_path}: {e}")
            return {"error": f"Code file analysis failed: {str(e)}"}

    async def _analyze_binary_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze binary file."""
        try:
            file_size = os.path.getsize(file_path)

            return {
                "file_category": "binary",
                "summary": f"Binary file ({file_size} bytes)",
                "statistics": {"size_bytes": file_size}
            }

        except Exception as e:
            logger.error(f"Failed to analyze binary file {file_path}: {e}")
            return {"error": f"Binary file analysis failed: {str(e)}"}

    async def _extract_text_content(self, file_path: str, max_length: int) -> str:
        """Extract content from text file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(max_length + 1)  # Read one extra to check if truncated

            if len(content) > max_length:
                content = content[:max_length] + "...[truncated]"

            return content

        except Exception as e:
            logger.error(f"Failed to extract text content from {file_path}: {e}")
            return f"Error extracting content: {str(e)}"

    async def _extract_csv_content(self, file_path: str, max_length: int) -> str:
        """Extract content from CSV file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                rows = list(reader)

            # Limit rows to prevent too much content
            max_rows = min(len(rows), 50)  # Max 50 rows
            limited_rows = rows[:max_rows]

            content = []
            for i, row in enumerate(limited_rows):
                row_str = ', '.join(str(cell) for cell in row)
                content.append(f"Row {i+1}: {row_str}")

            result = '\n'.join(content)

            if len(rows) > max_rows:
                result += f"\n...[{len(rows) - max_rows} more rows]"

            if len(result) > max_length:
                result = result[:max_length] + "...[truncated]"

            return result

        except Exception as e:
            logger.error(f"Failed to extract CSV content from {file_path}: {e}")
            return f"Error extracting CSV content: {str(e)}"

    async def _extract_json_content(self, file_path: str, max_length: int) -> str:
        """Extract content from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)

            result = json.dumps(data, indent=2, ensure_ascii=False)

            if len(result) > max_length:
                result = result[:max_length] + "...[truncated]"

            return result

        except Exception as e:
            logger.error(f"Failed to extract JSON content from {file_path}: {e}")
            return f"Error extracting JSON content: {str(e)}"

    async def _extract_binary_content(self, file_path: str, max_length: int) -> str:
        """Extract content from binary file."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read(min(max_length, 1024))  # Read first 1KB max

            # Convert to hex representation
            hex_content = content.hex()
            result = ' '.join(hex_content[i:i+2] for i in range(0, len(hex_content), 2))

            return f"Binary file content (hex representation):\n{result}"

        except Exception as e:
            logger.error(f"Failed to extract binary content from {file_path}: {e}")
            return f"Error extracting binary content: {str(e)}"

    def get_temp_directory(self) -> str:
        """Get temporary directory path."""
        return str(self.temp_dir)

    def get_file_statistics(self) -> Dict[str, Any]:
        """Get file manager statistics."""
        try:
            temp_files = list(self.temp_dir.iterdir())
            total_size = sum(f.stat().st_size for f in temp_files if f.is_file())

            return {
                "temp_directory": str(self.temp_dir),
                "temp_files_count": len(temp_files),
                "total_temp_size": total_size,
                "max_file_size_mb": self.max_file_size_mb,
                "allowed_extensions": list(self.allowed_extensions)
            }

        except Exception as e:
            logger.error(f"Failed to get file statistics: {e}")
            return {"error": f"Failed to get statistics: {str(e)}"}