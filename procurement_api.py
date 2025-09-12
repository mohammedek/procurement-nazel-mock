from fastapi import FastAPI, Query
from faker import Faker
import random
from datetime import datetime, timedelta

app = FastAPI(title="Packing Department Procurement API")
fake = Faker()

# Frequent suppliers and packing-related items
frequent_suppliers = ["SUPP_PACK_01", "SUPP_PACK_02", "SUPP_PACK_03"]

# Realistic packing materials for SKU analysis
packing_items = [
    {"description": "Cardboard Box Small", "material_group": "BOX", "unit_price_range": (1.0, 3.0)},
    {"description": "Cardboard Box Large", "material_group": "BOX", "unit_price_range": (3.5, 6.0)},
    {"description": "Packing Tape", "material_group": "TAPE", "unit_price_range": (0.5, 1.5)},
    {"description": "Bubble Wrap Roll", "material_group": "WRAP", "unit_price_range": (5.0, 15.0)},
    {"description": "Plastic Straps", "material_group": "STRAP", "unit_price_range": (0.8, 2.0)},
    {"description": "Labels Pack", "material_group": "LABEL", "unit_price_range": (0.2, 1.0)},
    {"description": "Protective Foam", "material_group": "FOAM", "unit_price_range": (2.0, 10.0)}
]

YEAR_2025_START = datetime(2025, 1, 1)
YEAR_2025_END = datetime(2025, 12, 31)

# Generate realistic item
def generate_packing_item(item_number: int):
    item = random.choice(packing_items)
    quantity = float(random.randint(50, 500))  # convert to float
    unit_price = round(random.uniform(*item["unit_price_range"]), 2)
    net_value = round(quantity * unit_price, 2)
    gross_value = round(net_value * 1.15, 2)  # VAT 15%
    return {
        "item_number": int(item_number),
        "description": str(item["description"]),
        "plant": str(f"PLANT{random.randint(1,3):03d}"),
        "material_group": str(item["material_group"]),
        "quantity": float(quantity),
        "unit": "EA",
        "unit_price": float(unit_price),
        "net_value": float(net_value),
        "gross_value": float(gross_value),
        "effective_value": float(net_value)
    }

# Generate a single PO
def generate_po(po_id: int):
    supplier_id = random.choices(
        frequent_suppliers + [f"SUPP_PACK_{str(i).zfill(2)}" for i in range(4, 10)],
        weights=[5,5,5] + [1]*6, k=1
    )[0]

    num_items = random.randint(2, 5)
    items = [generate_packing_item((i+1)*10) for i in range(num_items)]
    total_value = round(sum(item["net_value"] for item in items), 2)

    created_date = fake.date_between_dates(date_start=YEAR_2025_START, date_end=YEAR_2025_END)
    last_modified = created_date + timedelta(days=random.randint(0,7))

    return {
        "purchase_order_id": f"PO-2025-{po_id:04d}",
        "company_code": "1000",
        "doc_category": "F",
        "doc_type": "ZLP1",
        "status": random.choice(["Released", "Pending", "Approved"]),
        "created_date": created_date.strftime("%Y-%m-%d"),
        "created_by": fake.user_name(),
        "last_modified": last_modified.strftime("%Y-%m-%d"),
        "supplier_id": supplier_id,
        "purchasing_org": "ORG1000",
        "purchasing_group": "GRP100",
        "total_value": float(total_value),
        "currency": "SAR",
        "items": items
    }

# API endpoint
@app.get("/purchase-orders")
def get_purchase_orders(
    start_date: str = None,
    end_date: str = None,
    supplier: str = None,
    status: str = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    records = []
    generated_count = 0
    po_id = offset + 1

    while generated_count < limit:
        po = generate_po(po_id)
        po_id += 1

        # Apply filters
        if supplier and po["supplier_id"] != supplier:
            continue
        if status and po["status"] != status:
            continue
        if start_date and po["created_date"] < start_date:
            continue
        if end_date and po["created_date"] > end_date:
            continue

        records.append(po)
        generated_count += 1

    return {
        "data": records,
        "pagination": {
            "total": 1250,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < 1250
        }
    }
