"""
Deduplicator Module
Identifies and removes duplicate SQL queries using multiple strategies.
"""

import re
import logging
import hashlib
from typing import List, Dict, Tuple
from dataclasses import dataclass, field
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


@dataclass
class DeduplicationResult:
    unique_queries: List = field(default_factory=list)
    duplicate_groups: List[Dict] = field(default_factory=list)
    total_input: int = 0
    total_unique: int = 0
    total_duplicates: int = 0
    exact_duplicates: int = 0
    semantic_duplicates: int = 0


class QueryDeduplicator:
    def __init__(self, config: Dict):
        self.config = config
        self.dedup_config = config.get("deduplicator", {})
        self.similarity_threshold = self.dedup_config.get("similarity_threshold", 0.95)

    def deduplicate(self, queries: List) -> DeduplicationResult:
        result = DeduplicationResult()
        result.total_input = len(queries)
        if not queries:
            return result

        logger.info(f"Starting deduplication of {len(queries)} queries")

        after_exact, exact_groups = self._exact_deduplication(queries)
        result.exact_duplicates = result.total_input - len(after_exact)
        result.duplicate_groups.extend(exact_groups)

        after_norm, norm_groups = self._normalized_deduplication(after_exact)
        result.exact_duplicates += len(after_exact) - len(after_norm)
        result.duplicate_groups.extend(norm_groups)

        if len(after_norm) <= 5000:
            after_sem, sem_groups = self._semantic_deduplication(after_norm)
            result.semantic_duplicates = len(after_norm) - len(after_sem)
            result.duplicate_groups.extend(sem_groups)
            result.unique_queries = after_sem
        else:
            result.unique_queries = after_norm

        result.total_unique = len(result.unique_queries)
        result.total_duplicates = result.total_input - result.total_unique
        logger.info(
            f"Deduplication complete. {result.total_unique} unique "
            f"from {result.total_input} ({result.total_duplicates} removed)"
        )
        return result

    def _exact_deduplication(self, queries: List) -> Tuple[List, List[Dict]]:
        seen: Dict[str, object] = {}
        unique: List = []
        groups: List[Dict] = []
        for query in queries:
            fp = query.fingerprint
            if fp in seen:
                query.is_duplicate = True
                query.duplicate_of = seen[fp].source_file
                existing = next((g for g in groups if g["fingerprint"] == fp), None)
                if existing:
                    existing["duplicates"].append({
                        "file": query.source_file,
                        "line": query.line_number_start,
                        "type": "EXACT"
                    })
                else:
                    groups.append({
                        "fingerprint": fp,
                        "original": seen[fp].source_file,
                        "original_line": seen[fp].line_number_start,
                        "duplicates": [{"file": query.source_file,
                                        "line": query.line_number_start,
                                        "type": "EXACT"}],
                        "duplicate_type": "EXACT",
                        "query_preview": query.raw_sql[:100]
                    })
            else:
                seen[fp] = query
                unique.append(query)
        return unique, groups

    def _normalized_deduplication(self, queries: List) -> Tuple[List, List[Dict]]:
        seen: Dict[str, object] = {}
        unique: List = []
        groups: List[Dict] = []
        for query in queries:
            key = self._get_normalized_key(query.raw_sql)
            norm_fp = hashlib.sha256(key.encode()).hexdigest()
            if norm_fp in seen:
                query.is_duplicate = True
                query.duplicate_of = seen[norm_fp].source_file
                groups.append({
                    "fingerprint": norm_fp,
                    "original": seen[norm_fp].source_file,
                    "original_line": seen[norm_fp].line_number_start,
                    "duplicates": [{"file": query.source_file,
                                    "line": query.line_number_start,
                                    "type": "NORMALIZED"}],
                    "duplicate_type": "FORMATTING",
                    "query_preview": query.raw_sql[:100]
                })
            else:
                seen[norm_fp] = query
                unique.append(query)
        return unique, groups

    def _semantic_deduplication(self, queries: List) -> Tuple[List, List[Dict]]:
        type_groups: Dict[str, List] = {}
        for query in queries:
            k = query.query_type.value
            type_groups.setdefault(k, []).append(query)
        all_unique: List = []
        all_groups: List[Dict] = []
        for _, grp in type_groups.items():
            u, g = self._semantic_dedup_group(grp)
            all_unique.extend(u)
            all_groups.extend(g)
        return all_unique, all_groups

    def _semantic_dedup_group(self, queries: List) -> Tuple[List, List[Dict]]:
        unique: List = []
        groups: List[Dict] = []
        token_cache = [self._tokenize_query(q.raw_sql) for q in queries]
        for i, query in enumerate(queries):
            is_dup = False
            for j, uq in enumerate(unique):
                sim = self._calculate_similarity(
                    token_cache[i], self._tokenize_query(uq.raw_sql)
                )
                if sim >= self.similarity_threshold:
                    query.is_duplicate = True
                    query.duplicate_of = uq.source_file
                    is_dup = True
                    groups.append({
                        "fingerprint": f"sem_{i}_{j}",
                        "original": uq.source_file,
                        "original_line": uq.line_number_start,
                        "duplicates": [{"file": query.source_file,
                                        "line": query.line_number_start,
                                        "type": "SEMANTIC",
                                        "similarity": f"{sim:.2%}"}],
                        "duplicate_type": "SEMANTIC",
                        "query_preview": query.raw_sql[:100]
                    })
                    break
            if not is_dup:
                unique.append(query)
        return unique, groups

    def _get_normalized_key(self, sql: str) -> str:
        sql = re.sub(r"--[^\n]*", " ", sql)
        sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
        sql = sql.upper()
        sql = re.sub(r"\s+", " ", sql).strip().rstrip(";").strip()
        sql = re.sub(r"'[^']*'", "'?'", sql)
        sql = re.sub(r"\b\d+\b", "?", sql)
        return sql

    def _tokenize_query(self, sql: str) -> List[str]:
        return re.findall(r"\b\w+\b", self._get_normalized_key(sql))

    def _calculate_similarity(self, t1: List[str], t2: List[str]) -> float:
        if not t1 or not t2:
            return 0.0
        if min(len(t1), len(t2)) / max(len(t1), len(t2)) < 0.5:
            return 0.0
        return SequenceMatcher(None, " ".join(t1), " ".join(t2)).ratio()

    def generate_dedup_report(self, result: DeduplicationResult) -> str:
        lines = [
            "=" * 80,
            "DEDUPLICATION REPORT",
            "=" * 80,
            f"Total queries processed : {result.total_input}",
            f"Unique queries retained : {result.total_unique}",
            f"Total duplicates removed: {result.total_duplicates}",
            f"  - Exact duplicates    : {result.exact_duplicates}",
            f"  - Semantic duplicates : {result.semantic_duplicates}",
            f"Deduplication rate      : "
            f"{(result.total_duplicates / max(result.total_input, 1)) * 100:.1f}%",
            "", "DUPLICATE GROUPS:", "-" * 80,
        ]
        for i, group in enumerate(result.duplicate_groups[:50], 1):
            lines.append(f"\nGroup #{i} ({group['duplicate_type']})")
            lines.append(f"  Original : {group['original']} (Line {group['original_line']})")
            lines.append(f"  Preview  : {group['query_preview'][:80]}")
            for dup in group.get("duplicates", []):
                lines.append(
                    f"  Duplicate: {dup['file']} (Line {dup['line']}) [{dup['type']}]"
                )
        return "\n".join(lines)
