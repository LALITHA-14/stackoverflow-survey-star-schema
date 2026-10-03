#!/usr/bin/env python3
"""Load Stack Overflow Developer Survey 2023 into the PostgreSQL star schema."""

from __future__ import annotations

import csv
import io
import os
import re
from pathlib import Path
from typing import Iterable

import psycopg2
from psycopg2.extras import execute_values

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "survey_results_public.csv"
SCHEMA_FILE = ROOT / "schema" / "schema.sql"
INDEX_FILE = ROOT / "schema" / "indexes.sql"

DB_CONFIG = {
    "host": os.getenv("PGHOST", "127.0.0.1"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("PGDATABASE", "survey_db"),
    "user": os.getenv("PGUSER", "survey_user"),
    "password": os.getenv("PGPASSWORD", "survey_password"),
}


def clean_text(value: str | None) -> str:
    if value is None:
        return "Unknown"
    value = value.strip()
    return value if value else "Unknown"


def clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value if value else None


def parse_number(value: str | None) -> float | None:
    if value is None:
        return None
    value = value.strip().replace(",", "")
    if not value or value.lower() in {"na", "n/a", "none", "null"}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_years_code(value: str | None) -> int | None:
    if value is None:
        return None

    value = value.strip()
    if not value:
        return None

    lowered = value.lower()

    if lowered == "less than 1 year":
        return 0

    if lowered == "more than 50 years":
        return 51

    match = re.fullmatch(r"\d+", value)
    return int(match.group()) if match else None


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}\n"
            "Place survey_results_public.csv in the data/ directory."
        )

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def unique_dimension_values(
    rows: Iterable[dict[str, str]], column: str
) -> list[str]:
    values = {clean_text(row.get(column)) for row in rows}
    return sorted(values, key=str.casefold)


def execute_sql_file(cursor, path: Path) -> None:
    cursor.execute(path.read_text(encoding="utf-8"))


def load_dimensions(
    cursor, rows: list[dict[str, str]]
) -> dict[str, dict[str, int]]:
    dimensions = {
        "country": unique_dimension_values(rows, "Country"),
        "employment": unique_dimension_values(rows, "Employment"),
        "dev_type": unique_dimension_values(rows, "DevType"),
    }

    execute_values(
        cursor,
        """
        INSERT INTO dim_country (country_name)
        VALUES %s
        ON CONFLICT (country_name) DO NOTHING
        """,
        [(value,) for value in dimensions["country"]],
    )

    execute_values(
        cursor,
        """
        INSERT INTO dim_employment (employment_name)
        VALUES %s
        ON CONFLICT (employment_name) DO NOTHING
        """,
        [(value,) for value in dimensions["employment"]],
    )

    execute_values(
        cursor,
        """
        INSERT INTO dim_developer_type (dev_type_name)
        VALUES %s
        ON CONFLICT (dev_type_name) DO NOTHING
        """,
        [(value,) for value in dimensions["dev_type"]],
    )

    cursor.execute("SELECT country_name, country_id FROM dim_country")
    country_map = dict(cursor.fetchall())

    cursor.execute("SELECT employment_name, employment_id FROM dim_employment")
    employment_map = dict(cursor.fetchall())

    cursor.execute("SELECT dev_type_name, dev_type_id FROM dim_developer_type")
    dev_type_map = dict(cursor.fetchall())

    return {
        "country": country_map,
        "employment": employment_map,
        "dev_type": dev_type_map,
    }


def copy_facts(
    cursor,
    rows: list[dict[str, str]],
    maps: dict[str, dict[str, int]],
) -> int:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    count = 0

    for row in rows:
        country = clean_text(row.get("Country"))
        employment = clean_text(row.get("Employment"))
        dev_type = clean_text(row.get("DevType"))

        writer.writerow(
            [
                maps["country"][country],
                maps["employment"][employment],
                maps["dev_type"][dev_type],
                parse_number(row.get("ConvertedCompYearly")),
                parse_years_code(row.get("YearsCode")),
                clean_optional_text(row.get("LanguageHaveWorkedWith")),
                clean_optional_text(row.get("LanguageWantToWorkWith")),
            ]
        )
        count += 1

    buffer.seek(0)

    cursor.copy_expert(
        """
        COPY fact_responses (
            country_id,
            employment_id,
            dev_type_id,
            ConvertedCompYearly,
            YearsCode,
            LanguageHaveWorkedWith,
            LanguageWantToWorkWith
        )
        FROM STDIN WITH (FORMAT CSV, NULL '')
        """,
        buffer,
    )

    return count


def main() -> None:
    print(f"Database host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"Reading dataset: {DATA_FILE}")

    rows = read_rows(DATA_FILE)
    print(f"Rows read: {len(rows):,}")

    try:
        with psycopg2.connect(**DB_CONFIG) as connection:
            with connection.cursor() as cursor:
                execute_sql_file(cursor, SCHEMA_FILE)

                maps = load_dimensions(cursor, rows)
                fact_count = copy_facts(cursor, rows, maps)

                execute_sql_file(cursor, INDEX_FILE)

                cursor.execute("SELECT COUNT(*) FROM dim_country")
                country_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM dim_employment")
                employment_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM dim_developer_type")
                dev_type_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM fact_responses")
                loaded_fact_count = cursor.fetchone()[0]

    except psycopg2.OperationalError as exc:
        raise SystemExit(
            "\nCould not connect to PostgreSQL.\n"
            f"Host: {DB_CONFIG['host']}\n"
            f"Port: {DB_CONFIG['port']}\n"
            "If you are using the local Docker workflow, run this script "
            "inside the ETL container with docker compose run --rm etl.\n\n"
            f"Original error: {exc}"
        )

    print("\nETL completed successfully.")
    print(f"Countries:          {country_count:,}")
    print(f"Employment values:  {employment_count:,}")
    print(f"Developer types:    {dev_type_count:,}")
    print(f"Fact rows copied:    {fact_count:,}")
    print(f"Fact rows in DB:     {loaded_fact_count:,}")


if __name__ == "__main__":
    main()
