"""
Query Analyzer Module
Analyzes SQL queries for risk detection, complexity, and insights.
"""

import re
import logging
from typing import List, Dict, Tuple
from collections import Counter
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AnalysisReport:
    total_queries: int = 0
    risk_summary: Dict[str, int] = field(default_factory=dict)
    high_risk_queries: List = field(default_factory=list)
    complex_queries: List = field(default_factory=list)
    most_common_tables: List[Tuple[str, int]] = field(default_factory=list)
    query_type_distribution: Dict[str, int] = field(default_factory=dict)
    average_complexity: float = 0.0
    natural_language_summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    top_important_queries: List = field(default_factory=list)


class QueryAnalyzer:
    def __init__(self, config: Dict):
        self.config = config
        self.analyzer_config = config.get("analyzer", {})

    def analyze(self, queries: List) -> AnalysisReport:
        report = AnalysisReport()
        report.total_queries = len(queries)
        if not queries:
            return report

        logger.info(f"Analyzing {len(queries)} queries")
        report.query_type_distribution = dict(
            Counter(q.query_type.value for q in queries).most_common()
        )
        report.risk_summary = dict(Counter(q.risk_level for q in queries))
        report.high_risk_queries = sorted(
            [q for q in queries if q.risk_level in ("HIGH", "CRITICAL")],
            key=lambda q: 0 if q.risk_level == "CRITICAL" else 1
        )
        report.complex_queries = sorted(
            queries, key=lambda q: q.complexity_score, reverse=True
        )[:20]
        report.average_complexity = sum(q.complexity_score for q in queries) / len(queries)
        report.top_important_queries = sorted(
            queries, key=lambda q: q.importance_score, reverse=True
        )[:50]
        all_tables = []
        for q in queries:
            all_tables.extend(q.table_names)
        report.most_common_tables = Counter(
            t.lower() for t in all_tables if t
        ).most_common(20)
        report.recommendations = self._generate_recommendations(queries, report)
        report.natural_language_summary = self._generate_nl_summary(report)
        logger.info("Analysis complete")
        return report

    def _generate_recommendations(self, queries: List, report: AnalysisReport) -> List[str]:
        recs = []
        critical = report.risk_summary.get("CRITICAL", 0)
        if critical > 0:
            recs.append(
                f"CRITICAL: {critical} DELETE/UPDATE queries found WITHOUT WHERE clause. "
                f"Review immediately to prevent mass data loss."
            )
        high = report.risk_summary.get("HIGH", 0)
        if high > 0:
            recs.append(
                f"HIGH RISK: {high} DROP/TRUNCATE queries found. "
                f"Ensure these are intentional and have backups."
            )
        complex_q = [q for q in queries if q.complexity_score > 20]
        if complex_q:
            recs.append(
                f"{len(complex_q)} highly complex queries detected (score > 20). "
                f"Consider optimization review."
            )
        from sql_parser.sql_parser import QueryType
        risky_dml = [
            q for q in queries
            if q.query_type in (QueryType.UPDATE, QueryType.DELETE)
            and not q.has_where_clause
        ]
        if risky_dml:
            recs.append(
                f"{len(risky_dml)} UPDATE/DELETE queries lack WHERE clauses - "
                f"potential full table modifications!"
            )
        if report.most_common_tables:
            top = report.most_common_tables[0]
            recs.append(
                f"Most referenced table: '{top[0]}' appears in {top[1]} queries. "
                f"Ensure proper indexing."
            )
        ddl_count = sum(
            report.query_type_distribution.get(t, 0) for t in ["CREATE", "ALTER", "DROP"]
        )
        if ddl_count > 0:
            recs.append(
                f"{ddl_count} DDL statements found. Ensure schema changes are "
                f"version-controlled."
            )
        return recs

    def _generate_nl_summary(self, report: AnalysisReport) -> str:
        lines = [
            "NATURAL LANGUAGE SUMMARY", "=" * 60,
            f"This consolidated document contains {report.total_queries} unique SQL queries.",
            "",
        ]
        if report.query_type_distribution:
            lines.append("Query Breakdown:")
            for qtype, count in report.query_type_distribution.items():
                lines.append(f"  * {count} {qtype} queries")
            lines.append("")
        critical = report.risk_summary.get("CRITICAL", 0)
        high = report.risk_summary.get("HIGH", 0)
        medium = report.risk_summary.get("MEDIUM", 0)
        low = report.risk_summary.get("LOW", 0)
        lines += [
            "Risk Profile:",
            f"  * {critical} CRITICAL risk (DELETE/UPDATE without WHERE)",
            f"  * {high} HIGH risk (DROP/TRUNCATE)",
            f"  * {medium} MEDIUM risk (DML with WHERE)",
            f"  * {low} LOW risk (SELECT/DDL)",
            "",
            f"Average complexity score: {report.average_complexity:.1f}",
            "",
        ]
        if report.most_common_tables:
            lines.append("Top Referenced Tables:")
            for table, count in report.most_common_tables[:5]:
                lines.append(f"  * {table}: referenced {count} times")
            lines.append("")
        if report.recommendations:
            lines.append("Key Recommendations:")
            for rec in report.recommendations:
                lines.append(f"  {rec}")
        return "\n".join(lines)
