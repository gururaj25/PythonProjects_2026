"""
SQL Parser Module
Extracts, classifies, and validates SQL queries from raw text content.
"""

import re
import logging
import hashlib
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import sqlparse

logger = logging.getLogger(__name__)


class QueryType(Enum):
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    MERGE = "MERGE"
    CREATE = "CREATE"
    ALTER = "ALTER"
    DROP = "DROP"
    TRUNCATE = "TRUNCATE"
    EXEC = "EXEC"
    WITH = "WITH"
    TRANSACTION = "TRANSACTION"
    STORED_PROCEDURE = "STORED_PROCEDURE"
    VIEW = "VIEW"
    FUNCTION = "FUNCTION"
    TRIGGER = "TRIGGER"
    INDEX = "INDEX"
    UNKNOWN = "UNKNOWN"


@dataclass
class ExtractedQuery:
    raw_sql: str
    normalized_sql: str
    query_type: QueryType
    source_file: str
    source_folder: str
    line_number_start: int
    line_number_end: int
    table_names: List[str] = field(default_factory=list)
    has_joins: bool = False
    has_subquery: bool = False
    has_cte: bool = False
    has_aggregation: bool = False
    has_where_clause: bool = False
    is_complete: bool = True
    complexity_score: int = 0
    importance_score: int = 0
    risk_level: str = "LOW"
    is_duplicate: bool = False
    duplicate_of: str = ""
    fingerprint: str = ""


class LineTracker:
    def __init__(self, content: str):
        self.lines = content.split("\n")

    def find_query_lines(self, query: str) -> Tuple[int, int]:
        first_line = query.split("\n")[0].strip()[:50]
        for i, line in enumerate(self.lines, 1):
            if first_line and first_line in line:
                line_count = query.count("\n") + 1
                return i, min(i + line_count - 1, len(self.lines))
        return 1, 1


class SQLParser:
    def __init__(self, config: Dict):
        self.config = config
        self.parser_config = config.get("parser", {})
        self.min_length = self.parser_config.get("min_query_length", 10)
        self.max_length = self.parser_config.get("max_query_length", 500000)
        self.test_keywords = self.parser_config.get("test_keywords", [])
        self.supported_types = self.parser_config.get(
            "supported_query_types",
            ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP"]
        )

    def parse_file_content(
        self, content: str, file_path: str, folder_path: str
    ) -> List[ExtractedQuery]:
        extracted_queries = []
        try:
            sqlparse_queries = self._extract_with_sqlparse(content, file_path, folder_path)
            extracted_queries.extend(sqlparse_queries)
            if not sqlparse_queries:
                regex_queries = self._extract_with_regex(content, file_path, folder_path)
                extracted_queries.extend(regex_queries)
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")

        valid_queries = []
        for query in extracted_queries:
            if self._is_valid_query(query):
                self._enrich_query_metadata(query)
                valid_queries.append(query)
        return valid_queries

    def _extract_with_sqlparse(
        self, content: str, file_path: str, folder_path: str
    ) -> List[ExtractedQuery]:
        queries = []
        line_tracker = LineTracker(content)
        try:
            statements = sqlparse.parse(content)
            for statement in statements:
                raw_sql = str(statement).strip()
                if not raw_sql or len(raw_sql) < self.min_length:
                    continue
                if self._is_comment_only(statement):
                    continue
                query_type = self._classify_query_type(raw_sql)
                if query_type == QueryType.UNKNOWN:
                    continue
                line_start, line_end = line_tracker.find_query_lines(raw_sql)
                queries.append(ExtractedQuery(
                    raw_sql=raw_sql,
                    normalized_sql=self._normalize_sql(raw_sql),
                    query_type=query_type,
                    source_file=file_path,
                    source_folder=folder_path,
                    line_number_start=line_start,
                    line_number_end=line_end,
                ))
        except Exception as e:
            logger.warning(f"sqlparse extraction failed for {file_path}: {e}")
        return queries

    def _extract_with_regex(
        self, content: str, file_path: str, folder_path: str
    ) -> List[ExtractedQuery]:
        queries = []
        lines = content.split("\n")
        current_query_lines = []
        query_start_line = 0
        in_query = False

        sql_starters = re.compile(
            r"^\s*(SELECT|INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|"
            r"TRUNCATE|EXEC|EXECUTE|WITH|BEGIN|DECLARE|CALL)\b",
            re.IGNORECASE,
        )

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if sql_starters.match(stripped) and not in_query:
                in_query = True
                query_start_line = line_num
                current_query_lines = [line]
            elif in_query:
                current_query_lines.append(line)
                if ";" in line or (
                    not stripped and len(current_query_lines) > 1
                    and any(ln.strip() for ln in current_query_lines[-3:])
                ):
                    raw_sql = "\n".join(current_query_lines).strip()
                    if len(raw_sql) >= self.min_length:
                        query_type = self._classify_query_type(raw_sql)
                        if query_type != QueryType.UNKNOWN:
                            queries.append(ExtractedQuery(
                                raw_sql=raw_sql,
                                normalized_sql=self._normalize_sql(raw_sql),
                                query_type=query_type,
                                source_file=file_path,
                                source_folder=folder_path,
                                line_number_start=query_start_line,
                                line_number_end=line_num,
                            ))
                    in_query = False
                    current_query_lines = []

        if in_query and current_query_lines:
            raw_sql = "\n".join(current_query_lines).strip()
            if len(raw_sql) >= self.min_length:
                query_type = self._classify_query_type(raw_sql)
                if query_type != QueryType.UNKNOWN:
                    queries.append(ExtractedQuery(
                        raw_sql=raw_sql,
                        normalized_sql=self._normalize_sql(raw_sql),
                        query_type=query_type,
                        source_file=file_path,
                        source_folder=folder_path,
                        line_number_start=query_start_line,
                        line_number_end=len(lines),
                    ))
        return queries

    def _classify_query_type(self, sql: str) -> QueryType:
        sql_upper = sql.upper().strip()
        sql_upper = re.sub(
            r"^(/\*.*?\*/\s*|--[^\n]*\n\s*)*", "", sql_upper, flags=re.DOTALL
        )
        type_patterns = [
            (r"^\s*CREATE\s+(OR\s+REPLACE\s+)?PROCEDURE\b", QueryType.STORED_PROCEDURE),
            (r"^\s*CREATE\s+(OR\s+REPLACE\s+)?FUNCTION\b", QueryType.FUNCTION),
            (r"^\s*CREATE\s+(OR\s+REPLACE\s+)?TRIGGER\b", QueryType.TRIGGER),
            (r"^\s*CREATE\s+(OR\s+REPLACE\s+)?VIEW\b", QueryType.VIEW),
            (r"^\s*CREATE\s+(OR\s+REPLACE\s+)?INDEX\b", QueryType.INDEX),
            (r"^\s*CREATE\b", QueryType.CREATE),
            (r"^\s*ALTER\b", QueryType.ALTER),
            (r"^\s*DROP\b", QueryType.DROP),
            (r"^\s*TRUNCATE\b", QueryType.TRUNCATE),
            (r"^\s*SELECT\b", QueryType.SELECT),
            (r"^\s*WITH\s+\w+.*\bAS\s*\(", QueryType.WITH),
            (r"^\s*INSERT\b", QueryType.INSERT),
            (r"^\s*UPDATE\b", QueryType.UPDATE),
            (r"^\s*DELETE\b", QueryType.DELETE),
            (r"^\s*MERGE\b", QueryType.MERGE),
            (r"^\s*EXEC(UTE)?\b", QueryType.EXEC),
            (r"^\s*(BEGIN|COMMIT|ROLLBACK)\b", QueryType.TRANSACTION),
            (r"^\s*DECLARE\s+@", QueryType.EXEC),
            (r"^\s*CALL\b", QueryType.EXEC),
        ]
        for pattern, query_type in type_patterns:
            if re.match(pattern, sql_upper):
                return query_type
        return QueryType.UNKNOWN

    def _is_valid_query(self, query: ExtractedQuery) -> bool:
        sql = query.raw_sql.strip()
        if len(sql) < self.min_length or len(sql) > self.max_length:
            return False
        if not sql.replace("\n", "").replace("\t", "").strip():
            return False
        if self._is_pure_comment(sql):
            return False
        if not self._has_minimum_sql_structure(sql):
            return False
        return True

    def _has_minimum_sql_structure(self, sql: str) -> bool:
        sql_upper = sql.upper().strip()
        keywords = [
            "SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER",
            "DROP", "TRUNCATE", "MERGE", "EXEC", "WITH", "BEGIN", "CALL"
        ]
        return any(sql_upper.startswith(kw) for kw in keywords)

    def _is_comment_only(self, statement) -> bool:
        try:
            for token in statement.tokens:
                if token.ttype not in (
                    sqlparse.tokens.Comment.Single,
                    sqlparse.tokens.Comment.Multiline,
                    sqlparse.tokens.Newline,
                    sqlparse.tokens.Whitespace,
                ):
                    return False
            return True
        except Exception:
            return False

    def _is_pure_comment(self, sql: str) -> bool:
        lines = sql.strip().split("\n")
        non_comment = [
            ln.strip() for ln in lines
            if ln.strip()
            and not ln.strip().startswith("--")
            and not ln.strip().startswith("/*")
            and not ln.strip().startswith("*")
            and not ln.strip().startswith("*/")
        ]
        return len(non_comment) == 0

    def _normalize_sql(self, sql: str) -> str:
        sql = re.sub(r"--[^\n]*", "", sql)
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
        sql = " ".join(sql.split()).upper().rstrip(";").strip()
        return sql

    def _enrich_query_metadata(self, query: ExtractedQuery) -> None:
        sql = query.raw_sql.upper()
        query.has_joins = bool(re.search(
            r"\b(INNER|LEFT|RIGHT|FULL|CROSS|OUTER)\s+JOIN\b|\bJOIN\b", sql
        ))
        query.has_subquery = bool(re.search(r"\(\s*SELECT\b", sql))
        query.has_cte = query.query_type == QueryType.WITH or bool(
            re.search(r"\bWITH\s+\w+\s+AS\s*\(", sql)
        )
        query.has_aggregation = bool(re.search(
            r"\b(COUNT|SUM|AVG|MAX|MIN|GROUP\s+BY|HAVING)\b", sql
        ))
        query.has_where_clause = bool(re.search(r"\bWHERE\b", sql))
        query.table_names = self._extract_table_names(query.raw_sql)
        query.fingerprint = self._generate_fingerprint(query.normalized_sql)
        query.complexity_score = self._calculate_complexity(query)
        query.risk_level = self._assess_risk_level(query)
        query.importance_score = self._calculate_importance(query)

    def _extract_table_names(self, sql: str) -> List[str]:
        table_names = []
        patterns = [
            r"\bFROM\s+([\w\.]+)",
            r"\bJOIN\s+([\w\.]+)",
            r"\bINTO\s+([\w\.]+)",
            r"\bUPDATE\s+([\w\.]+)",
            r"\bTABLE\s+([\w\.]+)",
        ]
        skip_words = {
            "SELECT", "SET", "WHERE", "GROUP", "ORDER", "HAVING",
            "ON", "AND", "OR", "NOT", "NULL", "AS", "IF", "EXISTS"
        }
        for pattern in patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            for match in matches:
                clean = re.sub(r"[`\[\]\"\']", "", match).strip()
                if clean and clean.upper() not in skip_words:
                    table_names.append(clean)
        return list(set(table_names))

    def _generate_fingerprint(self, normalized_sql: str) -> str:
        return hashlib.sha256(normalized_sql.encode("utf-8")).hexdigest()

    def _calculate_complexity(self, query: ExtractedQuery) -> int:
        score = 1
        sql = query.raw_sql.upper()
        score += len(re.findall(r"\bJOIN\b", sql)) * 3
        score += len(re.findall(r"\(\s*SELECT\b", sql)) * 4
        if query.has_cte:
            score += 3
        if query.has_aggregation:
            score += 2
        if re.search(r"\bOVER\s*\(", sql):
            score += 4
        score += len(re.findall(r"\bUNION\b", sql)) * 2
        if re.search(r"\bHAVING\b", sql):
            score += 2
        score += min(len(query.raw_sql) // 200, 10)
        return score

    def _assess_risk_level(self, query: ExtractedQuery) -> str:
        if query.query_type in (QueryType.DELETE, QueryType.UPDATE):
            if not query.has_where_clause:
                return "CRITICAL"
        if query.query_type == QueryType.DROP:
            return "HIGH"
        if query.query_type == QueryType.TRUNCATE:
            return "HIGH"
        if query.query_type in (QueryType.DELETE, QueryType.UPDATE):
            return "MEDIUM"
        if query.query_type == QueryType.INSERT:
            return "MEDIUM"
        return "LOW"

    def _calculate_importance(self, query: ExtractedQuery) -> int:
        score = 0
        type_scores = {
            QueryType.CREATE: 8, QueryType.ALTER: 7,
            QueryType.STORED_PROCEDURE: 9, QueryType.VIEW: 8,
            QueryType.FUNCTION: 8, QueryType.TRIGGER: 7,
            QueryType.SELECT: 5, QueryType.INSERT: 6,
            QueryType.UPDATE: 6, QueryType.DELETE: 6,
            QueryType.MERGE: 7, QueryType.WITH: 6,
        }
        score += type_scores.get(query.query_type, 3)
        score += min(query.complexity_score // 3, 10)
        if query.has_joins:
            score += 3
        if query.has_subquery:
            score += 4
        if query.has_cte:
            score += 3
        if query.has_aggregation:
            score += 2
        if query.has_where_clause:
            score += 1
        score += min(len(query.table_names), 5)
        return score
