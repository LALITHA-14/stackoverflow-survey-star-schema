#!/usr/bin/env python3
"""Run the five analytical queries and save CSV and EXPLAIN ANALYZE results."""

from __future__ import annotations

import csv
import os
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
QUERIES_DIR = ROOT / "queries"
OUTPUT_DIR = ROOT / "output"
EXPLAIN_DIR = ROOT / "explain_analyze"

DB_CONFIG = {
    "host": os.getenv("PGHOST", "127.0.0.1"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("PGDATABASE", "survey_db"),
    "user": os.getenv("PGUSER", "survey_user"),
    "password": os.getenv("PGPASSWORD", "survey_password"),
}

QUERY_FILES = [
    "query_1_salary_percentile.sql",
    "query_2_top_technologies.sql",
    "query_3_compensation_rank.sql",
    "query_4_desired_technologies.sql",
    "query_5_compensation_comparison.sql",
]


def clean_sql(sql: str) -> str:
    sql = sql.strip()
    if sql.endswith(";"):
        sql = sql[:-1].rstrip()
    return sql


def write_csv(path: Path, headers: list[str], rows: list[tuple]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)


def run_query(cursor, query_path: Path) -> None:
    sql = clean_sql(query_path.read_text(encoding="utf-8"))

    cursor.execute(sql)
    rows = cursor.fetchall()
    headers = [column.name for column in cursor.description]

    output_path = OUTPUT_DIR / f"{query_path.stem.replace('.sql', '')}_results.csv"
    write_csv(output_path, headers, rows)

    cursor.execute("EXPLAIN ANALYZE " + sql)
    plan_rows = cursor.fetchall()

    explain_path = EXPLAIN_DIR / f"{query_path.stem.replace('.sql', '')}_plan.txt"
    with explain_path.open("w", encoding="utf-8", newline="") as file:
        for row in plan_rows:
            file.write(str(row[0]))
            file.write("\n")

    print(
        f"{query_path.name}: {len(rows):,} rows -> "
        f"{output_path.name}, {explain_path.name}"
    )


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    EXPLAIN_DIR.mkdir(exist_ok=True)

    print(f"Database host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")

    try:
        with psycopg2.connect(**DB_CONFIG) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_user, current_database()")
                user, database = cursor.fetchone()
                print(f"Connected as {user} to {database}")

                for filename in QUERY_FILES:
                    query_path = QUERIES_DIR / filename
                    if not query_path.exists():
                        raise FileNotFoundError(f"Missing query file: {query_path}")
                    run_query(cursor, query_path)

    except psycopg2.OperationalError as exc:
        raise SystemExit(
            "\nCould not connect to PostgreSQL.\n"
            "For the conflict-free Docker workflow, run:\n"
            "docker compose -f docker-compose.yml -f docker-compose.local.yml "
            "run --rm etl python scripts/run_analysis.py\n\n"
            f"Original error: {exc}"
        )

    print("\nAnalysis completed successfully.")


if __name__ == "__main__":
    main()
