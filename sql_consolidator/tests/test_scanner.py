"""Unit tests for File Scanner module."""
import os, pytest, tempfile
from pathlib import Path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scanner.file_scanner import FileScanner


@pytest.fixture
def config():
    return {"scanner": {"default_extensions": [".sql",".txt"],
                         "exclude_extensions": [".exe"],
                         "max_file_size_mb": 10,
                         "encoding_fallbacks": ["utf-8","latin-1"]}}

@pytest.fixture
def scanner(config):
    return FileScanner(config)

@pytest.fixture
def tmpdir_with_files():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "test.sql").write_text("SELECT * FROM users;\nINSERT INTO logs VALUES (1);", encoding="utf-8")
        (Path(d) / "queries.txt").write_text("Some text\nSELECT id FROM orders;", encoding="utf-8")
        sub = Path(d) / "subdir"
        sub.mkdir()
        (sub / "nested.sql").write_text("UPDATE users SET active=1 WHERE id=5;", encoding="utf-8")
        yield d

class TestScanner:
    def test_finds_files(self, scanner, tmpdir_with_files):
        r = scanner.scan_directory(tmpdir_with_files)
        assert r.total_files_scanned > 0

    def test_recursive(self, scanner, tmpdir_with_files):
        r = scanner.scan_directory(tmpdir_with_files)
        assert "nested.sql" in [f.file_name for f in r.scanned_files]

    def test_extension_filter(self, scanner, tmpdir_with_files):
        r = scanner.scan_directory(tmpdir_with_files, extensions=[".sql"])
        assert all(f.extension == ".sql" for f in r.scanned_files)

    def test_nonexistent(self, scanner):
        r = scanner.scan_directory("/nonexistent/path/xyz")
        assert r.total_files_scanned == 0

    def test_content_read(self, scanner, tmpdir_with_files):
        r = scanner.scan_directory(tmpdir_with_files, extensions=[".sql"])
        assert all(len(f.content) > 0 for f in r.scanned_files)

    def test_keyword_filter(self, scanner, tmpdir_with_files):
        r = scanner.scan_directory(tmpdir_with_files, keyword_filter=["UPDATE"])
        for f in r.scanned_files:
            assert "UPDATE" in f.content.upper()

    def test_metadata_populated(self, scanner, tmpdir_with_files):
        r = scanner.scan_directory(tmpdir_with_files, extensions=[".sql"])
        for f in r.scanned_files:
            assert f.file_name and f.folder_path and f.size_bytes > 0

    def test_statistics(self, scanner, tmpdir_with_files):
        r = scanner.scan_directory(tmpdir_with_files)
        assert r.total_files_found >= r.total_files_scanned
