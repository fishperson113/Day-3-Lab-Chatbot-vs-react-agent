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

def get_order_weight(order_id: str) -> str:
    """
    TODO (Person B): Implement logic to retrieve order weight.
    1. Search for order_id in MOCK_ORDERS.
    2. Return weight as a string if found, else return error message.
    """
    # Placeholder for Person B
    return "Weight result placeholder"

def calculate_shipping(weight: float, province: str) -> str:
    """
    TODO (Person B): Implement shipping calculation logic.
    Formula: weight * 5000 (standard) or weight * 10000 (express/remote).
    """
    # Placeholder for Person B
    return "Shipping cost placeholder"

def check_stock(item_name: str) -> str:
    """
    TODO (Person B): Implement stock checking logic.
    """
    # Placeholder for Person B
    return "Stock status placeholder"

# Mapping for the Agent to call
TOOLS_MAPPING = {
    "get_order_weight": get_order_weight,
    "calculate_shipping": calculate_shipping,
    "check_stock": check_stock
}
