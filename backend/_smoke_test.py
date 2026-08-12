"""Quick end-to-end smoke test – run from backend/ directory."""
import sys, asyncio
sys.path.insert(0, ".")

# ── Ingestion ──────────────────────────────────────────────────────────────
from app.services.ingestion_service import parse_input_csv

CSV = (
    "Mfg_Part_Num,Part_Desc,Part_Manuf,E1_Brand,Unilog_Brand,DIB_Brand\n"
    'DCB518ASTS06G,"DCB518ASTS06G Diablo 1/2\\"x18\\" Sanding Belt 6pc","Freud Inc (2435)",DIABLO,DIABLO,DIABLO\n'
    '3M-314D-P80,"3M 314D P80 Grit 4.5\\" Flap Disc 10pk","Jam Industrial Supply LLC (JAMIN)",3M,3M,-- No Unilog Brand --\n'
    'NOR-66261131655,"Norton 66261131655 SG Blaze R980 P120 Grit Abrasive Belt 1"x42"","Saint-Gobain Abrasives (SGP)",NORTON,NORTON,NORTON\n'
)

records, warnings = parse_input_csv(CSV.encode())
print(f"[INGEST] {len(records)} records parsed, {len(warnings)} warnings")
assert len(records) == 3, f"Expected 3 records, got {len(records)}"

# ── Pipeline ───────────────────────────────────────────────────────────────
from app.services.hybrid_engine import HybridEnrichmentEngine
from app.services.validator import ValidationEngine, build_export_csv

engine    = HybridEnrichmentEngine()
validator = ValidationEngine()


async def run() -> None:
    products  = await engine.process_batch(records)
    validated = [validator.validate(p) for p in products]

    print("\n[RESULTS]")
    for p in validated:
        print(
            f"  [{p.status.value:<16}] {str(p.mfg_part_num):<25} "
            f"manuf={p.manufacturer_name}  brand={p.brand_name}  "
            f"grit={p.attributes.grit}  "
            f"dims={p.attributes.width_value}x{p.attributes.length_value}  "
            f"qty={p.attributes.package_quantity}  "
            f"conf={p.confidence.overall:.3f}"
        )

    csv_out = build_export_csv(validated)
    lines   = csv_out.splitlines()
    cols    = lines[0].split(",")
    print(f"\n[EXPORT] {len(validated)} rows, {len(cols)} columns")
    assert len(cols) == 252, f"Expected 252 columns, got {len(cols)}"

    # Status checks
    statuses = {p.mfg_part_num: p.status.value for p in validated}
    print(f"[STATUS] {statuses}")

    print("\nAll smoke-test assertions PASSED")


asyncio.run(run())
