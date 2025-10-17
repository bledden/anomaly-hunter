"""
File system access utilities with user permission handling for CLI
"""

import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class FileAccessManager:
    """
    Manages file system access with user permissions.

    Features:
    - Read files and directories
    - Write files with user confirmation
    - Safety checks for file operations
    - Permission-based access control
    """

    def __init__(self, require_confirmation: bool = True, allowed_paths: Optional[List[str]] = None):
        """
        Initialize file access manager.

        Args:
            require_confirmation: If True, ask user before write operations
            allowed_paths: Optional list of allowed directory paths (None = all allowed)
        """
        self.require_confirmation = require_confirmation
        self.allowed_paths = [Path(p).resolve() for p in allowed_paths] if allowed_paths else None
        logger.info("FileAccessManager initialized")

    def is_path_allowed(self, path: Path) -> bool:
        """Check if path is within allowed directories"""
        if self.allowed_paths is None:
            return True

        resolved_path = path.resolve()
        for allowed in self.allowed_paths:
            try:
                resolved_path.relative_to(allowed)
                return True
            except ValueError:
                continue
        return False

    def read_file(self, file_path: str) -> Optional[str]:
        """
        Read a file's contents.

        Args:
            file_path: Path to file

        Returns:
            File contents as string, or None if error
        """
        try:
            path = Path(file_path).resolve()

            if not self.is_path_allowed(path):
                logger.error(f"Access denied: {file_path} is outside allowed paths")
                return None

            if not path.exists():
                logger.error(f"File not found: {file_path}")
                return None

            if not path.is_file():
                logger.error(f"Not a file: {file_path}")
                return None

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            logger.info(f"Read file: {file_path} ({len(content)} bytes)")
            return content

        except PermissionError:
            logger.error(f"Permission denied reading: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return None

    def write_file(self, file_path: str, content: str, overwrite: bool = False) -> bool:
        """
        Write content to a file.

        Args:
            file_path: Path to write to
            content: Content to write
            overwrite: If True, overwrite existing file without confirmation

        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(file_path).resolve()

            if not self.is_path_allowed(path):
                logger.error(f"Access denied: {file_path} is outside allowed paths")
                return False

            # Check if file exists and confirmation needed
            if path.exists() and self.require_confirmation and not overwrite:
                logger.warning(f"File exists: {file_path} (set overwrite=True to replace)")
                return False

            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Wrote file: {file_path} ({len(content)} bytes)")
            return True

        except PermissionError:
            logger.error(f"Permission denied writing: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Error writing {file_path}: {e}")
            return False

    def list_directory(self, dir_path: str, pattern: Optional[str] = None) -> Optional[List[str]]:
        """
        List files in a directory.

        Args:
            dir_path: Directory path
            pattern: Optional glob pattern (e.g., "*.py")

        Returns:
            List of file paths, or None if error
        """
        try:
            path = Path(dir_path).resolve()

            if not self.is_path_allowed(path):
                logger.error(f"Access denied: {dir_path} is outside allowed paths")
                return None

            if not path.exists():
                logger.error(f"Directory not found: {dir_path}")
                return None

            if not path.is_dir():
                logger.error(f"Not a directory: {dir_path}")
                return None

            if pattern:
                files = [str(p) for p in path.glob(pattern)]
            else:
                files = [str(p) for p in path.iterdir()]

            logger.info(f"Listed directory: {dir_path} ({len(files)} items)")
            return sorted(files)

        except PermissionError:
            logger.error(f"Permission denied listing: {dir_path}")
            return None
        except Exception as e:
            logger.error(f"Error listing {dir_path}: {e}")
            return None

    def read_json(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Read and parse JSON file"""
        content = self.read_file(file_path)
        if content is None:
            return None

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return None

    def write_json(self, file_path: str, data: Dict[str, Any], overwrite: bool = False) -> bool:
        """Write data as JSON file"""
        try:
            content = json.dumps(data, indent=2)
            return self.write_file(file_path, content, overwrite=overwrite)
        except Exception as e:
            logger.error(f"Error serializing JSON for {file_path}: {e}")
            return False

    def file_exists(self, file_path: str) -> bool:
        """Check if file exists"""
        try:
            path = Path(file_path).resolve()
            return path.exists() and path.is_file()
        except Exception:
            return False

    def directory_exists(self, dir_path: str) -> bool:
        """Check if directory exists"""
        try:
            path = Path(dir_path).resolve()
            return path.exists() and path.is_dir()
        except Exception:
            return False

    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file metadata"""
        try:
            path = Path(file_path).resolve()

            if not path.exists():
                return None

            stat = path.stat()
            return {
                'path': str(path),
                'name': path.name,
                'size': stat.st_size,
                'is_file': path.is_file(),
                'is_dir': path.is_dir(),
                'modified': stat.st_mtime,
                'created': stat.st_ctime
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return None
