import sys
import pathlib
import sys
import pathlib
import datetime
import unittest

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from Budget import Budget, BudgetLine


class TestBudget(unittest.TestCase):
    def make_row(self, date_str, amount, category="", tags=()):
        return pd.Series({
            "Date": date_str,
            "Amount": amount,
            "Category": category,
            "tags": tags,
        })

    def test_add_transaction_and_totals(self):
        b = Budget(
            name="test",
            start_date=datetime.date(2025, 1, 1),
            end_date=datetime.date(2025, 12, 31),
            limit=100.0,
            budget_lines=[BudgetLine(category="groceries")],
        )

        r = self.make_row("2025-10-01", 42.5, category="Groceries", tags=("food",))
        b.add_transaction(r)

        self.assertEqual(b.total_spent(), 42.5)
        per_cat = b.per_category_spent()
        self.assertEqual(per_cat.get("groceries", 0.0), 42.5)
        per_tag = b.per_tag_spent()
        self.assertEqual(per_tag.get("food", 0.0), 42.5)

    def test_to_from_dict_roundtrip(self):
        b = Budget(
            name="round",
            start_date=datetime.date(2025, 1, 1),
            end_date=datetime.date(2025, 6, 30),
            limit=250.0,
            budget_lines=[BudgetLine(category="entertainment")],
        )
        b.tx_ids = ["tx1", "tx2"]
        d = b.to_dict()
        self.assertEqual(d["name"], "round")
        self.assertIsInstance(d["tx_ids"], list)
        self.assertEqual(d["tx_ids"], ["tx1", "tx2"])

        b2 = Budget.from_dict(d)
        self.assertEqual(b2.name, "round")
        self.assertEqual(b2.tx_ids, ["tx1", "tx2"])

    def test_get_num_transactions_and_tx_ids(self):
        b = Budget(
            name="n",
            start_date=datetime.date(2025, 1, 1),
            end_date=datetime.date(2025, 12, 31),
            limit=10.0,
        )
        b.tx_ids = ["a", "b", "c"]
        self.assertEqual(b.get_num_transactions(), 3)

    def test_assign_line_no_match(self):
        b = Budget(
            name="empty",
            start_date=datetime.date(2025, 1, 1),
            end_date=datetime.date(2025, 12, 31),
            limit=10.0,
        )
        row = self.make_row("2025-05-01", 5, category="other", tags=("x",))
        self.assertIsNone(b.assign_line(row))

    def test_matches_with_string_tags(self):
        b = Budget(
            name="t1",
            start_date=datetime.date(2025, 1, 1),
            end_date=datetime.date(2025, 12, 31),
            limit=100.0,
            budget_lines=[BudgetLine(include_tags=("food",))],
        )
        row = self.make_row("2025-10-01", 10, category="", tags="food, coffee")
        self.assertIsNotNone(b.assign_line(row))

    def test_include_tags_override_category(self):
        b = Budget(
            name="include_override",
            start_date=datetime.date(2025, 1, 1),
            end_date=datetime.date(2025, 12, 31),
            limit=200.0,
            budget_lines=[BudgetLine(category="transport", include_tags=("food",))],
        )
        r = self.make_row("2025-10-01", 15.0, category="Groceries", tags=("food",))
        line = b.assign_line(r)
        self.assertIsNotNone(line)
        self.assertEqual(line.category, "transport")
        b.add_transaction(r)
        per_cat = b.per_category_spent()
        self.assertEqual(per_cat.get("transport", 0.0), 15.0)


if __name__ == "__main__":
    unittest.main()

