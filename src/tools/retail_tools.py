import json
from typing import Dict, Any

# Mock Database for Retail Use Case
MOCK_INVENTORY = {
    "iphone": {"stock": 10, "weight": 0.5},
    "macbook": {"stock": 5, "weight": 2.0},
    "ipad": {"stock": 0, "weight": 0.7}
}

MOCK_ORDERS = {
    "ORD123": {"items": ["iphone", "iphone"], "total_weight": 1.0, "province": "Hanoi"},
    "ORD456": {"items": ["macbook"], "total_weight": 2.0, "province": "HCM"}
}

INNER_CITY = ["hanoi", "hà nội", "hcm", "ho chi minh", "hồ chí minh"]

def get_order_weight(order_id: str) -> str:
    order = MOCK_ORDERS.get(order_id.upper())
    if not order:
        return f"Không tìm thấy đơn hàng {order_id}."
    return f"{order['total_weight']} kg"

def calculate_shipping(weight: float, province: str) -> str:
    rate = 5000 if province.lower() in INNER_CITY else 10000
    fee = float(weight) * rate
    return f"{int(fee)} VND"

def check_stock(item_name: str) -> str:
    item = MOCK_INVENTORY.get(item_name.lower())
    if not item:
        return f"Không tìm thấy sản phẩm '{item_name}'."
    if item["stock"] == 0:
        return "Hết hàng."
    return f"Còn {item['stock']} cái."

# Mapping for the Agent to call
TOOLS_MAPPING = {
    "get_order_weight": get_order_weight,
    "calculate_shipping": calculate_shipping,
    "check_stock": check_stock
}

# Tool descriptions for system prompt (dùng cho Person A)
TOOL_DESCRIPTIONS = [
    {
        "name": "get_order_weight",
        "description": "Trả về cân nặng của đơn hàng. Input: mã đơn hàng (ví dụ ORD123). Output: '1.0 kg'."
    },
    {
        "name": "calculate_shipping",
        "description": "Tính phí ship. Input: weight|province. Nội thành (Hanoi/HCM): weight*5000, ngoại thành: weight*10000. Output: '50000 VND'."
    },
    {
        "name": "check_stock",
        "description": "Kiểm tra tồn kho. Input: tên sản phẩm. Output: 'Còn 10 cái' hoặc 'Hết hàng'."
    },
]
