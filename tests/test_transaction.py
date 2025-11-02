import sys
import pathlib
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from Transaction import Transaction

class TestTransaction(unittest.TestCase):
    def test_basic_mutations(self):
        t = Transaction("2025-10-01", "Lunch", 12.5, "EUR", "debit")
        self.assertEqual(t.category, "Undefined")
        self.assertEqual(t.tag, "Undefined")

        t.change_category("food")
        self.assertEqual(t.category, "food")

        t.add_tag("dining")
        self.assertEqual(t.tag, "dining")

    def test_init_values(self):
        t = Transaction("2025-01-01", "Shop", 5.0, "USD", "debit", category="groceries", tag="food")
        self.assertEqual(t.category, "groceries")
        self.assertEqual(t.tag, "food")

    def test_multiple_mutations(self):
        t = Transaction("2025-02-02", "Coffee", 3.0, "EUR", "debit")
        t.change_category("beverages")
        t.add_tag("morning")
        t.add_tag("work")
        # last add_tag replaces tag (class stores single tag), ensure last value set
        self.assertEqual(t.tag, "work")
        self.assertEqual(t.category, "beverages")

    def test_string_fields(self):
        t = Transaction("2025-03-03", "Gym", 20.0, "EUR", "debit")
        # ensure attributes are stored as provided types
        self.assertIsInstance(t.details, str)
        self.assertIsInstance(t.amount, (int, float))

    def test_tag_overwrite_behavior(self):
        t = Transaction("2025-04-04", "Snack", 2.5, "EUR", "debit")
        t.add_tag("a")
        t.add_tag("b")
        # ensure tag was overwritten by last add_tag call
        self.assertEqual(t.tag, "b")


if __name__ == "__main__":
    unittest.main()

