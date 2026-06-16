"""
SQL Query Consolidation and Deduplication Tool
Main entry point for command-line execution.
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, BarColumn
from rich.panel import Panel
from rich.table import Table

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scanner.file_scanner import FileScanner
from sql_parser.sql_parser import SQLParser, ExtractedQuery
from deduplicator.deduplicator import QueryDeduplicator, DeduplicationResult
from analyzer.query_analyzer import QueryAnalyzer
from reports.report_generator import ReportGenerator

console = Console()


def setup_logging(config: Dict) -> logging.Logger:
    log_config = config.get("logging", {})
    log_level = getattr(logging, log_config.get("level", "INFO"))
    log_file = log_config.get("log_file", "logs/sql_consolidator.log")
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    handlers = [logging.StreamHandler()]
    if log_config.get("log_to_file", True):
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )
    return logging.getLogger("sql_consolidator")


def load_config(config_path: str = "config/config.yaml") -> Dict:
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    logging.warning(f"Config not found: {config_path}. Using defaults.")
    return {}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SQL Query Consolidation and Deduplication Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py -i ./input -o ./output\n"
            "  python main.py -i ./input -o ./output -e .sql .txt\n"
            "  python main.py -i ./input -o ./output -k production\n"
            "  python main.py -i ./input -o ./output --no-dedup\n"
        ),
    )
    parser.add_argument("-i", "--input", required=True, help="Input directory path")
    parser.add_argument("-o", "--output", required=True, help="Output directory path")
    parser.add_argument("-e", "--extensions", nargs="+", default=None)
    parser.add_argument("-k", "--keywords", nargs="+", default=None)
    parser.add_argument("--exclude-dirs", nargs="+", default=None)
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--no-dedup", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--min-complexity", type=int, default=0)
    parser.add_argument("--min-importance", type=int, default=0)
    return parser.parse_args()


def run_consolidation(
    input_dir: str,
    output_dir: str,
    config: Dict,
    extensions: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None,
    skip_dedup: bool = False,
    min_complexity: int = 0,
    min_importance: int = 0,
) -> Dict:
    logger = logging.getLogger("sql_consolidator.pipeline")
    start_time = datetime.now()

    with Progress(
        SpinnerColumn(),
        "[progress.description]{task.description}",
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:

        # Step 1: Scan
        t1 = progress.add_task("[cyan]Scanning files...", total=None)
        scanner = FileScanner(config)
        scan_result = scanner.scan_directory(
            directory=input_dir,
            extensions=extensions,
            keyword_filter=keywords,
            exclude_dirs=exclude_dirs,
        )
        progress.update(t1, completed=True, description="[green]Files scanned")

        if scan_result.total_files_scanned == 0:
            console.print("[red]No files found. Check input directory.[/red]")
            return {}

        # Step 2: Parse
        t2 = progress.add_task(
            f"[cyan]Parsing {scan_result.total_files_scanned} files...",
            total=scan_result.total_files_scanned
        )
        parser = SQLParser(config)
        all_queries: List[ExtractedQuery] = []
        for sf in scan_result.scanned_files:
            extracted = parser.parse_file_content(sf.content, sf.file_path, sf.folder_path)
            all_queries.extend(extracted)
            progress.advance(t2)
        progress.update(t2, description=f"[green]{len(all_queries)} queries extracted")

        if min_complexity > 0 or min_importance > 0:
            orig = len(all_queries)
            all_queries = [
                q for q in all_queries
                if q.complexity_score >= min_complexity and q.importance_score >= min_importance
            ]
            logger.info(f"Filtered to {len(all_queries)} (removed {orig - len(all_queries)})")

        # Step 3: Dedup
        dedup_result = DeduplicationResult()
        if not skip_dedup:
            t3 = progress.add_task("[cyan]Deduplicating...", total=None)
            dedup_result = QueryDeduplicator(config).deduplicate(all_queries)
            unique_queries = dedup_result.unique_queries
            progress.update(t3, completed=True,
                            description=f"[green]{dedup_result.total_unique} unique")
        else:
            unique_queries = all_queries
            dedup_result.unique_queries = all_queries
            dedup_result.total_input = len(all_queries)
            dedup_result.total_unique = len(all_queries)

        # Step 4: Analyze
        t4 = progress.add_task("[cyan]Analyzing queries...", total=None)
        analysis_report = QueryAnalyzer(config).analyze(unique_queries)
        progress.update(t4, completed=True, description="[green]Analysis complete")

        # Step 5: Reports
        t5 = progress.add_task("[cyan]Generating reports...", total=None)
        scan_metadata = {
            "scan_datetime": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "input_directory": input_dir,
            "total_files_found": scan_result.total_files_found,
            "total_files_scanned": scan_result.total_files_scanned,
            "total_files_failed": scan_result.total_files_failed,
            "total_size_bytes": scan_result.total_size_bytes,
            "total_queries_found": len(all_queries),
            "total_unique_queries": dedup_result.total_unique,
            "total_duplicates_removed": dedup_result.total_duplicates,
            "total_errors": scan_result.total_files_failed,
            "failed_files": scan_result.failed_files,
            "query_type_distribution": analysis_report.query_type_distribution,
        }
        output_files = ReportGenerator(config, output_dir).generate_all_reports(
            queries=unique_queries,
            dedup_result=dedup_result,
            analysis_report=analysis_report,
            scan_metadata=scan_metadata,
        )
        progress.update(t5, completed=True, description="[green]Reports generated")

    elapsed = (datetime.now() - start_time).total_seconds()
    console.print(f"\n[bold green]Complete in {elapsed:.1f} seconds[/bold green]")

    return {
        "scan_result": scan_result,
        "all_queries": all_queries,
        "unique_queries": unique_queries,
        "dedup_result": dedup_result,
        "analysis_report": analysis_report,
        "output_files": output_files,
        "elapsed_seconds": elapsed,
    }


def main():
    console.print(Panel(
        "  SQL QUERY CONSOLIDATION AND DEDUPLICATION TOOL\n  Professional Edition v1.0",
        style="bold blue"
    ))
    args = parse_arguments()
    config = load_config(args.config)
    logger = setup_logging(config)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    console.print(f"[bold]Input :[/bold] {args.input}")
    console.print(f"[bold]Output:[/bold] {args.output}")

    try:
        results = run_consolidation(
            input_dir=args.input,
            output_dir=args.output,
            config=config,
            extensions=args.extensions,
            keywords=args.keywords,
            exclude_dirs=args.exclude_dirs,
            skip_dedup=args.no_dedup,
            min_complexity=args.min_complexity,
            min_importance=args.min_importance,
        )
        if results:
            tbl = Table(title="Final Summary", header_style="bold green")
            tbl.add_column("Metric", style="cyan", width=35)
            tbl.add_column("Value", style="yellow", width=20)
            d = results["dedup_result"]
            a = results["analysis_report"]
            tbl.add_row("Total Queries Found", str(d.total_input))
            tbl.add_row("Unique Queries", str(d.total_unique))
            tbl.add_row("Duplicates Removed", str(d.total_duplicates))
            tbl.add_row(
                "Deduplication Rate",
                f"{(d.total_duplicates / max(d.total_input, 1)) * 100:.1f}%"
            )
            tbl.add_row("Avg Complexity", f"{a.average_complexity:.1f}")
            tbl.add_row("Critical Risk", str(a.risk_summary.get("CRITICAL", 0)))
            tbl.add_row("High Risk", str(a.risk_summary.get("HIGH", 0)))
            console.print(tbl)

            ftbl = Table(title="Generated Files", header_style="bold blue")
            ftbl.add_column("Report Type", style="cyan", width=25)
            ftbl.add_column("File Path", style="green", width=60)
            for rtype, fpath in results["output_files"].items():
                ftbl.add_row(rtype.replace("_", " ").title(), fpath)
            console.print(ftbl)

            if a.recommendations:
                console.print("\n[bold yellow]Key Recommendations:[/bold yellow]")
                for rec in a.recommendations:
                    console.print(f"  {rec}")

    except KeyboardInterrupt:
        console.print("\n[red]Interrupted.[/red]")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
