# SQL Query Consolidation and Deduplication Tool

A professional Python application that scans multiple files containing SQL
queries and generates a single consolidated document with only clean,
unique, important queries.

## Quick Start

Step 1: Install dependencies
    pip install -r requirements.txt

Step 2: Run with sample data
    python main.py -i ./sample_input -o ./output --verbose
	
	python main.py -i D:\Gururaj\Learning\Python\ConsolidateSQLFilesinOne\TESTData\FCU -o D:\Gururaj\Learning\Python\ConsolidateSQLFilesinOne\TESTData\FCU_Output --verbose

Step 3: Launch GUI
    streamlit run ui/streamlit_app.py

Step 4: Windows users can run run.bat

## Command Line Options

    python main.py -i INPUT_DIR -o OUTPUT_DIR [OPTIONS]

    -i, --input        Input directory to scan (required)
    -o, --output       Output directory for reports (required)
    -e, --extensions   File extensions: .sql .txt .log
    -k, --keywords     Filter keywords: production critical
    --no-dedup         Skip deduplication
    --min-complexity   Minimum complexity score (0-50)
    --min-importance   Minimum importance score (0-30)
    --verbose          Show detailed output

## Output Files

    master_consolidated_TIMESTAMP.sql   Main SQL document
    summary_report_TIMESTAMP.txt        Statistics report
    sql_report_TIMESTAMP.docx           Word document
    sql_analysis_TIMESTAMP.xlsx         Excel workbook
    duplicate_report_TIMESTAMP.txt      Duplicate details
    error_log_TIMESTAMP.txt             Error log

## Project Structure

    sql_consolidator/
    |-- main.py
    |-- requirements.txt
    |-- run.bat
    |-- run.sh
    |-- config/config.yaml
    |-- scanner/file_scanner.py
    |-- parser/sql_parser.py
    |-- deduplicator/deduplicator.py
    |-- formatter/sql_formatter.py
    |-- analyzer/query_analyzer.py
    |-- reports/report_generator.py
    |-- ui/streamlit_app.py
    |-- tests/
    |-- sample_input/
    |-- logs/
    |-- output/

## Running Tests

    pytest tests/ -v
    pytest tests/ --cov=. --cov-report=html

## Requirements

Python 3.8 or higher required.
See requirements.txt for all dependencies.
