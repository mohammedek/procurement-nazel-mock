from fastapi import FastAPI, Query
from faker import Faker
import random
from datetime import datetime, timedelta

app = FastAPI(title="Dynamic Procurement API")
fake = Faker()

# Frequent suppliers and items
frequent_suppliers = ["SUPP001", "SUPP002", "SUPP003"]
common_items = [
    {"description": "Office Paper", "material_group": "OFFICE"},
    {"description": "Laptop", "material_group": "IT"},
    {"description": "Cardamom Pack", "material_group": "RAW"},
    {"description": "Pen Set", "material_group": "OFFICE"},
    {"description": "Printer Ink", "material_group": "OFFICE"}
]

# Generate random item if not in common_items
def generate_random_item(item_number: int):
    quantity = random.randint(1, 500)
    unit_price = round(random.uniform(50, 500), 2)
    net_value = round(quantity * unit_price, 2)
    gross_value = round(net_value * 1.15, 2)  # VAT 15%
    item_template = random.choice(common_items)
    return {
        "item_number": item_number,
        "description": item_template["description"],
        "plant": f"PLANT{random.randint(1,5):03d}",
        "material_group": item_template["material_group"],
        "quantity": quantity,
        "unit": "EA",
        "unit_price": unit_price,
        "net_value": net_value,
        "gross_value": gross_value,
        "effective_value": net_value
    }

# Generate a single purchase order
def generate_po(po_id: int):
    supplier_id = random.choices(
        frequent_suppliers + [f"SUPP{str(i).zfill(3)}" for i in range(4, 20)],
        weights=[5, 5, 5] + [1]*16, k=1
    )[0]

    num_items = random.randint(1, 4)
    items = [generate_random_item((i+1)*10) for i in range(num_items)]
    total_value = sum(item["net_value"] for item in items)

    return {
        "purchase_order_id": f"PO-2025-{po_id:04d}",
        "company_code": random.choice(["1000", "2000"]),
        "doc_category": "F",
        "doc_type": random.choice(["ZLP1", "NB", "FO"]),
        "status": random.choice(["Released", "Pending", "Approved"]),
        "created_date": str(fake.date_between(start_date="-1y", end_date="today")),
        "created_by": fake.user_name(),
        "last_modified": str(fake.date_between(start_date="-1y", end_date="today")),
        "supplier_id": supplier_id,
        "purchasing_org": f"ORG{random.randint(1000, 9999)}",
        "purchasing_group": f"GRP{random.randint(100, 999)}",
        "total_value": round(total_value, 2),
        "currency": random.choice(["SAR", "USD", "EUR"]),
        "items": items
    }

# API Endpoint
@app.get("/purchase-orders")
def get_purchase_orders(
    start_date: str = None,
    end_date: str = None,
    company_code: str = None,
    supplier: str = None,
    status: str = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    records = []
    for i in range(limit):
        po = generate_po(i+offset+1)
        # Apply filters
        if company_code and po["company_code"] != company_code:
            continue
        if supplier and po["supplier_id"] != supplier:
            continue
        if status and po["status"] != status:
            continue
        if start_date and po["created_date"] < start_date:
            continue
        if end_date and po["created_date"] > end_date:
            continue
        records.append(po)

    return {
        "data": records,
        "pagination": {
            "total": 1250,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < 1250
        }
    }
