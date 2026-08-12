"""
CatalogIQ â€“ Pydantic v2 Schemas
Covers: Input ingestion, extracted attributes, LLM payload contracts,
HITL review requests, and the full 252-column delivery output model.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class RecordStatus(str, Enum):
    RAW = "RAW"
    ENRICHED = "ENRICHED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    APPROVED = "APPROVED"


class UOMCode(str, Enum):
    EA = "EA"   # Each
    BX = "BX"   # Box
    PK = "PK"   # Pack
    PR = "PR"   # Pair
    ST = "ST"   # Set
    RL = "RL"   # Roll
    FT = "FT"   # Foot
    IN = "IN"   # Inch
    YD = "YD"   # Yard
    LB = "LB"   # Pound
    OZ = "OZ"   # Ounce
    KG = "KG"   # Kilogram
    M  = "M"    # Meter
    MM = "MM"   # Millimeter
    CM = "CM"   # Centimeter


# ---------------------------------------------------------------------------
# Input / Ingestion Schema
# ---------------------------------------------------------------------------

class RawInputRecord(BaseModel):
    """Represents exactly one row from the supplier input CSV."""

    mfg_part_num: Optional[str] = Field(None, alias="Mfg_Part_Num")
    part_desc: Optional[str] = Field(None, alias="Part_Desc")
    part_manuf: Optional[str] = Field(None, alias="Part_Manuf")
    e1_brand: Optional[str] = Field(None, alias="E1_Brand")
    unilog_brand: Optional[str] = Field(None, alias="Unilog_Brand")
    dib_brand: Optional[str] = Field(None, alias="DIB_Brand")

    model_config = {"populate_by_name": True}

    @field_validator("mfg_part_num", "part_desc", "part_manuf",
                     "e1_brand", "unilog_brand", "dib_brand", mode="before")
    @classmethod
    def sanitize_csv_injection(cls, v: Any) -> Optional[str]:
        """Strip CSV injection characters from the start of any field."""
        if isinstance(v, str):
            v = v.strip()
            if v in ("", "nan", "None", "N/A", "n/a"):
                return None
            while v and v[0] in ("=", "@", "+", "-"):
                v = v[1:]
            return v or None
        return v


# ---------------------------------------------------------------------------
# Extracted Attribute Schema  (deterministic + LLM merged)
# ---------------------------------------------------------------------------

class ExtractedAttributes(BaseModel):
    """Granular, field-level extracted attributes for a product."""

    # Physical dimensions
    length_value: Optional[float] = None
    length_uom: Optional[str] = None
    width_value: Optional[float] = None
    width_uom: Optional[str] = None
    diameter_value: Optional[float] = None
    diameter_uom: Optional[str] = None
    thickness_value: Optional[float] = None
    thickness_uom: Optional[str] = None
    height_value: Optional[float] = None
    height_uom: Optional[str] = None

    # Abrasive-specific
    grit: Optional[str] = None
    abrasive_material: Optional[str] = None
    backing_material: Optional[str] = None
    product_type: Optional[str] = None
    bond_type: Optional[str] = None
    grade: Optional[str] = None

    # Packaging
    package_quantity: Optional[int] = None
    package_uom: Optional[str] = None

    # Electrical
    voltage: Optional[str] = None
    amperage: Optional[str] = None
    wattage: Optional[str] = None

    # Material / Finish
    material: Optional[str] = None
    finish: Optional[str] = None
    color: Optional[str] = None

    # Application
    application: Optional[str] = None
    compatible_with: Optional[str] = None

    # Misc
    series: Optional[str] = None
    model_number: Optional[str] = None
    certifications: Optional[str] = None
    country_of_origin: Optional[str] = None

    model_config = {"extra": "allow"}  # allow dynamic attributes


class ConfidenceMap(BaseModel):
    """Field-level confidence scores in [0.0, 1.0]."""
    manufacturer_name: float = 0.0
    brand_name: float = 0.0
    part_number: float = 0.0
    product_type: float = 0.0
    grit: float = 0.0
    dimensions: float = 0.0
    package_quantity: float = 0.0
    short_description: float = 0.0
    invoice_description: float = 0.0
    overall: float = 0.0

    model_config = {"extra": "allow"}


# ---------------------------------------------------------------------------
# LLM Payload Contracts  (structured output enforcement)
# ---------------------------------------------------------------------------

class LLMEnrichmentResponse(BaseModel):
    """Strict schema for LLM JSON output â€“ prevents hallucination leakage."""

    manufacturer_name: Optional[str] = Field(None, max_length=120)
    brand_name: Optional[str] = Field(None, max_length=80)
    product_type: Optional[str] = Field(None, max_length=100)
    abrasive_material: Optional[str] = Field(None, max_length=80)
    backing_material: Optional[str] = Field(None, max_length=80)
    grit: Optional[str] = Field(None, max_length=20)
    dimensions: Optional[str] = Field(None, max_length=60)
    package_quantity: Optional[int] = Field(None, ge=1)
    package_uom: Optional[str] = Field(None, max_length=10)
    short_description: Optional[str] = Field(None, max_length=60)
    invoice_description: Optional[str] = Field(None, max_length=30)
    mobile_description: Optional[str] = Field(None, max_length=255)
    marketing_description: Optional[str] = Field(None, max_length=500)
    class_name: Optional[str] = Field(None, max_length=100)
    fine_class: Optional[str] = Field(None, max_length=100)
    application: Optional[str] = Field(None, max_length=200)
    material: Optional[str] = Field(None, max_length=80)
    color: Optional[str] = Field(None, max_length=40)
    certifications: Optional[str] = Field(None, max_length=120)
    confidence_hint: Optional[float] = Field(None, ge=0.0, le=1.0)

    @field_validator("short_description")
    @classmethod
    def check_short_desc_len(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 60:
            return v[:60]
        return v

    @field_validator("invoice_description")
    @classmethod
    def check_invoice_desc_len(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 30:
            return v[:30]
        return v


# ---------------------------------------------------------------------------
# Enriched Product Record  (internal pipeline record)
# ---------------------------------------------------------------------------

class EnrichedProduct(BaseModel):
    """Full internal record after enrichment pipeline execution."""

    id: UUID = Field(default_factory=uuid4)
    status: RecordStatus = RecordStatus.RAW

    # Original fields
    mfg_part_num: Optional[str] = None
    part_desc: Optional[str] = None
    part_manuf_raw: Optional[str] = None
    e1_brand: Optional[str] = None
    unilog_brand: Optional[str] = None
    dib_brand: Optional[str] = None

    # Resolved / enriched
    manufacturer_name: Optional[str] = None
    brand_name: Optional[str] = None
    part_number: Optional[str] = None
    class_name: Optional[str] = None
    fine_class: Optional[str] = None

    # Descriptions
    short_description: Optional[str] = None
    invoice_description: Optional[str] = None
    mobile_description: Optional[str] = None
    marketing_description: Optional[str] = None

    # Attributes
    attributes: ExtractedAttributes = Field(default_factory=ExtractedAttributes)

    # Scoring
    confidence: ConfidenceMap = Field(default_factory=ConfidenceMap)

    # Audit
    enrichment_source: str = "DETERMINISTIC"  # DETERMINISTIC | LLM | HUMAN
    validation_errors: List[str] = Field(default_factory=list)
    review_notes: Optional[str] = None


# ---------------------------------------------------------------------------
# API Request / Response Bodies
# ---------------------------------------------------------------------------

class BatchEnrichResponse(BaseModel):
    job_id: str
    status: str
    total_records: int
    message: str


class ProductListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Dict[str, Any]]


class ReviewRequest(BaseModel):
    """Human override payload for HITL queue."""
    manufacturer_name: Optional[str] = Field(None, max_length=120)
    brand_name: Optional[str] = Field(None, max_length=80)
    part_number: Optional[str] = Field(None, max_length=80)
    short_description: Optional[str] = Field(None, max_length=60)
    invoice_description: Optional[str] = Field(None, max_length=30)
    class_name: Optional[str] = Field(None, max_length=100)
    fine_class: Optional[str] = Field(None, max_length=100)
    attributes: Optional[Dict[str, Any]] = None
    review_notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("short_description")
    @classmethod
    def validate_short_desc(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 60:
            raise ValueError("short_description must be <= 60 characters")
        return v

    @field_validator("invoice_description")
    @classmethod
    def validate_invoice_desc(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 30:
            raise ValueError("invoice_description must be <= 30 characters")
        return v


class EvaluationMetrics(BaseModel):
    manufacturer_accuracy: float
    brand_accuracy: float
    attribute_accuracy: float
    description_compliance: float
    overall_field_accuracy: float
    total_evaluated: int
    matched_records: int


# ---------------------------------------------------------------------------
# 252-Column Delivery Output Schema
# ---------------------------------------------------------------------------

# All 252 canonical column names in order
DELIVERY_COLUMNS: List[str] = [
    "PART_NUMBER", "Mfg_Part_Num", "MANUFACTURER_NAME", "BRAND_NAME",
    "Part_Desc", "Short_Desc", "Invoice_Desc", "Mobile_Desc", "Marketing_Desc",
    "Class", "Fine", "Sub_Class", "Product_Type",
    "Attr_Grit", "Attr_Abrasive_Material", "Attr_Backing_Material",
    "Attr_Bond_Type", "Attr_Grade", "Attr_Application",
    "Attr_Length_Value", "Attr_Length_UOM",
    "Attr_Width_Value", "Attr_Width_UOM",
    "Attr_Diameter_Value", "Attr_Diameter_UOM",
    "Attr_Thickness_Value", "Attr_Thickness_UOM",
    "Attr_Height_Value", "Attr_Height_UOM",
    "Attr_Pkg_Qty", "Attr_Pkg_UOM",
    "Attr_Voltage", "Attr_Amperage", "Attr_Wattage",
    "Attr_Material", "Attr_Finish", "Attr_Color",
    "Attr_Series", "Attr_Model_Number",
    "Attr_Certifications", "Attr_Country_Of_Origin",
    "Attr_Compatible_With",
    # UOM fields
    "UOM_Order", "UOM_Price", "UOM_Weight", "UOM_Cube",
    "Weight_Value", "Cube_Value",
    # Identifiers
    "UPC_Code", "GTIN", "EAN", "ISBN",
    "Vendor_Part_Number", "Customer_Part_Number",
    "Alternate_Part_Number_1", "Alternate_Part_Number_2",
    # Pricing
    "List_Price", "Cost", "MSRP", "MAP_Price",
    "Price_Break_1_Qty", "Price_Break_1_Price",
    "Price_Break_2_Qty", "Price_Break_2_Price",
    "Price_Break_3_Qty", "Price_Break_3_Price",
    # Status / Lifecycle
    "Status", "Lifecycle_Stage", "Date_Added", "Date_Modified",
    "Discontinue_Date", "Available_Date",
    # Logistics
    "Lead_Time_Days", "Min_Order_Qty", "Order_Multiple",
    "Ship_Weight", "Ship_Length", "Ship_Width", "Ship_Height",
    "Freight_Class", "Hazmat_Flag", "Country_Of_Origin",
    # Taxonomy
    "UNSPSC_Code", "UNSPSC_Desc",
    "Taxonomy_Level_1", "Taxonomy_Level_2", "Taxonomy_Level_3",
    "Taxonomy_Level_4", "Taxonomy_Level_5",
    # Rich content
    "Image_URL_1", "Image_URL_2", "Image_URL_3",
    "Document_URL_1", "Document_URL_2",
    "Video_URL",
    # Compliance
    "RoHS_Compliant", "Prop65_Flag", "Safety_Data_Sheet_URL",
    "Compliance_Notes",
    # Marketing
    "Search_Keywords", "SEO_Title", "SEO_Description",
    "Feature_Bullet_1", "Feature_Bullet_2", "Feature_Bullet_3",
    "Feature_Bullet_4", "Feature_Bullet_5",
    # Supplier
    "Supplier_ID", "Supplier_Name", "Supplier_Part_Num",
    "Catalog_Page", "Catalog_Section",
    # Extended attributes (generic slots 1-100 to reach 252 total)
] + [f"Ext_Attr_{i:03d}" for i in range(1, 141)]


class DeliveryRow(BaseModel):
    """One row of the 252-column delivery CSV. All fields default to ''."""

    model_config = {"extra": "allow", "populate_by_name": True}

    # Seed with empty strings for all columns
    @model_validator(mode="before")
    @classmethod
    def fill_delivery_defaults(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        for col in DELIVERY_COLUMNS:
            data.setdefault(col, "")
        return data

