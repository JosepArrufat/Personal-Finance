import sys
import pathlib
import json
import unittest
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from Budget import Budget
import BudgetManager as bm_mod


class TestBudgetManager(unittest.TestCase):
    def test_save_and_load_budget(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_file = f"{d}/budgets.json"
            mgr = bm_mod.BudgetManager()
            b = Budget(
                name="mgr_test",
                start_date=__import__('datetime').date(2025, 1, 1),
                end_date=__import__('datetime').date(2025, 12, 31),
                limit=500.0,
            )
            mgr.save_budget(b, file_path=tmp_file)
            self.assertTrue(pathlib.Path(tmp_file).exists())

            mgr2 = bm_mod.BudgetManager()
            mgr2.load_all(file_path=tmp_file)
            self.assertIn("mgr_test", mgr2.get_budgets())
            loaded = mgr2.get_budget("mgr_test")
            self.assertEqual(loaded.name, "mgr_test")

    def test_delete_budget(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_file = f"{d}/budgets.json"
            mgr = bm_mod.BudgetManager()
            b = Budget(
                name="to_delete",
                start_date=__import__('datetime').date(2025, 1, 1),
                end_date=__import__('datetime').date(2025, 12, 31),
                limit=10.0,
            )
            mgr.save_budget(b, file_path=tmp_file)
            setattr(bm_mod, "DEFAULT_BUDGETS_PATH", tmp_file)
            with open(tmp_file, "r") as f:
                data = json.load(f)
            self.assertIn("to_delete", data)

            mgr.delete_budget("to_delete")
            with open(tmp_file, "r") as f:
                data2 = json.load(f)
            self.assertNotIn("to_delete", data2)

    def test_add_or_update_and_get_budget(self):
        mgr = bm_mod.BudgetManager()
        b = Budget(
            name="addtest",
            start_date=__import__('datetime').date(2025, 1, 1),
            end_date=__import__('datetime').date(2025, 12, 31),
            limit=123.0,
        )
        mgr.add_or_update_budget(b)
        self.assertIn("addtest", mgr.get_budgets())
        got = mgr.get_budget("addtest")
        self.assertEqual(got.limit, 123.0)

    def test_apply_budgets_populates_transactions(self):
        mgr = bm_mod.BudgetManager()
        import pandas as pd
        b = Budget(
            name="popp",
            start_date=__import__('datetime').date(2025, 1, 1),
            end_date=__import__('datetime').date(2025, 12, 31),
            limit=1000.0,
        )
        b.tx_ids = ["a1", "b2"]
        mgr.add_or_update_budget(b)

        df = pd.DataFrame([
            {"Date": "2025-01-01", "Amount": 10.0, "Details": "x", "tx_id": "a1"},
            {"Date": "2025-01-02", "Amount": 20.0, "Details": "y", "tx_id": "b2"},
            {"Date": "2025-01-03", "Amount": 30.0, "Details": "z", "tx_id": "c3"},
        ])

        mgr.apply_budgets_to_transactions(df_master=df)
        got = mgr.get_budget("popp")
        self.assertFalse(got.transactions.empty)
        self.assertEqual(set(got.transactions["tx_id"].astype(str).tolist()), {"a1", "b2"})

    def test_save_budget_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_file = f"{d}/budgets.json"
            mgr = bm_mod.BudgetManager()
            b1 = Budget(
                name="ov",
                start_date=__import__('datetime').date(2025, 1, 1),
                end_date=__import__('datetime').date(2025, 12, 31),
                limit=10.0,
            )
            mgr.save_budget(b1, file_path=tmp_file)
            b2 = Budget(
                name="ov",
                start_date=__import__('datetime').date(2025, 1, 1),
                end_date=__import__('datetime').date(2025, 12, 31),
                limit=99.0,
            )
            mgr.save_budget(b2, file_path=tmp_file)
            mgr2 = bm_mod.BudgetManager()
            mgr2.load_all(file_path=tmp_file)
            self.assertEqual(mgr2.get_budget("ov").limit, 99.0)


if __name__ == "__main__":
    unittest.main()
