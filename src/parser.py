import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from config import MANIFEST_PATH, RAW_DIR


RESISTANCE_COLUMNS = [
    "Region", "Country", "Year", "Pathogen", "Antibiotic",
    "Resistance Percentage", "Isolates Tested",
]
USE_COLUMNS = [
    "Region", "Country", "Year", "Antibiotic Class / Category",
    "Consumption Rate", "Unit", "Data Source",
]


def to_numeric(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text or text.lower() in {"nan", "null", "none", "n/a", "*"}:
        return None
    if text.startswith("<") or text.startswith(">"):
        return None
    try:
        return float(text.replace(",", ""))
    except (TypeError, ValueError):
        return None


def numeric_year(value: Any) -> int | None:
    number = to_numeric(value)
    return int(number) if number is not None and number.is_integer() else None


def parse_all() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, datetime]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    resistance_rows: list[dict] = []
    use_rows: list[dict] = []
    latest_resistance: dict[str, int | None] = {}
    latest_use: dict[str, int | None] = {}

    for entry in manifest:
        cache_path = RAW_DIR / f"{entry['slug']}.json"
        resistance_years: list[int] = []
        use_years: list[int] = []
        if cache_path.exists():
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            for response in cache.get("responses", []):
                payload = response.get("payload")
                if not isinstance(payload, list):
                    continue

                records: list[dict] = []
                def collect(value: Any):
                    if isinstance(value, list):
                        for item in value:
                            collect(item)
                    elif isinstance(value, dict):
                        keys = {key.lower(): key for key in value}
                        if "organism" in keys or (
                            ("antibioticid" in keys or "antimicrobialid" in keys)
                            and "value" in keys
                        ):
                            records.append(value)
                        for child in value.values():
                            collect(child)

                collect(payload)

                page_is_use = "page=use" in str(response.get("post_data", ""))
                for record in records:
                    lower = {str(key).lower(): key for key in record}

                    if page_is_use or "year" in lower and "antimicrobial" in lower and "organism" not in lower:
                        year_key = lower.get("year")
                        antimicrobial_key = lower.get("antimicrobial")
                        value_key = lower.get("value")
                        sector_key = lower.get("sector")
                        year = numeric_year(record.get(year_key)) if year_key else None
                        if year is not None:
                            use_years.append(year)
                        use_rows.append({
                            "Region": entry["region"],
                            "Country": entry["country"],
                            "Year": year,
                            "Antibiotic Class / Category": record.get(antimicrobial_key) if antimicrobial_key else None,
                            "Consumption Rate": to_numeric(record.get(value_key)) if value_key else None,
                            "Unit": "DDD per 1,000 inhabitants/day",
                            "Data Source": record.get(sector_key) if sector_key else "ResistanceMap",
                        })
                        continue

                    organism_key = lower.get("organism")
                    antimicrobial_key = lower.get("antimicrobial")
                    year_key = lower.get("year")
                    value_key = lower.get("value")
                    isolates_key = lower.get("isolatestested")
                    if organism_key or (antimicrobial_key and value_key):
                        year = numeric_year(record.get(year_key)) if year_key else None
                        if year is not None:
                            resistance_years.append(year)
                        row = {
                            "Region": entry["region"],
                            "Country": entry["country"],
                            "Year": year,
                            "Pathogen": record.get(organism_key) if organism_key else None,
                            "Antibiotic": record.get(antimicrobial_key) if antimicrobial_key else None,
                            "Resistance Percentage": to_numeric(record.get(value_key)) if value_key else None,
                            "Isolates Tested": to_numeric(record.get(isolates_key)) if isolates_key else None,
                        }
                        for key, value in record.items():
                            if key not in {"Organism", "Antimicrobial", "year", "Year", "value", "IsolatesTested"}:
                                row[key] = value
                        resistance_rows.append(row)

        latest_resistance[entry["country"]] = max(resistance_years) if resistance_years else None
        latest_use[entry["country"]] = max(use_years) if use_years else None

    df_overview = pd.DataFrame(
        [
            {
                "Region": entry["region"],
                "Country": entry["country"],
                "Resistance Data Available": entry["resistance_available"],
                "Use Data Available": entry["use_available"],
                "Latest Resistance Year": latest_resistance.get(entry["country"]),
                "Latest Use Year": latest_use.get(entry["country"]),
                "Source URL": entry["source_url"],
            }
            for entry in manifest
        ],
        columns=[
            "Region", "Country", "Resistance Data Available", "Use Data Available",
            "Latest Resistance Year", "Latest Use Year", "Source URL",
        ],
    )
    df_resistance = pd.DataFrame(resistance_rows)
    df_use = pd.DataFrame(use_rows)

    for frame in (df_overview, df_resistance, df_use):
        frame.replace("", pd.NA, inplace=True)
    for column in ("Latest Resistance Year", "Latest Use Year"):
        df_overview[column] = pd.to_numeric(df_overview[column], errors="coerce").astype("Int64")
    for column in ("Year", "Isolates Tested", "Resistance Percentage"):
        if column in df_resistance:
            df_resistance[column] = pd.to_numeric(df_resistance[column], errors="coerce")
    for column in ("Year", "Consumption Rate"):
        if column in df_use:
            df_use[column] = pd.to_numeric(df_use[column], errors="coerce")
    if "Year" in df_resistance:
        df_resistance["Year"] = df_resistance["Year"].astype("Int64")
    if "Year" in df_use:
        df_use["Year"] = df_use["Year"].astype("Int64")

    return df_overview, df_resistance, df_use, datetime.now(timezone.utc)
