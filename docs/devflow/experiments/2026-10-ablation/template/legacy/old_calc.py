"""Pre-2025 total calculation. Still used by scripts/monthly_report.py for
historical invoices that must be reproduced exactly."""


def legacy_total(rows):
    return sum(row["price"] * row["qty"] for row in rows)
