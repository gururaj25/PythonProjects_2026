"""
File Scanner Module
Recursively scans directories and extracts file content for SQL parsing.
"""

import os
import logging
import chardet
from pathlib import Path
from typing import List, Dict, Optional, Generator
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ScannedFile:
    file_path: str
    file_name: str
    folder_path: str
    extension: str
    size_bytes: int
    content: str
    encoding: str
    line_count: int
    scan_status: str = "success"
    error_message: str = ""


@dataclass
class ScanResult:
    scanned_files: List[ScannedFile] = field(default_factory=list)
    failed_files: List[Dict] = field(default_factory=list)
    total_files_found: int = 0
    total_files_scanned: int = 0
    total_files_failed: int = 0
    total_size_bytes: int = 0


class FileScanner:
    def __init__(self, config: Dict):
        self.config = config
        self.scanner_config = config.get("scanner", {})
        self.default_extensions = set(
            self.scanner_config.get("default_extensions", [".sql", ".txt", ".log"])
        )
        self.exclude_extensions = set(
            self.scanner_config.get("exclude_extensions", [])
        )
        self.max_file_size = (
            self.scanner_config.get("max_file_size_mb", 100) * 1024 * 1024
        )
        self.encoding_fallbacks = self.scanner_config.get(
            "encoding_fallbacks", ["utf-8", "latin-1", "cp1252"]
        )

    def scan_directory(
        self,
        directory: str,
        extensions: Optional[List[str]] = None,
        keyword_filter: Optional[List[str]] = None,
        exclude_dirs: Optional[List[str]] = None,
    ) -> ScanResult:
        result = ScanResult()
        target_extensions = set(extensions) if extensions else self.default_extensions
        exclude_dirs = set(exclude_dirs or [".git", "__pycache__", "node_modules"])

        if not os.path.exists(directory):
            logger.error(f"Directory does not exist: {directory}")
            return result

        logger.info(f"Starting scan of directory: {directory}")
        all_files = list(self._walk_directory(directory, target_extensions, exclude_dirs))
        result.total_files_found = len(all_files)
        logger.info(f"Found {len(all_files)} files to process")

        for file_path in all_files:
            try:
                scanned = self._process_file(file_path)
                if scanned:
                    if keyword_filter:
                        if self._matches_keyword_filter(scanned.content, keyword_filter):
                            result.scanned_files.append(scanned)
                            result.total_size_bytes += scanned.size_bytes
                    else:
                        result.scanned_files.append(scanned)
                        result.total_size_bytes += scanned.size_bytes
                    result.total_files_scanned += 1
            except Exception as e:
                result.failed_files.append({"file_path": str(file_path), "error": str(e)})
                result.total_files_failed += 1
                logger.warning(f"Failed to process file {file_path}: {e}")

        logger.info(
            f"Scan complete. Scanned: {result.total_files_scanned}, "
            f"Failed: {result.total_files_failed}"
        )
        return result

    def _walk_directory(
        self, directory: str, extensions: set, exclude_dirs: set
    ) -> Generator[Path, None, None]:
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
            for file_name in files:
                file_path = Path(root) / file_name
                ext = file_path.suffix.lower()
                if ext in self.exclude_extensions:
                    continue
                if extensions and ext not in extensions:
                    continue
                try:
                    if file_path.stat().st_size > self.max_file_size:
                        logger.warning(f"Skipping large file: {file_path}")
                        continue
                except OSError:
                    continue
                yield file_path

    def _process_file(self, file_path: Path) -> Optional[ScannedFile]:
        file_stat = file_path.stat()
        content, encoding = self._read_file_with_encoding(file_path)
        if content is None:
            return None
        return ScannedFile(
            file_path=str(file_path.absolute()),
            file_name=file_path.name,
            folder_path=str(file_path.parent.absolute()),
            extension=file_path.suffix.lower(),
            size_bytes=file_stat.st_size,
            content=content,
            encoding=encoding,
            line_count=content.count("\n") + 1,
        )

    def _read_file_with_encoding(self, file_path: Path):
        try:
            with open(file_path, "rb") as f:
                raw_data = f.read(min(32768, file_path.stat().st_size))
                detected = chardet.detect(raw_data)
                detected_encoding = detected.get("encoding", "utf-8")
        except Exception:
            detected_encoding = "utf-8"

        encodings_to_try = [detected_encoding] + self.encoding_fallbacks
        encodings_to_try = list(dict.fromkeys(e for e in encodings_to_try if e))

        for encoding in encodings_to_try:
            try:
                with open(file_path, "r", encoding=encoding, errors="strict") as f:
                    content = f.read()
                return content, encoding
            except (UnicodeDecodeError, LookupError):
                continue

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return content, "utf-8"
        except Exception as e:
            logger.error(f"Cannot read file {file_path}: {e}")
            return None, None

    @staticmethod
    def _matches_keyword_filter(content: str, keywords: List[str]) -> bool:
        content_lower = content.lower()
        return any(kw.lower() in content_lower for kw in keywords)

    def scan_multiple_directories(
        self,
        directories: List[str],
        extensions: Optional[List[str]] = None,
        keyword_filter: Optional[List[str]] = None,
    ) -> ScanResult:
        merged_result = ScanResult()
        for directory in directories:
            result = self.scan_directory(directory, extensions, keyword_filter)
            merged_result.scanned_files.extend(result.scanned_files)
            merged_result.failed_files.extend(result.failed_files)
            merged_result.total_files_found += result.total_files_found
            merged_result.total_files_scanned += result.total_files_scanned
            merged_result.total_files_failed += result.total_files_failed
            merged_result.total_size_bytes += result.total_size_bytes
        return merged_result
