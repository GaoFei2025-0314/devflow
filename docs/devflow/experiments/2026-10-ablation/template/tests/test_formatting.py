import unittest

from invoice.formatting import format_money


class FormattingTests(unittest.TestCase):
    def test_format(self):
        self.assertEqual(format_money(1234.5), "$1,234.50")


if __name__ == "__main__":
    unittest.main()
