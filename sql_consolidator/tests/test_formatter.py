"""Unit tests for SQL Formatter module."""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from formatter.sql_formatter import SQLFormatter
from sql_parser.sql_parser import SQLParser, ExtractedQuery, QueryType


@pytest.fixture
def config():
    return {"formatter": {"keyword_case":"upper","indent_width":4,"reindent":True,"strip_comments":False}}

@pytest.fixture
def formatter(config):
    return SQLFormatter(config)

def make_q(sql, qtype=QueryType.SELECT):
    p = SQLParser({"parser": {}})
    n = p._normalize_sql(sql)
    fp = p._generate_fingerprint(n)
    q = ExtractedQuery(raw_sql=sql, normalized_sql=n, query_type=qtype,
                       source_file="/test/sample.sql", source_folder="/test",
                       line_number_start=1, line_number_end=5, fingerprint=fp,
                       complexity_score=3, importance_score=7, risk_level="LOW",
                       table_names=["users"])
    return q

class TestFormatter:
    def test_format_returns_content(self, formatter):
        q = make_q("select * from users where active=1")
        assert len(formatter.format_query(q)) > 0

    def test_ends_with_semicolon(self, formatter):
        q = make_q("SELECT * FROM users")
        assert formatter.format_query(q).rstrip().endswith(";")

    def test_metadata_comment(self, formatter):
        q = make_q("SELECT id FROM users")
        result = formatter._add_metadata_comment(q, "SELECT id FROM users;")
        assert "Source File" in result and "Risk Level" in result

    def test_select_category(self, formatter):
        assert "SELECT" in formatter._get_category_name(QueryType.SELECT)

    def test_ddl_category(self, formatter):
        assert "CREATE" in formatter._get_category_name(QueryType.CREATE) or "DDL" in formatter._get_category_name(QueryType.CREATE)

    def test_groups_by_type(self, formatter):
        queries = [make_q("SELECT * FROM users"), make_q("INSERT INTO t VALUES (1)", QueryType.INSERT), make_q("SELECT id FROM orders")]
        cat = formatter.format_all_queries(queries)
        assert isinstance(cat, dict) and len(cat) >= 1

    def test_master_doc_header(self, formatter):
        queries = [make_q("SELECT * FROM users")]
        meta = {"scan_datetime":"2024-01-01 00:00:00","input_directory":"/test",
                "total_files_scanned":1,"total_files_failed":0,
                "total_queries_found":1,"total_unique_queries":1,
                "total_duplicates_removed":0,"query_type_distribution":{"SELECT":1}}
        doc = formatter.generate_master_sql_document(queries, meta)
        assert "SQL QUERY CONSOLIDATION MASTER DOCUMENT" in doc
