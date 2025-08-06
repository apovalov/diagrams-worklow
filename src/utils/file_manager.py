"""File management utilities for temporary diagram files."""

import asyncio
import logging
import time
from pathlib import Path
from uuid import uuid4

from src.config import settings

logger = logging.getLogger(__name__)


class FileManager:
    """Manages temporary files for diagram generation."""

    def __init__(self, temp_dir: Path | None = None):
        """Initialize the file manager.

        Args:
            temp_dir: Directory for temporary files. Uses settings.temp_dir if None.
        """
        self.temp_dir = temp_dir or settings.temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def generate_filename(self, extension: str = "png") -> str:
        """Generate a unique filename.

        Args:
            extension: File extension without the dot

        Returns:
            Unique filename with extension
        """
        unique_id = str(uuid4())
        return f"diagram_{unique_id}.{extension}"

    def get_temp_path(self, filename: str | None = None) -> Path:
        """Get a temporary file path.

        Args:
            filename: Specific filename to use. Generated if None.

        Returns:
            Path to temporary file
        """
        if filename is None:
            filename = self.generate_filename()

        return self.temp_dir / filename

    def create_temp_file(self, content: bytes, extension: str = "png") -> Path:
        """Create a temporary file with content.

        Args:
            content: File content as bytes
            extension: File extension without the dot

        Returns:
            Path to created file
        """
        filename = self.generate_filename(extension)
        file_path = self.temp_dir / filename

        with file_path.open("wb") as f:
            f.write(content)

        logger.debug(f"Created temporary file: {file_path}")
        return file_path

    def cleanup_old_files(self, max_age_minutes: int | None = None) -> int:
        """Clean up old temporary files.

        Args:
            max_age_minutes: Maximum age in minutes. Uses settings value if None.

        Returns:
            Number of files cleaned up
        """
        if max_age_minutes is None:
            max_age_minutes = settings.max_file_age_minutes

        max_age_seconds = max_age_minutes * 60
        current_time = time.time()
        cleaned_count = 0

        try:
            for file_path in self.temp_dir.iterdir():
                if not file_path.is_file():
                    continue

                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                        logger.debug(f"Cleaned up old file: {file_path}")
                    except OSError as e:
                        logger.warning(f"Failed to delete {file_path}: {e}")

        except OSError as e:
            logger.error(f"Error during cleanup: {e}")

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old temporary files")

        return cleaned_count

    def delete_file(self, file_path: Path) -> bool:
        """Delete a specific file.

        Args:
            file_path: Path to file to delete

        Returns:
            True if file was deleted successfully
        """
        try:
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Deleted file: {file_path}")
                return True
            return False
        except OSError as e:
            logger.warning(f"Failed to delete {file_path}: {e}")
            return False

    def get_file_size(self, file_path: Path) -> int | None:
        """Get file size in bytes.

        Args:
            file_path: Path to file

        Returns:
            File size in bytes, or None if file doesn't exist
        """
        try:
            return file_path.stat().st_size
        except OSError:
            return None

    def ensure_temp_dir_exists(self) -> None:
        """Ensure the temporary directory exists."""
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def cleanup_periodically(self, interval_minutes: int = 30) -> None:
        """Periodically clean up old files.

        Args:
            interval_minutes: Cleanup interval in minutes
        """
        interval_seconds = interval_minutes * 60

        while True:
            try:
                await asyncio.sleep(interval_seconds)
                self.cleanup_old_files()
            except asyncio.CancelledError:
                logger.info("Periodic cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")


# Global file manager instance
file_manager = FileManager()
