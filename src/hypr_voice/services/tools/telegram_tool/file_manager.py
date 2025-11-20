"""
Telegram File Manager for Helper Agent

This module handles file operations for Telegram Bot API integration,
including downloading, uploading, and processing files.
"""

import asyncio
import logging
import os
import tempfile
import aiofiles
import csv
import json
from typing import Dict, List, Optional, Any, Union, BinaryIO
from datetime import datetime
from pathlib import Path

try:
    from telegram import Document, PhotoSize, Bot
    from telegram.constants import ParseMode
except ImportError:
    raise ImportError("python-telegram-bot is required for Telegram integration")

logger = logging.getLogger(__name__)


class TelegramFileManager:
    """
    Manages file operations for Telegram Bot API integration.

    Provides functionality to:
    - Download files from Telegram
    - Upload files to Telegram
    - Process different file types
    - Validate file security
    - Manage temporary files
    """

    def __init__(self, bot: Bot, temp_dir: Optional[str] = None):
        """
        Initialize Telegram file manager.

        Args:
            bot: Telegram bot instance
            temp_dir: Temporary directory for file operations
        """
        self.bot = bot
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "telegram_files"
        self.temp_dir.mkdir(exist_ok=True)

        # File limits and security
        self.max_file_size_mb = 20
        self.allowed_extensions = {
            # Text files
            '.txt', '.md', '.json', '.xml', '.yaml', '.yml', '.csv',
            # Documents
            '.pdf', '.doc', '.docx', '.odt',
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.webp',
            # Archives
            '.zip', '.tar', '.gz', '.bz2',
            # Data files
            '.xlsx', '.xls', '.ods'
        }

        # Track active downloads
        self.active_downloads: Dict[str, Dict[str, Any]] = {}

        logger.info(f"Telegram file manager initialized with temp dir: {self.temp_dir}")

    async def download_file(
        self,
        file_id: str,
        filename: Optional[str] = None,
        chat_id: Optional[Union[str, int]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Download a file from Telegram.

        Args:
            file_id: Telegram file ID
            filename: Optional custom filename
            chat_id: Optional chat ID for tracking

        Returns:
            Dictionary containing download information or None if failed
        """
        try:
            # Get file object from Telegram
            file_obj = await self.bot.get_file(file_id)

            # Generate filename if not provided
            if not filename:
                filename = file_obj.file_path.split('/')[-1]

            # Validate file security
            if not self._validate_file_security(file_obj, filename):
                return None

            # Create download path
            download_path = self.temp_dir / filename

            # Track download
            download_id = f"{file_id}_{datetime.now().isoformat()}"
            self.active_downloads[download_id] = {
                "file_id": file_id,
                "filename": filename,
                "chat_id": chat_id,
                "download_path": str(download_path),
                "started_at": datetime.now(),
                "status": "downloading"
            }

            logger.info(f"Starting download: {filename} ({file_obj.file_size} bytes)")

            # Download file
            async with aiofiles.open(download_path, 'wb') as file:
                async for chunk in file_obj.download_to_bytearray():
                    await file.write(chunk)

            # Update download status
            self.active_downloads[download_id]["status"] = "completed"
            self.active_downloads[download_id]["completed_at"] = datetime.now()
            self.active_downloads[download_id]["file_size"] = download_path.stat().st_size

            # Get file info
            file_info = await self._get_file_info(download_path)

            logger.info(f"Successfully downloaded: {filename}")

            return {
                "download_id": download_id,
                "file_path": str(download_path),
                "filename": filename,
                "file_info": file_info,
                "status": "completed"
            }

        except Exception as e:
            logger.error(f"Failed to download file {file_id}: {e}")
            return None

    async def upload_file(
        self,
        chat_id: Union[str, int],
        file_path: Union[str, Path],
        caption: Optional[str] = None,
        reply_to_message_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Upload a file to Telegram.

        Args:
            chat_id: Target chat ID
            file_path: Path to file to upload
            caption: Optional file caption
            reply_to_message_id: Reply to specific message

        Returns:
            Dictionary containing upload information or None if failed
        """
        try:
            file_path = Path(file_path)

            # Validate file
            if not file_path.exists():
                logger.error(f"File does not exist: {file_path}")
                return None

            if not self._validate_upload_file(file_path):
                return None

            # Upload file
            with open(file_path, 'rb') as file:
                message = await self.bot.send_document(
                    chat_id=chat_id,
                    document=file,
                    caption=caption,
                    reply_to_message_id=reply_to_message_id
                )

            logger.info(f"Successfully uploaded file to {chat_id}: {file_path.name}")

            return {
                "message_id": message.message_id,
                "chat_id": message.chat.id,
                "document_id": message.document.file_id,
                "file_name": message.document.file_name,
                "file_size": message.document.file_size,
                "caption": message.caption,
                "upload_time": datetime.now()
            }

        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            return None

    async def process_csv_file(
        self,
        file_path: Union[str, Path],
        analysis_options: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process a CSV file and extract data.

        Args:
            file_path: Path to CSV file
            analysis_options: Options for processing

        Returns:
            Dictionary containing CSV analysis results
        """
        try:
            file_path = Path(file_path)
            analysis_options = analysis_options or {}

            # Read CSV file
            async with aiofiles.open(file_path, 'r', encoding='utf-8', newline='') as file:
                content = await file.read()

                # Detect delimiter
                sample = content[:1024]
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample)

                # Reset file pointer
                await file.seek(0)

                # Read full CSV
                reader = csv.DictReader(file, delimiter=delimiter)
                rows = []
                headers = None

                async for row in reader:
                    if headers is None:
                        headers = reader.fieldnames
                    rows.append(row)

            # Analyze CSV data
            analysis = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "headers": headers,
                "total_rows": len(rows),
                "total_columns": len(headers) if headers else 0,
                "file_size": file_path.stat().st_size,
                "delimiter": delimiter,
                "encoding": "utf-8"
            }

            # Data analysis
            if rows:
                analysis.update(await self._analyze_csv_data(rows, analysis_options))

            logger.info(f"Processed CSV file: {file_path.name} ({len(rows)} rows, {len(headers)} columns)")

            return analysis

        except Exception as e:
            logger.error(f"Failed to process CSV file {file_path}: {e}")
            return None

    async def process_text_file(
        self,
        file_path: Union[str, Path],
        max_length: int = 10000
    ) -> Optional[Dict[str, Any]]:
        """
        Process a text file and extract content.

        Args:
            file_path: Path to text file
            max_length: Maximum characters to read

        Returns:
            Dictionary containing text file analysis
        """
        try:
            file_path = Path(file_path)

            # Read file content
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                content = await file.read()

                # Truncate if too long
                if len(content) > max_length:
                    content = content[:max_length] + "... [truncated]"

            # Analyze text
            analysis = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "content": content,
                "character_count": len(content),
                "word_count": len(content.split()),
                "line_count": content.count('\n'),
                "file_size": file_path.stat().st_size
            }

            # Additional analysis
            analysis.update(await self._analyze_text_content(content))

            logger.info(f"Processed text file: {file_path.name} ({len(content)} characters)")

            return analysis

        except Exception as e:
            logger.error(f"Failed to process text file {file_path}: {e}")
            return None

    async def create_summary_file(
        self,
        summary_text: str,
        filename: Optional[str] = None,
        chat_id: Optional[Union[str, int]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a summary file from text.

        Args:
            summary_text: Summary text to save
            filename: Optional custom filename
            chat_id: Optional chat ID for context

        Returns:
            Dictionary containing file creation information
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"summary_{timestamp}.md"

            file_path = self.temp_dir / filename

            # Write summary to file
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
                await file.write(summary_text)

            # Get file info
            file_info = await self._get_file_info(file_path)

            logger.info(f"Created summary file: {filename}")

            return {
                "file_path": str(file_path),
                "filename": filename,
                "chat_id": chat_id,
                "content_length": len(summary_text),
                "file_info": file_info,
                "created_at": datetime.now()
            }

        except Exception as e:
            logger.error(f"Failed to create summary file: {e}")
            return None

    async def send_processed_file(
        self,
        chat_id: Union[str, int],
        file_path: Union[str, Path],
        processing_results: Dict[str, Any],
        original_filename: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send a processed file back to the user.

        Args:
            chat_id: Target chat ID
            file_path: Path to processed file
            processing_results: Results of processing
            original_filename: Original filename for context

        Returns:
            Dictionary containing send operation result
        """
        try:
            file_path = Path(file_path)

            # Create caption with processing results
            caption = self._create_processing_caption(
                processing_results, original_filename
            )

            # Upload the processed file
            result = await self.upload_file(
                chat_id=chat_id,
                file_path=file_path,
                caption=caption
            )

            if result:
                result["processing_results"] = processing_results
                result["original_filename"] = original_filename

            return result

        except Exception as e:
            logger.error(f"Failed to send processed file {file_path}: {e}")
            return None

    async def cleanup_temp_files(self, older_than_hours: int = 24):
        """Clean up temporary files older than specified hours."""
        try:
            cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
            cleaned_count = 0

            for file_path in self.temp_dir.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1

            logger.info(f"Cleaned up {cleaned_count} temporary files older than {older_than_hours} hours")

        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")

    async def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get detailed information about a file."""
        try:
            stat = file_path.stat()

            # Get file extension
            extension = file_path.suffix.lower()

            # Detect file type
            file_type = "unknown"
            if extension in ['.txt', '.md']:
                file_type = "text"
            elif extension in ['.csv']:
                file_type = "csv"
            elif extension in ['.json']:
                file_type = "json"
            elif extension in ['.pdf']:
                file_type = "pdf"
            elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                file_type = "image"
            elif extension in ['.zip', '.tar', '.gz']:
                file_type = "archive"

            return {
                "file_name": file_path.name,
                "file_size": stat.st_size,
                "file_type": file_type,
                "extension": extension,
                "created_time": datetime.fromtimestamp(stat.st_ctime),
                "modified_time": datetime.fromtimestamp(stat.st_mtime),
                "is_readable": os.access(file_path, os.R_OK)
            }

        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return {}

    def _validate_file_security(self, file_obj: Any, filename: str) -> bool:
        """Validate file security before download."""
        try:
            # Check file size
            if file_obj.file_size and file_obj.file_size > (self.max_file_size_mb * 1024 * 1024):
                logger.warning(f"File too large: {file_obj.file_size} bytes")
                return False

            # Check file extension
            file_extension = Path(filename).suffix.lower()
            if file_extension not in self.allowed_extensions:
                logger.warning(f"File extension not allowed: {file_extension}")
                return False

            # Check filename for suspicious patterns
            suspicious_patterns = [
                '.exe', '.bat', '.cmd', '.scr', '.pif', '.com',
                '.jar', '.app', '.deb', '.rpm', '.dmg', '.pkg'
            ]

            for pattern in suspicious_patterns:
                if pattern in filename.lower():
                    logger.warning(f"Suspicious file pattern detected: {pattern}")
                    return False

            return True

        except Exception as e:
            logger.error(f"File security validation error: {e}")
            return False

    def _validate_upload_file(self, file_path: Path) -> bool:
        """Validate file before upload."""
        try:
            # Check if file exists
            if not file_path.exists():
                return False

            # Check file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                logger.warning(f"File too large for upload: {file_size_mb:.2f}MB")
                return False

            # Check file extension
            file_extension = file_path.suffix.lower()
            if file_extension not in self.allowed_extensions:
                logger.warning(f"File extension not allowed for upload: {file_extension}")
                return False

            return True

        except Exception as e:
            logger.error(f"Upload file validation error: {e}")
            return False

    async def _analyze_csv_data(self, rows: List[Dict[str, Any]], options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze CSV data and provide insights."""
        analysis = {
            "data_sample": rows[:5] if len(rows) > 5 else rows,  # First 5 rows as sample
            "numeric_columns": [],
            "text_columns": [],
            "empty_values_count": 0,
            "data_quality": "good"
        }

        if not rows:
            return analysis

        headers = rows[0].keys()

        # Analyze column types
        for header in headers:
            values = [row.get(header) for row in rows if header in row]
            non_empty_values = [v for v in values if v and v.strip()]

            if not non_empty_values:
                analysis["empty_values_count"] += len(values)
                continue

            # Check if column is numeric
            numeric_count = 0
            for value in non_empty_values:
                try:
                    float(value)
                    numeric_count += 1
                except ValueError:
                    pass

            if numeric_count / len(non_empty_values) > 0.8:
                analysis["numeric_columns"].append(header)
            else:
                analysis["text_columns"].append(header)

        # Assess data quality
        total_cells = len(rows) * len(headers)
        empty_ratio = analysis["empty_values_count"] / total_cells

        if empty_ratio > 0.3:
            analysis["data_quality"] = "poor"
        elif empty_ratio > 0.1:
            analysis["data_quality"] = "fair"

        return analysis

    async def _analyze_text_content(self, content: str) -> Dict[str, Any]:
        """Analyze text content for insights."""
        analysis = {
            "sentence_count": content.count('.') + content.count('!') + content.count('?'),
            "avg_sentence_length": 0,
            "word_count": len(content.split()),
            "has_urls": bool('http://' in content or 'https://' in content),
            "has_emails": bool('@' in content and '.' in content.split('@')[1]),
            "readability_score": 0
        }

        # Calculate average sentence length
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        if sentences:
            total_words = sum(len(s.split()) for s in sentences)
            analysis["avg_sentence_length"] = total_words / len(sentences)

        # Simple readability score
        if analysis["word_count"] > 0:
            avg_sentence = analysis["avg_sentence_length"]
            if avg_sentence < 10:
                analysis["readability_score"] = 8.0
            elif avg_sentence < 20:
                analysis["readability_score"] = 6.0
            elif avg_sentence < 30:
                analysis["readability_score"] = 4.0
            else:
                analysis["readability_score"] = 2.0

        return analysis

    def _create_processing_caption(
        self,
        results: Dict[str, Any],
        original_filename: Optional[str]
    ) -> str:
        """Create a caption for processed files."""
        caption_parts = []

        if original_filename:
            caption_parts.append(f"📄 Original: *{original_filename}*")

        # Add processing summary
        if "summary" in results:
            summary = results["summary"]
            caption_parts.append(f"📝 Summary: {summary[:100]}{'...' if len(summary) > 100 else ''}")

        if "analysis" in results:
            analysis = results["analysis"]
            if "overall_assessment" in analysis:
                caption_parts.append(f"🔍 Assessment: {analysis['overall_assessment'][:80]}{'...' if len(analysis['overall_assessment']) > 80 else ''}")

        if "processing_time" in results:
            caption_parts.append(f"⏱️ Processed in: {results['processing_time']:.2f}s")

        if "metrics" in results:
            metrics = results["metrics"]
            if "word_count" in metrics:
                caption_parts.append(f"📊 Words: {metrics['word_count']:,}")

        return "\n".join(caption_parts)

    def get_temp_directory(self) -> str:
        """Get the temporary directory path."""
        return str(self.temp_dir)

    def get_active_downloads(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active downloads."""
        return self.active_downloads.copy()

    def clear_completed_downloads(self, older_than_hours: int = 1):
        """Clear completed downloads from tracking."""
        cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)

        completed_downloads = [
            download_id for download_id, download_info in self.active_downloads.items()
            if download_info.get("status") == "completed" and
            download_info.get("completed_at", datetime.now()).timestamp() < cutoff_time
        ]

        for download_id in completed_downloads:
            del self.active_downloads[download_id]

        logger.info(f"Cleared {len(completed_downloads)} completed download records")


# Factory function for easy file manager creation
def create_telegram_file_manager(
    bot: Bot,
    temp_dir: Optional[str] = None
) -> TelegramFileManager:
    """
    Create and initialize a Telegram file manager.

    Args:
        bot: Telegram bot instance
        temp_dir: Optional temporary directory

    Returns:
        Initialized Telegram file manager
    """
    return TelegramFileManager(bot, temp_dir)