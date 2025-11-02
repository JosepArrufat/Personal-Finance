import sys
import pathlib
import json
import unittest
import tempfile

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from CategoryStore import CategoryStore

class TestCategoryStore(unittest.TestCase):
    def test_load_and_add_category(self):
        with tempfile.TemporaryDirectory() as d:
            cat_file = f"{d}/categories.json"
            income_file = f"{d}/income_categories.json"
            tags_file = f"{d}/tags.json"
            open(cat_file, "w").write(json.dumps({}))
            open(income_file, "w").write(json.dumps({}))
            open(tags_file, "w").write(json.dumps({}))

            store = CategoryStore(cat_file, income_file, tags_path=tags_file)
            store.load_all()
            self.assertTrue(store.is_loaded())

            store.add_category("categories", "New Cat")
            self.assertIn("new cat", store.get_options("categories"))

    def test_tags_and_apply_to_df(self):
        with tempfile.TemporaryDirectory() as d:
            cat_file = f"{d}/categories.json"
            income_file = f"{d}/income_categories.json"
            tags_file = f"{d}/tags.json"
            open(cat_file, "w").write(json.dumps({}))
            open(income_file, "w").write(json.dumps({}))
            open(tags_file, "w").write(json.dumps({}))

            store = CategoryStore(cat_file, income_file, tags_path=tags_file)
            store.load_all()
            store.set_current_file("file1.csv")
            store.set_tags("tx1", ["groceries", "food"])
            self.assertEqual(store.get_tags("tx1"), ["groceries", "food"])

            df = pd.DataFrame([{"Date": "2025-01-01", "Details": "Buy", "Amount": 5}])
            out = store.apply_tags_to_df(df, "file1.csv")
            cols = set(out.columns)
            # support either legacy 'transaction_id' or canonical 'tx_id'
            self.assertTrue("tx_id" in cols or "transaction_id" in cols)
            self.assertIn("tags", out.columns)

    def test_get_options_and_lookup(self):
        with tempfile.TemporaryDirectory() as d:
            cat_file = f"{d}/categories.json"
            income_file = f"{d}/income_categories.json"
            tags_file = f"{d}/tags.json"
            open(cat_file, "w").write(json.dumps({"groceries": ["buy"], "uncategorized": []}))
            open(income_file, "w").write(json.dumps({}))
            open(tags_file, "w").write(json.dumps({}))

            store = CategoryStore(cat_file, income_file, tags_path=tags_file)
            store.load_all()
            opts = store.get_options("categories")
            self.assertIn("groceries", opts)
            lookup = store.get_lookup("categories")
            self.assertEqual(lookup.get("buy"), "groceries")

    def test_set_and_remove_tags_and_rebuild(self):
        with tempfile.TemporaryDirectory() as d:
            cat_file = f"{d}/c.json"
            income_file = f"{d}/i.json"
            tags_file = f"{d}/t.json"
            open(cat_file, "w").write(json.dumps({}))
            open(income_file, "w").write(json.dumps({}))
            open(tags_file, "w").write(json.dumps({}))

            store = CategoryStore(cat_file, income_file, tags_path=tags_file)
            store.load_all()
            store.set_current_file("f1.csv")
            store.set_tags("tx1", ["a", "b"])
            self.assertEqual(store.get_tags("tx1"), ["a", "b"])
            store.rebuild_tags()
            self.assertIn("a", store.tags_list)
            store.remove_tag("a", "tx1")
            self.assertNotIn("a", store.get_tags("tx1"))

    def test_get_all_tags_empty_when_no_file(self):
        with tempfile.TemporaryDirectory() as d:
            cat_file = f"{d}/c2.json"
            income_file = f"{d}/i2.json"
            tags_file = f"{d}/t2.json"
            open(cat_file, "w").write(json.dumps({}))
            open(income_file, "w").write(json.dumps({}))
            open(tags_file, "w").write(json.dumps({}))
            store = CategoryStore(cat_file, income_file, tags_path=tags_file)
            store.load_all()
            self.assertEqual(store.get_all_tags(), [])


if __name__ == "__main__":
    unittest.main()

