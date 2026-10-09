import unittest

from invoice.calc import LineItem, apply_discount, subtotal, total


class CalcTests(unittest.TestCase):
    def test_subtotal(self):
        items = [LineItem("a", 2.5, 2), LineItem("b", 1.0, 3)]
        self.assertEqual(subtotal(items), 8.0)

    def test_discount(self):
        self.assertEqual(apply_discount(100, 15), 85.0)

    def test_total_with_tax(self):
        self.assertEqual(total([LineItem("a", 100, 1)], 10, 0.08), 97.2)


if __name__ == "__main__":
    unittest.main()
