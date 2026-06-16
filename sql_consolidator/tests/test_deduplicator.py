"""Unit tests for Deduplicator module."""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from deduplicator.deduplicator import QueryDeduplicator
from sql_parser.sql_parser import SQLParser, ExtractedQuery, QueryType


@pytest.fixture
def config():
    return {"deduplicator": {"similarity_threshold": 0.95,
                              "normalize_whitespace": True, "normalize_case": True}}

@pytest.fixture
def deduplicator(config):
    return QueryDeduplicator(config)

def make_query(sql, source="test.sql", qtype=QueryType.SELECT):
    p = SQLParser({"parser": {}})
    n = p._normalize_sql(sql)
    fp = p._generate_fingerprint(n)
    return ExtractedQuery(raw_sql=sql, normalized_sql=n, query_type=qtype,
                          source_file=source, source_folder="/t",
                          line_number_start=1, line_number_end=1, fingerprint=fp)

class TestExact:
    def test_removes_exact_dup(self, deduplicator):
        q1, q2 = make_query("SELECT * FROM users"), make_query("SELECT * FROM users")
        u, g = deduplicator._exact_deduplication([q1, q2])
        assert len(u) == 1 and len(g) == 1

    def test_keeps_different(self, deduplicator):
        q1, q2 = make_query("SELECT * FROM users"), make_query("SELECT * FROM orders")
        u, g = deduplicator._exact_deduplication([q1, q2])
        assert len(u) == 2 and len(g) == 0

    def test_triple_dup(self, deduplicator):
        q1 = make_query("SELECT id FROM users")
        u, _ = deduplicator._exact_deduplication([q1, make_query("SELECT id FROM users"), make_query("SELECT id FROM users")])
        assert len(u) == 1

class TestNormalized:
    def test_case_insensitive(self, deduplicator):
        r = deduplicator.deduplicate([make_query("SELECT * FROM users"), make_query("select * from users")])
        assert r.total_unique == 1

    def test_whitespace_insensitive(self, deduplicator):
        r = deduplicator.deduplicate([make_query("SELECT * FROM users"), make_query("SELECT   *   FROM   users")])
        assert r.total_unique == 1

    def test_different_not_deduped(self, deduplicator):
        r = deduplicator.deduplicate([make_query("SELECT id FROM users WHERE active=1"), make_query("SELECT name FROM customers")])
        assert r.total_unique == 2

class TestStats:
    def test_statistics(self, deduplicator):
        queries = [make_query("SELECT * FROM users")] * 5 + [make_query("SELECT * FROM orders"), make_query("SELECT * FROM products")]
        r = deduplicator.deduplicate(queries)
        assert r.total_input == 7 and r.total_unique == 3 and r.total_duplicates == 4

    def test_empty_input(self, deduplicator):
        r = deduplicator.deduplicate([])
        assert r.total_input == 0 and r.total_unique == 0

    def test_single_query(self, deduplicator):
        r = deduplicator.deduplicate([make_query("SELECT * FROM users")])
        assert r.total_unique == 1 and r.total_duplicates == 0

    def test_report_content(self, deduplicator):
        r = deduplicator.deduplicate([make_query("SELECT * FROM users"), make_query("SELECT * FROM users"), make_query("INSERT INTO t VALUES (1)")])
        report = deduplicator.generate_dedup_report(r)
        assert "DEDUPLICATION REPORT" in report
