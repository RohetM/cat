"""
CatalogIQ â€“ Ingestion Service
==============================
Parses the supplier input CSV, sanitizes rows, and yields RawInputRecord objects.
"""
from __future__ import annotations

import io
import logging
from typing import List, Tuple
from uuid import uuid4

import pandas as pd

from app.schemas.product import RawInputRecord

logger = logging.getLogger(__name__)

# Canonical expected columns (case-insensitive match attempted)
EXPECTED_COLUMNS = [
    "Mfg_Part_Num",
    "Part_Desc",
    "Part_Manuf",
    "E1_Brand",
    "Unilog_Brand",
    "DIB_Brand",
]

COLUMN_ALIASES: dict[str, str] = {
    "mfg_part_num":   "Mfg_Part_Num",
    "part_desc":      "Part_Desc",
    "part_manuf":     "Part_Manuf",
    "e1_brand":       "E1_Brand",
    "unilog_brand":   "Unilog_Brand",
    "dib_brand":      "DIB_Brand",
    "manufacturer":   "Part_Manuf",
    "description":    "Part_Desc",
    "part_number":    "Mfg_Part_Num",
}


def _normalize_header(col: str) -> str:
    """Map any variant column name to the canonical one."""
    normalized = col.strip().replace(" ", "_")
    return COLUMN_ALIASES.get(normalized.lower(), normalized)


def parse_input_csv(content: bytes) -> Tuple[List[RawInputRecord], List[str]]:
    """
    Parse supplier CSV bytes into a list of RawInputRecord objects.

    Returns:
        records: list of parsed records
        warnings: list of non-fatal parsing warnings
    """
    warnings: List[str] = []
    text = content.decode("utf-8-sig", errors="replace")

    try:
        df = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)
    except Exception as exc:
        raise ValueError(f"CSV parse failure: {exc}") from exc

    # Normalize column headers
    df.columns = [_normalize_header(c) for c in df.columns]

    # Warn about missing expected columns
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            warnings.append(f"Missing expected column: '{col}'")

    # Fill any missing expected columns with empty strings
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    records: List[RawInputRecord] = []
    for idx, row in df.iterrows():
        raw_data = {
            "Mfg_Part_Num": row.get("Mfg_Part_Num", "") or "",
            "Part_Desc":    row.get("Part_Desc", "") or "",
            "Part_Manuf":   row.get("Part_Manuf", "") or "",
            "E1_Brand":     row.get("E1_Brand", "") or "",
            "Unilog_Brand": row.get("Unilog_Brand", "") or "",
            "DIB_Brand":    row.get("DIB_Brand", "") or "",
        }

        try:
            record = RawInputRecord(**raw_data)
            records.append(record)
        except Exception as exc:
            warnings.append(f"Row {idx}: skipped due to validation error â€“ {exc}")
            continue

    logger.info("Parsed %d records from CSV (%d warnings).", len(records), len(warnings))
    return records, warnings

