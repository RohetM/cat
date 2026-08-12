"""
CatalogIQ â€“ Validation Engine & Ground-Truth Evaluator
=======================================================
Validator  : Field-level rule checks (length, UOM, required fields).
Evaluator  : Token + RapidFuzz comparison against expected output CSV.
"""
from __future__ import annotations

import csv
import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rapidfuzz import fuzz

from app.schemas.product import (
    DELIVERY_COLUMNS,
    DeliveryRow,
    EnrichedProduct,
    EvaluationMetrics,
    RecordStatus,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Validation Rules
# ---------------------------------------------------------------------------

VALID_UOMS: set = {
    "EA", "BX", "PK", "PR", "ST", "RL", "FT", "IN", "YD",
    "LB", "OZ", "KG", "M", "MM", "CM",
}

MAX_LENGTHS: Dict[str, int] = {
    "short_description": 60,
    "invoice_description": 30,
    "manufacturer_name": 120,
    "brand_name": 80,
    "part_number": 80,
    "class_name": 100,
    "fine_class": 100,
}

REQUIRED_FIELDS: List[str] = [
    "mfg_part_num",
    "manufacturer_name",
]


class ValidationEngine:
    """
    Validates an EnrichedProduct against business rules.
    Populates product.validation_errors list and updates status if needed.
    """

    def validate(self, product: EnrichedProduct) -> EnrichedProduct:
        errors: List[str] = []

        # ---- Required fields ----
        for field in REQUIRED_FIELDS:
            if not getattr(product, field, None):
                errors.append(f"REQUIRED_FIELD_MISSING: {field}")

        # ---- Length constraints ----
        for field, max_len in MAX_LENGTHS.items():
            val = getattr(product, field, None)
            if val and len(val) > max_len:
                errors.append(
                    f"FIELD_TOO_LONG: {field} ({len(val)} > {max_len})"
                )

        # ---- UOM validation ----
        attrs = product.attributes
        for uom_field in (
            attrs.length_uom, attrs.width_uom, attrs.diameter_uom,
            attrs.height_uom, attrs.thickness_uom, attrs.package_uom,
        ):
            if uom_field and uom_field.upper() not in VALID_UOMS:
                errors.append(f"INVALID_UOM: {uom_field}")

        # ---- Package quantity sanity ----
        if attrs.package_quantity is not None and attrs.package_quantity < 1:
            errors.append("INVALID_PACKAGE_QTY: must be >= 1")

        # ---- Confidence threshold ----
        if product.confidence.overall < 0.85:
            errors.append(
                f"LOW_CONFIDENCE: overall={product.confidence.overall:.3f}"
            )

        product.validation_errors = errors

        # If validation errors exist AND record is not already approved
        if errors and product.status != RecordStatus.APPROVED:
            product.status = RecordStatus.REQUIRES_REVIEW

        return product


# ---------------------------------------------------------------------------
# Delivery Row Builder
# ---------------------------------------------------------------------------

def build_delivery_row(product: EnrichedProduct) -> Dict[str, str]:
    """
    Map an EnrichedProduct to the full 252-column delivery format.
    All unmapped columns default to empty string.
    """
    row: Dict[str, str] = {col: "" for col in DELIVERY_COLUMNS}

    def _s(v: Any) -> str:
        return str(v) if v is not None else ""

    # Core identifiers
    row["PART_NUMBER"] = _s(product.part_number or product.mfg_part_num)
    row["Mfg_Part_Num"] = _s(product.mfg_part_num)
    row["MANUFACTURER_NAME"] = _s(product.manufacturer_name)
    row["BRAND_NAME"] = _s(product.brand_name)
    row["Part_Desc"] = _s(product.part_desc)

    # Descriptions
    row["Short_Desc"] = _s(product.short_description)
    row["Invoice_Desc"] = _s(product.invoice_description)
    row["Mobile_Desc"] = _s(product.mobile_description)
    row["Marketing_Desc"] = _s(product.marketing_description)

    # Classification
    row["Class"] = _s(product.class_name)
    row["Fine"] = _s(product.fine_class)
    row["Product_Type"] = _s(product.attributes.product_type)

    # Extracted attributes
    a = product.attributes
    row["Attr_Grit"] = _s(a.grit)
    row["Attr_Abrasive_Material"] = _s(a.abrasive_material)
    row["Attr_Backing_Material"] = _s(a.backing_material)
    row["Attr_Bond_Type"] = _s(a.bond_type)
    row["Attr_Grade"] = _s(a.grade)
    row["Attr_Application"] = _s(a.application)
    row["Attr_Length_Value"] = _s(a.length_value)
    row["Attr_Length_UOM"] = _s(a.length_uom)
    row["Attr_Width_Value"] = _s(a.width_value)
    row["Attr_Width_UOM"] = _s(a.width_uom)
    row["Attr_Diameter_Value"] = _s(a.diameter_value)
    row["Attr_Diameter_UOM"] = _s(a.diameter_uom)
    row["Attr_Thickness_Value"] = _s(a.thickness_value)
    row["Attr_Thickness_UOM"] = _s(a.thickness_uom)
    row["Attr_Height_Value"] = _s(a.height_value)
    row["Attr_Height_UOM"] = _s(a.height_uom)
    row["Attr_Pkg_Qty"] = _s(a.package_quantity)
    row["Attr_Pkg_UOM"] = _s(a.package_uom)
    row["Attr_Voltage"] = _s(a.voltage)
    row["Attr_Amperage"] = _s(a.amperage)
    row["Attr_Wattage"] = _s(a.wattage)
    row["Attr_Material"] = _s(a.material)
    row["Attr_Finish"] = _s(a.finish)
    row["Attr_Color"] = _s(a.color)
    row["Attr_Series"] = _s(a.series)
    row["Attr_Model_Number"] = _s(a.model_number)
    row["Attr_Certifications"] = _s(a.certifications)
    row["Attr_Country_Of_Origin"] = _s(a.country_of_origin)
    row["Attr_Compatible_With"] = _s(a.compatible_with)

    # Status
    row["Status"] = product.status.value

    return row


# ---------------------------------------------------------------------------
# CSV Export Builder
# ---------------------------------------------------------------------------

def build_export_csv(products: List[EnrichedProduct]) -> str:
    """Return a 252-column CSV string for all products."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=DELIVERY_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for product in products:
        row = build_delivery_row(product)
        writer.writerow(row)
    return output.getvalue()


# ---------------------------------------------------------------------------
# Ground-Truth Evaluator
# ---------------------------------------------------------------------------

EVAL_FIELD_MAP: Dict[str, Tuple[str, str]] = {
    # (enriched_product_attr, expected_csv_column)
    "manufacturer_name": ("manufacturer_name", "MANUFACTURER_NAME"),
    "brand_name":        ("brand_name",        "BRAND_NAME"),
    "part_number":       ("part_number",        "PART_NUMBER"),
    "short_description": ("short_description",  "Short_Desc"),
    "invoice_description": ("invoice_description", "Invoice_Desc"),
    "class_name":        ("class_name",         "Class"),
    "fine_class":        ("fine_class",         "Fine"),
}

ATTRIBUTE_EVAL_FIELDS: List[Tuple[str, str]] = [
    # (attribute sub-field, expected_csv_column)
    ("grit",              "Attr_Grit"),
    ("abrasive_material", "Attr_Abrasive_Material"),
    ("product_type",      "Product_Type"),
    ("package_quantity",  "Attr_Pkg_Qty"),
]

FUZZY_MATCH_THRESHOLD: int = 80  # RapidFuzz score 0-100


def _normalize_for_eval(val: Optional[str]) -> str:
    if not val:
        return ""
    return val.lower().strip()


def _fuzzy_match(predicted: str, expected: str) -> bool:
    """Return True if RapidFuzz token_sort_ratio >= threshold."""
    if not predicted and not expected:
        return True
    if not predicted or not expected:
        return False
    score = fuzz.token_sort_ratio(
        _normalize_for_eval(predicted),
        _normalize_for_eval(expected),
    )
    return score >= FUZZY_MATCH_THRESHOLD


class GroundTruthEvaluator:
    """
    Compares enriched product records against the expected delivery CSV.
    Keyed on Mfg_Part_Num for matching rows.
    """

    def __init__(self, expected_csv_path: Optional[str] = None) -> None:
        self._expected: Dict[str, Dict[str, str]] = {}
        if expected_csv_path and Path(expected_csv_path).exists():
            self._load_expected(expected_csv_path)

    def _load_expected(self, path: str) -> None:
        with open(path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                key = (row.get("Mfg_Part_Num") or "").strip()
                if key:
                    self._expected[key] = row

    def load_from_bytes(self, content: bytes) -> None:
        """Load expected CSV from uploaded bytes."""
        text = content.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            key = (row.get("Mfg_Part_Num") or "").strip()
            if key:
                self._expected[key] = row

    def evaluate(self, products: List[EnrichedProduct]) -> EvaluationMetrics:
        if not self._expected:
            logger.warning("No ground-truth data loaded; returning zero metrics.")
            return EvaluationMetrics(
                manufacturer_accuracy=0.0, brand_accuracy=0.0,
                attribute_accuracy=0.0, description_compliance=0.0,
                overall_field_accuracy=0.0, total_evaluated=0, matched_records=0,
            )

        total = len(products)
        matched = 0

        manuf_hits = brand_hits = attr_hits = desc_hits = 0
        manuf_total = brand_total = attr_total = desc_total = 0

        for product in products:
            key = (product.mfg_part_num or "").strip()
            expected_row = self._expected.get(key)
            if not expected_row:
                continue
            matched += 1

            # Manufacturer accuracy
            exp_manuf = expected_row.get("MANUFACTURER_NAME", "")
            manuf_total += 1
            if _fuzzy_match(product.manufacturer_name, exp_manuf):
                manuf_hits += 1

            # Brand accuracy
            exp_brand = expected_row.get("BRAND_NAME", "")
            brand_total += 1
            if _fuzzy_match(product.brand_name, exp_brand):
                brand_hits += 1

            # Attribute accuracy (grit, material, type, qty)
            for attr_field, csv_col in ATTRIBUTE_EVAL_FIELDS:
                exp_val = expected_row.get(csv_col, "")
                pred_val = str(getattr(product.attributes, attr_field, "") or "")
                attr_total += 1
                if _fuzzy_match(pred_val, exp_val):
                    attr_hits += 1

            # Description compliance (short + invoice length within spec AND non-empty)
            desc_total += 2
            sd = product.short_description or ""
            inv = product.invoice_description or ""
            if sd and len(sd) <= 60:
                desc_hits += 1
            if inv and len(inv) <= 30:
                desc_hits += 1

        def _pct(hits: int, tot: int) -> float:
            return round(hits / tot * 100, 2) if tot > 0 else 0.0

        manuf_acc   = _pct(manuf_hits,  manuf_total)
        brand_acc   = _pct(brand_hits,  brand_total)
        attr_acc    = _pct(attr_hits,   attr_total)
        desc_comp   = _pct(desc_hits,   desc_total)
        total_hits  = manuf_hits + brand_hits + attr_hits + desc_hits
        total_denom = manuf_total + brand_total + attr_total + desc_total
        overall_acc = _pct(total_hits, total_denom)

        return EvaluationMetrics(
            manufacturer_accuracy=manuf_acc,
            brand_accuracy=brand_acc,
            attribute_accuracy=attr_acc,
            description_compliance=desc_comp,
            overall_field_accuracy=overall_acc,
            total_evaluated=total,
            matched_records=matched,
        )

