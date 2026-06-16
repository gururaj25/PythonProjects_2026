"""Unit tests for SQL Parser module."""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sql_parser.sql_parser import SQLParser, QueryType, ExtractedQuery


@pytest.fixture
def config():
    return {"parser": {"min_query_length": 10, "max_query_length": 500000,
                        "supported_query_types": ["SELECT","INSERT","UPDATE",
                        "DELETE","CREATE","ALTER","DROP","TRUNCATE","EXEC","WITH"],
                        "test_keywords": ["test_table","tmp_test"]}}

@pytest.fixture
def parser(config):
    return SQLParser(config)

def make_q(sql, qtype=None, p=None):
    p = p or SQLParser({"parser": {}})
    n = p._normalize_sql(sql)
    fp = p._generate_fingerprint(n)
    qt = qtype or p._classify_query_type(sql)
    return ExtractedQuery(raw_sql=sql, normalized_sql=n, query_type=qt,
                          source_file="t.sql", source_folder="/t",
                          line_number_start=1, line_number_end=1, fingerprint=fp)

class TestClassification:
    def test_select(self, parser): assert parser._classify_query_type("SELECT * FROM users") == QueryType.SELECT
    def test_insert(self, parser): assert parser._classify_query_type("INSERT INTO users (name) VALUES ('x')") == QueryType.INSERT
    def test_update(self, parser): assert parser._classify_query_type("UPDATE users SET name='x' WHERE id=1") == QueryType.UPDATE
    def test_delete(self, parser): assert parser._classify_query_type("DELETE FROM users WHERE id=1") == QueryType.DELETE
    def test_create(self, parser): assert parser._classify_query_type("CREATE TABLE t (id INT)") == QueryType.CREATE
    def test_procedure(self, parser): assert parser._classify_query_type("CREATE PROCEDURE p AS SELECT 1") == QueryType.STORED_PROCEDURE
    def test_view(self, parser): assert parser._classify_query_type("CREATE VIEW v AS SELECT 1") == QueryType.VIEW
    def test_alter(self, parser): assert parser._classify_query_type("ALTER TABLE t ADD col INT") == QueryType.ALTER
    def test_drop(self, parser): assert parser._classify_query_type("DROP TABLE t") == QueryType.DROP
    def test_cte(self, parser): assert parser._classify_query_type("WITH cte AS (SELECT 1) SELECT * FROM cte") == QueryType.WITH
    def test_exec(self, parser): assert parser._classify_query_type("EXEC sp_test") == QueryType.EXEC
    def test_unknown(self, parser): assert parser._classify_query_type("GARBAGE TEXT") == QueryType.UNKNOWN

class TestValidation:
    def test_valid(self, parser):
        q = make_q("SELECT id FROM users WHERE active=1", p=parser)
        assert parser._is_valid_query(q) is True
    def test_empty(self, parser):
        q = make_q("SELECT * FROM users", p=parser)
        q.raw_sql = ""
        assert parser._is_valid_query(q) is False
    def test_comment_only(self, parser):
        assert parser._is_pure_comment("-- comment") is True
        assert parser._is_pure_comment("SELECT * FROM t") is False

class TestNormalization:
    def test_whitespace(self, parser):
        assert parser._normalize_sql("SELECT   *   FROM   t") == parser._normalize_sql("SELECT * FROM t")
    def test_case(self, parser):
        assert parser._normalize_sql("select * from t") == parser._normalize_sql("SELECT * FROM T")
    def test_semicolon(self, parser):
        assert parser._normalize_sql("SELECT * FROM t;") == parser._normalize_sql("SELECT * FROM t")

class TestMetadata:
    def test_joins(self, parser):
        q = make_q("SELECT u.id FROM users u INNER JOIN orders o ON u.id=o.uid", QueryType.SELECT, parser)
        parser._enrich_query_metadata(q)
        assert q.has_joins is True
    def test_subquery(self, parser):
        q = make_q("SELECT * FROM users WHERE id IN (SELECT uid FROM orders)", QueryType.SELECT, parser)
        parser._enrich_query_metadata(q)
        assert q.has_subquery is True
    def test_critical_risk(self, parser):
        q = make_q("DELETE FROM users", QueryType.DELETE, parser)
        q.has_where_clause = False
        assert parser._assess_risk_level(q) == "CRITICAL"
    def test_medium_risk(self, parser):
        q = make_q("UPDATE users SET x=1 WHERE id=1", QueryType.UPDATE, parser)
        q.has_where_clause = True
        assert parser._assess_risk_level(q) == "MEDIUM"
