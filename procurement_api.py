from fastapi import FastAPI, Query
from faker import Faker
import random
from datetime import datetime, timedelta

app = FastAPI(title="Packing Department Procurement API")
fake = Faker()

# Frequent suppliers and packing-related items
frequent_suppliers = ["SUPP_PACK_01", "SUPP_PACK_02", "SUPP_PACK_03"]

# Static product catalog with product IDs
material_catalog = [
    {"description": "Corn", "material_group": "GRAIN", "unit": "KG", "unit_price_range": (1.2, 1.6)},
    {"description": "Soybean Meal", "material_group": "MEAL", "unit": "KG", "unit_price_range": (2.0, 2.5)},
    {"description": "Alfalfa", "material_group": "FORAGE", "unit": "KG", "unit_price_range": (0.8, 1.2)},
    {"description": "Wheat Bran", "material_group": "BYPROD", "unit": "KG", "unit_price_range": (0.5, 0.9)},
    {"description": "Canola Seeds", "material_group": "OILSEED", "unit": "KG", "unit_price_range": (1.8, 2.3)},
    {"description": "Barley Grain", "material_group": "GRAIN", "unit": "KG", "unit_price_range": (1.0, 1.4)},
    {"description": "Rumen Protected Fat", "material_group": "ADD", "unit": "KG", "unit_price_range": (3.0, 4.5)},
    {"description": "Molasses", "material_group": "ADD", "unit": "L", "unit_price_range": (0.6, 1.0)}
]


YEAR_2025_START = datetime(2025, 1, 1)
YEAR_2025_END = datetime(2025, 12, 31)

# Generate realistic item (linked to catalog)
def generate_packing_item(item_number: int, created_date: datetime):
    product = random.choice(material_catalog)
    if created_date.month in [1, 2]:
        product = material_catalog[0]  # e.g., Corn appears in Jan/Feb
    elif created_date.month in [3, 4]:
        product = material_catalog[1] 
    quantity = float(random.randint(500, 5000))  # bulk volumes
    unit_price = round(random.uniform(*product["unit_price_range"]), 2)
    net_value = round(quantity * unit_price, 2)
    gross_value = round(net_value * 1.15, 2)

    return {
        "item_number": int(item_number),
        "product_id": f"MAT-{abs(hash(product['description'])) % 10000}",  # stable product_id
        "description": product["description"],
        "plant": f"PLANT{random.randint(1,3):03d}",
        "material_group": product["material_group"],
        "quantity": quantity,
        "unit": product["unit"],
        "unit_price": unit_price,
        "net_value": net_value,
        "gross_value": gross_value,
        "effective_value": net_value,
        "month": created_date.strftime("%B")  # for SKU frequency later
    }

# Generate a single PO
def generate_po(po_id: int):
    supplier_id = random.choices(
        frequent_suppliers + [f"SUPP_PACK_{str(i).zfill(2)}" for i in range(4, 10)],
        weights=[5,5,5] + [1]*6, k=1
    )[0]

    num_items = random.randint(2, 5)

    created_date = fake.date_between_dates(date_start=YEAR_2025_START, date_end=YEAR_2025_END)
    month = created_date.month

    items = [generate_packing_item((i+1)*10, created_date) for i in range(num_items)]
    total_value = round(sum(item["net_value"] for item in items), 2)

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
