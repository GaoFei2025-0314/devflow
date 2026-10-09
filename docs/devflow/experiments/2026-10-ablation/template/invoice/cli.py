import argparse
import json
import sys

from .calc import LineItem, total
from .formatting import format_money


def main(argv=None):
    parser = argparse.ArgumentParser(prog="invoice")
    parser.add_argument("--items", required=True, help="JSON file with line items")
    parser.add_argument("--discount", type=float, default=0, help="discount percent")
    parser.add_argument("--tax", type=float, default=0.0, help="tax rate, e.g. 0.08")
    args = parser.parse_args(argv)
    with open(args.items, encoding="utf-8") as handle:
        items = [LineItem(**row) for row in json.load(handle)]
    print(format_money(total(items, args.discount, args.tax)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
