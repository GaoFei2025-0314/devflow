"""Reproduce totals for archived invoices (finance audit)."""
import json
import sys

from legacy.old_calc import legacy_total


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as handle:
        print(legacy_total(json.load(handle)))
