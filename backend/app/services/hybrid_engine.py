"""
CatalogIQ â€“ Hybrid Extraction & Entity Resolution Engine
=========================================================
LAYER 1 â€“ Deterministic: Regex pattern extraction + RapidFuzz entity resolution
LAYER 2 â€“ LLM Fallback : Structured Gemini/OpenAI call (triggered when L1 confidence < 0.85)
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from rapidfuzz import fuzz, process

from app.schemas.product import (
    ConfidenceMap,
    EnrichedProduct,
    ExtractedAttributes,
    LLMEnrichmentResponse,
    RawInputRecord,
    RecordStatus,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Known manufacturer / brand lookup tables (curated seed list)
# ---------------------------------------------------------------------------

KNOWN_MANUFACTURERS: List[str] = [
    "3M", "NORTON", "SAINT-GOBAIN", "FREUD", "DIABLO", "BOSCH", "DEWALT",
    "MAKITA", "MILWAUKEE", "FESTOOL", "MIRKA", "KLINGSPOR", "SIA ABRASIVES",
    "HENKEL", "ITW", "ILLINOIS TOOL WORKS", "STANLEY BLACK & DECKER",
    "EMERSON", "METABO", "HILTI", "STIHL", "HUSQVARNA", "RIDGID",
    "PORTER-CABLE", "CRAFTSMAN", "RYOBI", "BLACK+DECKER", "DREMEL",
    "WALTER SURFACE TECHNOLOGIES", "VSM ABRASIVES", "UNITED ABRASIVES",
    "BENCHMARK ABRASIVES", "MERCER ABRASIVES", "SUNMIGHT", "INDASA",
    "PETER WOLTERS", "HERMES ABRASIVES", "DEERFOS", "CARBORUNDUM",
    "CAMEL GRINDING WHEELS", "FLEXOVIT", "CGW ABRASIVES",
]

GENERIC_DISTRIBUTOR_PATTERNS: List[str] = [
    r"(?i)industrial\s+supply",
    r"(?i)distribution",
    r"(?i)supply\s+llc",
    r"(?i)supply\s+co",
    r"(?i)wholesale",
    r"(?i)trading\s+co",
]

UNBRANDED_VALUES: set = {
    "-- unbranded --",
    "-- no unilog brand --",
    "unbranded",
    "no brand",
    "unknown",
    "",
}

# ---------------------------------------------------------------------------
# Regex pattern registry for abrasive / industrial attributes
# ---------------------------------------------------------------------------

PATTERNS: Dict[str, re.Pattern] = {
    # Grit: P80, P150, 80 grit, 150-grit
    "grit": re.compile(
        r"\b(P\d{2,3}|(?:\d{1,4})\s?[-]?\s?grit)\b", re.IGNORECASE
    ),
    # Belt / sheet dimensions: 1/2"x18", 4"x24", 5 in, 4.5"
    "dimension_wxl": re.compile(
        r"(\d+(?:[./]\d+)?)\s?(?:\"|in|inch)?\s?[xXÃ—]\s?(\d+(?:[./]\d+)?)\s?(?:\"|in|inch)?",
        re.IGNORECASE,
    ),
    # Single diameter/size: 4.5", 5 in, 7"
    "dimension_single": re.compile(
        r"\b(\d+(?:[./]\d+)?)\s?(?:\"|in(?:ch)?)\b", re.IGNORECASE
    ),
    # Package qty: 6pc, 10/pk, 25 Disc/Box, 5-Pack
    "package_qty": re.compile(
        r"\b(\d+)\s?(?:pc|pcs|piece|pieces|/pk|/pack|pack|disc/box|disc|/box|[-]?pack)\b",
        re.IGNORECASE,
    ),
    # Voltage: 120V, 240 V, 18-Volt
    "voltage": re.compile(r"\b(\d+(?:\.\d+)?)\s?[-]?[Vv](?:olt|olts)?\b"),
    # Amperage: 15A, 7.5 amp
    "amperage": re.compile(r"\b(\d+(?:\.\d+)?)\s?[-]?[Aa](?:mp|mps)?\b"),
    # Wattage: 1200W, 750 watt
    "wattage": re.compile(r"\b(\d+(?:\.\d+)?)\s?[-]?[Ww](?:att|atts)?\b"),
    # Manufacturer part in parentheses, e.g. "Freud Inc (2435)"
    "manuf_code_in_parens": re.compile(r"\(([A-Z0-9]+)\)", re.IGNORECASE),
}

ABRASIVE_MATERIAL_KEYWORDS: Dict[str, str] = {
    r"(?i)ceramic": "Ceramic",
    r"(?i)alum(?:inum|inium)\s+oxide|al2o3|ao": "Aluminum Oxide",
    r"(?i)zirconi(?:a|um)": "Zirconia Alumina",
    r"(?i)silicon\s+carbide|sic": "Silicon Carbide",
    r"(?i)diamond": "Diamond",
    r"(?i)cbn|cubic\s+boron": "CBN",
    r"(?i)garnet": "Garnet",
    r"(?i)emery": "Emery",
}

PRODUCT_TYPE_KEYWORDS: Dict[str, str] = {
    r"(?i)sanding\s+belt|sand\s+belt": "Sanding Belt",
    r"(?i)cut[-\s]?off\s+(?:disc|disk|wheel)": "Cut-Off Disc",
    r"(?i)grinding\s+wheel|grind\s+wheel": "Grinding Wheel",
    r"(?i)flap\s+(?:disc|disk)": "Flap Disc",
    r"(?i)sanding\s+disc|sand\s+disc": "Sanding Disc",
    r"(?i)abrasive\s+sheet|sand(?:ing)?\s+sheet": "Sanding Sheet",
    r"(?i)abrasive\s+roll|sand(?:ing)?\s+roll": "Sanding Roll",
    r"(?i)wire\s+wheel|wire\s+brush": "Wire Wheel/Brush",
    r"(?i)jig\s+saw|jigsaw": "Jig Saw Blade",
    r"(?i)hole\s+saw": "Hole Saw",
    r"(?i)router\s+bit": "Router Bit",
    r"(?i)drill\s+bit": "Drill Bit",
    r"(?i)saw\s+blade|circular\s+saw": "Saw Blade",
    r"(?i)end\s+mill": "End Mill",
}

UOM_NORMALIZATION: Dict[str, str] = {
    '"': "IN", "in": "IN", "inch": "IN", "inches": "IN",
    "ft": "FT", "feet": "FT", "foot": "FT",
    "mm": "MM", "millimeter": "MM", "millimetre": "MM",
    "cm": "CM", "centimeter": "CM",
    "m": "M", "meter": "M", "metre": "M",
    "yd": "YD", "yard": "YD",
    "lb": "LB", "lbs": "LB", "pound": "LB",
    "oz": "OZ", "ounce": "OZ",
    "kg": "KG", "kilogram": "KG",
}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _normalize_uom(raw: str) -> str:
    return UOM_NORMALIZATION.get(raw.lower().strip(), raw.upper().strip())


def _parse_fraction(value: str) -> float:
    """Convert '1/2' or '4.5' to float."""
    value = value.strip()
    if "/" in value:
        num, den = value.split("/", 1)
        try:
            return float(num) / float(den)
        except ZeroDivisionError:
            return 0.0
    return float(value)


def _is_generic_distributor(manuf_raw: str) -> bool:
    for pat in GENERIC_DISTRIBUTOR_PATTERNS:
        if re.search(pat, manuf_raw):
            return True
    return False


def _resolve_brand_from_fallbacks(record: RawInputRecord) -> Optional[str]:
    for field in (record.e1_brand, record.unilog_brand, record.dib_brand):
        if field and field.lower().strip() not in UNBRANDED_VALUES:
            return field.strip()
    return None


def _fuzzy_match_manufacturer(raw_name: str) -> Tuple[Optional[str], float]:
    """
    Use RapidFuzz to match raw manufacturer string against known list.
    Returns (best_match, score 0-1).
    """
    # Strip parenthetical codes e.g. "Freud Inc (2435)" -> "Freud Inc"
    cleaned = re.sub(r"\s*\([^)]*\)\s*$", "", raw_name).strip()
    result = process.extractOne(
        cleaned.upper(),
        [m.upper() for m in KNOWN_MANUFACTURERS],
        scorer=fuzz.token_sort_ratio,
        score_cutoff=60,
    )
    if result:
        matched_upper, score, idx = result
        return KNOWN_MANUFACTURERS[idx], round(score / 100, 3)
    return cleaned.upper() or None, 0.5  # return cleaned fallback with low confidence


# ---------------------------------------------------------------------------
# LAYER 1: Deterministic Extraction
# ---------------------------------------------------------------------------

class DeterministicEngine:
    """Regex + RapidFuzz deterministic extraction layer."""

    def extract(self, record: RawInputRecord) -> Tuple[EnrichedProduct, float]:
        """
        Extract all attributes we can from the raw record deterministically.
        Returns (partial EnrichedProduct, layer_1_confidence).
        """
        product = EnrichedProduct(
            mfg_part_num=record.mfg_part_num,
            part_desc=record.part_desc,
            part_manuf_raw=record.part_manuf,
            e1_brand=record.e1_brand,
            unilog_brand=record.unilog_brand,
            dib_brand=record.dib_brand,
        )
        attrs = ExtractedAttributes()
        conf_fields: Dict[str, float] = {}
        desc = record.part_desc or ""

        # ---- Part number passthrough ----
        product.part_number = record.mfg_part_num
        conf_fields["part_number"] = 1.0 if record.mfg_part_num else 0.0

        # ---- Manufacturer / Brand resolution ----
        manuf_raw = record.part_manuf or ""
        if manuf_raw and not _is_generic_distributor(manuf_raw):
            matched_manuf, manuf_conf = _fuzzy_match_manufacturer(manuf_raw)
            product.manufacturer_name = matched_manuf
            conf_fields["manufacturer_name"] = manuf_conf
        else:
            # Fallback chain: E1 > Unilog > DIB
            brand_fallback = _resolve_brand_from_fallbacks(record)
            if brand_fallback:
                matched_manuf, manuf_conf = _fuzzy_match_manufacturer(brand_fallback)
                product.manufacturer_name = matched_manuf
                conf_fields["manufacturer_name"] = manuf_conf * 0.8  # penalise fallback
            else:
                product.manufacturer_name = None
                conf_fields["manufacturer_name"] = 0.0

        # Brand resolution
        brand_fallback = _resolve_brand_from_fallbacks(record)
        if brand_fallback and brand_fallback != product.manufacturer_name:
            product.brand_name = brand_fallback.upper()
            conf_fields["brand_name"] = 0.75
        elif product.manufacturer_name:
            product.brand_name = product.manufacturer_name
            conf_fields["brand_name"] = conf_fields["manufacturer_name"]
        else:
            conf_fields["brand_name"] = 0.0

        # ---- Grit extraction ----
        grit_match = PATTERNS["grit"].search(desc)
        if grit_match:
            attrs.grit = grit_match.group(1).upper().replace(" ", "")
            conf_fields["grit"] = 0.95
        else:
            conf_fields["grit"] = 0.0

        # ---- Dimension extraction ----
        wxl_match = PATTERNS["dimension_wxl"].search(desc)
        if wxl_match:
            w_raw, l_raw = wxl_match.group(1), wxl_match.group(2)
            attrs.width_value = _parse_fraction(w_raw)
            attrs.width_uom = "IN"
            attrs.length_value = _parse_fraction(l_raw)
            attrs.length_uom = "IN"
            conf_fields["dimensions"] = 0.92
        else:
            single_match = PATTERNS["dimension_single"].search(desc)
            if single_match:
                attrs.diameter_value = _parse_fraction(single_match.group(1))
                attrs.diameter_uom = "IN"
                conf_fields["dimensions"] = 0.80
            else:
                conf_fields["dimensions"] = 0.0

        # ---- Package quantity ----
        qty_match = PATTERNS["package_qty"].search(desc)
        if qty_match:
            attrs.package_quantity = int(qty_match.group(1))
            attrs.package_uom = "EA"
            conf_fields["package_quantity"] = 0.90
        else:
            conf_fields["package_quantity"] = 0.0

        # ---- Voltage / Amperage / Wattage ----
        v_match = PATTERNS["voltage"].search(desc)
        if v_match:
            attrs.voltage = v_match.group(1) + "V"
        a_match = PATTERNS["amperage"].search(desc)
        if a_match:
            attrs.amperage = a_match.group(1) + "A"
        w_match = PATTERNS["wattage"].search(desc)
        if w_match:
            attrs.wattage = w_match.group(1) + "W"

        # ---- Abrasive material ----
        for pattern, material_name in ABRASIVE_MATERIAL_KEYWORDS.items():
            if re.search(pattern, desc):
                attrs.abrasive_material = material_name
                break

        # ---- Product type ----
        for pattern, ptype in PRODUCT_TYPE_KEYWORDS.items():
            if re.search(pattern, desc):
                attrs.product_type = ptype
                conf_fields["product_type"] = 0.88
                break
        else:
            conf_fields["product_type"] = 0.0

        # ---- Simple short / invoice description (rule-based) ----
        if desc:
            short = desc[:60].rsplit(" ", 1)[0] if len(desc) > 60 else desc
            product.short_description = short
            conf_fields["short_description"] = 0.60  # low-conf, likely needs LLM

            invoice = desc[:30].rsplit(" ", 1)[0] if len(desc) > 30 else desc
            product.invoice_description = invoice
            conf_fields["invoice_description"] = 0.55

        product.attributes = attrs

        # ---- Compute overall confidence ----
        weights = {
            "manufacturer_name": 0.20,
            "brand_name": 0.10,
            "part_number": 0.10,
            "product_type": 0.15,
            "grit": 0.10,
            "dimensions": 0.10,
            "package_quantity": 0.05,
            "short_description": 0.10,
            "invoice_description": 0.10,
        }
        overall = sum(weights.get(k, 0) * v for k, v in conf_fields.items())
        conf_fields["overall"] = round(overall, 4)

        product.confidence = ConfidenceMap(**conf_fields)
        product.enrichment_source = "DETERMINISTIC"
        return product, overall


# ---------------------------------------------------------------------------
# LAYER 2: LLM Fallback Engine
# ---------------------------------------------------------------------------

LLM_SYSTEM_PROMPT = """You are an expert industrial product data analyst for a B2B distributor catalog.
Extract and normalize structured product attributes from the given raw supplier product description.
Return ONLY a valid JSON object matching the specified schema. Do NOT include markdown fences or prose."""

LLM_USER_TEMPLATE = """<product_enrichment_task>
  <raw_input>
    <mfg_part_num>{mfg_part_num}</mfg_part_num>
    <part_desc>{part_desc}</part_desc>
    <manufacturer_raw>{manufacturer_raw}</manufacturer_raw>
    <brand_candidates>{brand_candidates}</brand_candidates>
  </raw_input>
  <already_extracted>
    {already_extracted}
  </already_extracted>
  <instructions>
    Extract ALL missing attributes. Be concise. For short_description, use â‰¤60 chars.
    For invoice_description, use â‰¤30 chars. Output strict JSON matching the schema.
  </instructions>
</product_enrichment_task>"""


class LLMFallbackEngine:
    """Async LLM enrichment layer using OpenAI-compatible API."""

    def __init__(self) -> None:
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if settings.openai_api_key:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        elif settings.gemini_api_key:
            # Google GenAI uses OpenAI-compatible interface for function calling
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            self._client = genai
        return self._client

    async def enrich(self, product: EnrichedProduct) -> LLMEnrichmentResponse:
        """Call LLM to fill gaps. Returns structured LLMEnrichmentResponse."""
        client = self._get_client()
        if client is None:
            logger.warning("No LLM API key configured â€“ skipping LLM fallback.")
            return LLMEnrichmentResponse()

        already_extracted = json.dumps({
            "manufacturer_name": product.manufacturer_name,
            "brand_name": product.brand_name,
            "product_type": product.attributes.product_type,
            "grit": product.attributes.grit,
            "dimensions": (
                f"{product.attributes.width_value}x{product.attributes.length_value} IN"
                if product.attributes.width_value else
                f"{product.attributes.diameter_value} IN" if product.attributes.diameter_value
                else None
            ),
            "package_quantity": product.attributes.package_quantity,
        }, default=str)

        user_msg = LLM_USER_TEMPLATE.format(
            mfg_part_num=product.mfg_part_num or "",
            part_desc=product.part_desc or "",
            manufacturer_raw=product.part_manuf_raw or "",
            brand_candidates=", ".join(
                filter(None, [product.e1_brand, product.unilog_brand, product.dib_brand])
            ),
            already_extracted=already_extracted,
        )

        try:
            if settings.openai_api_key:
                response = await client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {"role": "system", "content": LLM_SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg},
                    ],
                    temperature=0.0,
                    max_tokens=600,
                    response_format={"type": "json_object"},
                )
                raw_json = response.choices[0].message.content or "{}"
            else:
                # Gemini path
                model = client.GenerativeModel(
                    model_name=settings.gemini_model,
                    system_instruction=LLM_SYSTEM_PROMPT,
                )
                resp = await model.generate_content_async(user_msg)
                raw_json = resp.text or "{}"
                # Strip markdown fences if present
                raw_json = re.sub(r"```(?:json)?", "", raw_json).strip()

            data = json.loads(raw_json)
            return LLMEnrichmentResponse(**data)

        except Exception as exc:
            logger.error("LLM enrichment failed: %s", exc)
            return LLMEnrichmentResponse()

    def _merge_llm_into_product(
        self, product: EnrichedProduct, llm: LLMEnrichmentResponse
    ) -> EnrichedProduct:
        """Merge LLM response into product, only filling empty / low-confidence fields."""
        conf = product.confidence.model_dump()

        def _fill(field: str, llm_val: Any, prod_conf_key: str, llm_conf: float = 0.80) -> None:
            if llm_val is not None and (
                getattr(product, field, None) is None or conf.get(prod_conf_key, 0) < 0.85
            ):
                setattr(product, field, llm_val)
                conf[prod_conf_key] = llm_conf

        _fill("manufacturer_name", llm.manufacturer_name, "manufacturer_name")
        _fill("brand_name", llm.brand_name, "brand_name")
        _fill("short_description", llm.short_description, "short_description", 0.88)
        _fill("invoice_description", llm.invoice_description, "invoice_description", 0.88)
        _fill("mobile_description", llm.mobile_description, "mobile_description", 0.82)
        _fill("marketing_description", llm.marketing_description, "marketing_description", 0.82)
        _fill("class_name", llm.class_name, "class_name", 0.78)
        _fill("fine_class", llm.fine_class, "fine_class", 0.78)

        # Attributes
        if llm.product_type and not product.attributes.product_type:
            product.attributes.product_type = llm.product_type
            conf["product_type"] = 0.82
        if llm.abrasive_material and not product.attributes.abrasive_material:
            product.attributes.abrasive_material = llm.abrasive_material
        if llm.backing_material and not product.attributes.backing_material:
            product.attributes.backing_material = llm.backing_material
        if llm.grit and not product.attributes.grit:
            product.attributes.grit = llm.grit
            conf["grit"] = 0.82
        if llm.package_quantity and not product.attributes.package_quantity:
            product.attributes.package_quantity = llm.package_quantity
        if llm.material and not product.attributes.material:
            product.attributes.material = llm.material
        if llm.application and not product.attributes.application:
            product.attributes.application = llm.application
        if llm.color and not product.attributes.color:
            product.attributes.color = llm.color
        if llm.certifications and not product.attributes.certifications:
            product.attributes.certifications = llm.certifications

        # Recompute overall
        weights = {
            "manufacturer_name": 0.20, "brand_name": 0.10, "part_number": 0.10,
            "product_type": 0.15, "grit": 0.10, "dimensions": 0.10,
            "package_quantity": 0.05, "short_description": 0.10, "invoice_description": 0.10,
        }
        conf["overall"] = round(sum(weights.get(k, 0) * v for k, v in conf.items()), 4)
        product.confidence = ConfidenceMap(**conf)
        product.enrichment_source = "LLM"
        return product


# ---------------------------------------------------------------------------
# Orchestrator: HybridEnrichmentEngine
# ---------------------------------------------------------------------------

class HybridEnrichmentEngine:
    """
    Main orchestrator: runs Layer 1 (deterministic) first; if confidence < threshold,
    invokes Layer 2 (LLM fallback) and merges results.
    """

    CONFIDENCE_THRESHOLD: float = 0.85

    def __init__(self) -> None:
        self._det = DeterministicEngine()
        self._llm = LLMFallbackEngine()

    async def process_record(self, record: RawInputRecord) -> EnrichedProduct:
        """Full pipeline for a single input record."""
        t0 = time.monotonic()

        # Layer 1
        product, l1_conf = self._det.extract(record)
        logger.debug(
            "Record %s â€“ L1 confidence=%.3f", product.mfg_part_num, l1_conf
        )

        # Layer 2 (conditional)
        if l1_conf < self.CONFIDENCE_THRESHOLD:
            try:
                llm_response = await self._llm.enrich(product)
                product = self._llm._merge_llm_into_product(product, llm_response)
                logger.debug(
                    "Record %s â€“ LLM merged, new confidence=%.3f",
                    product.mfg_part_num,
                    product.confidence.overall,
                )
            except Exception as exc:
                logger.warning("LLM fallback exception for %s: %s", product.mfg_part_num, exc)

        # Status assignment
        if product.confidence.overall >= self.CONFIDENCE_THRESHOLD:
            product.status = RecordStatus.ENRICHED
        else:
            product.status = RecordStatus.REQUIRES_REVIEW

        logger.info(
            "Processed %s in %.3fs â†’ status=%s conf=%.3f",
            product.mfg_part_num, time.monotonic() - t0,
            product.status.value, product.confidence.overall,
        )
        return product

    async def process_batch(
        self, records: List[RawInputRecord], concurrency: int = 10
    ) -> List[EnrichedProduct]:
        """Process a batch of records with bounded concurrency."""
        import asyncio
        semaphore = asyncio.Semaphore(concurrency)

        async def _guarded(record: RawInputRecord) -> EnrichedProduct:
            async with semaphore:
                return await self.process_record(record)

        return await asyncio.gather(*[_guarded(r) for r in records])

