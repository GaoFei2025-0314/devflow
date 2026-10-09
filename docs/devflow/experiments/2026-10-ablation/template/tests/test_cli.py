import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from invoice.cli import main


class CliTests(unittest.TestCase):
    def test_cli_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "items.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump([{"name": "a", "unit_price": 10, "quantity": 2}], handle)
            out = io.StringIO()
            with redirect_stdout(out):
                main(["--items", path, "--discount", "50"])
            self.assertEqual(out.getvalue().strip(), "$10.00")


if __name__ == "__main__":
    unittest.main()
