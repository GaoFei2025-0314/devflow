from dataclasses import dataclass


@dataclass
class LineItem:
    name: str
    unit_price: float
    quantity: int


def subtotal(items):
    return round(sum(i.unit_price * i.quantity for i in items), 2)


def apply_discount(amount, discount_pct):
    """Apply a percentage discount to an amount."""
    return round(amount * (1 - discount_pct / 100), 2)


def apply_tax(amount, tax_rate):
    return round(amount * (1 + tax_rate), 2)


def total(items, discount_pct=0, tax_rate=0.0):
    return apply_tax(apply_discount(subtotal(items), discount_pct), tax_rate)
