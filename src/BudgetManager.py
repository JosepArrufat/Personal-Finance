from dataclasses import dataclass, field
from datetime import date
from typing import Dict
import json
import os
import pandas as pd

from Budget import Budget

DEFAULT_BUDGETS_PATH = os.path.join(os.path.dirname(__file__), "budgets.json")

@dataclass
class BudgetManager:
    budgets: Dict[str, Budget] = field(default_factory=dict)
    def get_budget(self, name: str) ->  Budget:
        return self.budgets[name]
    def get_budgets(self) -> Dict[str, Budget]:
        return self.budgets
    def add_or_update_budget(self, budget: Budget):
        self.budgets[budget.name] = budget
    def load_all(self, file_path: str = DEFAULT_BUDGETS_PATH) -> None:
        if not os.path.exists(file_path):
            print(f"No budgets file at {file_path}, starting empty")
            self.budgets = {}
            return
        try:
            with open(file_path, "r") as f:
                data = json.load(f) or {}
            loaded_budgets: Dict[str, Budget] = {}
            if isinstance(data, dict):
                items = data.items()
            elif isinstance(data, list):
                items = ((d.get("name") or f"budget_{i}", d) for i, d in enumerate(data))
            for key, budget_dict in items:
                try:
                    if hasattr(Budget, "from_dict") and callable(getattr(Budget, "from_dict")):
                        bobj = Budget.from_dict(budget_dict)
                    else:
                        bobj = Budget(**budget_dict)
                    loaded_budgets[bobj.name or key] = bobj
                except Exception as e:
                    print(f"Skipping budget '{key}': {e}")
            self.budgets = loaded_budgets
            print("Loaded budgets successfully")
        except Exception as e:
            print(f"Error loading Budgets data: {e}")
            self.budgets = {}
    def save_budget(self, budget: Budget, file_path: str = DEFAULT_BUDGETS_PATH) -> None:
        try:
            if hasattr(budget, "to_dict") and callable(getattr(budget, "to_dict")):
                serial = budget.to_dict()
            else:
                from dataclasses import asdict
                serial = asdict(budget)
                for fld in ("start_date", "end_date"):
                    if fld in serial and isinstance(serial[fld], date):
                        serial[fld] = serial[fld].isoformat()

            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
            existing: Dict[str, dict] = {}
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r") as f:
                        existing = json.load(f) or {}
                except Exception:
                    existing = {}

            key = getattr(budget, "name", None)
            if not key:
                raise ValueError("Budget object must have a 'name' attribute")

            existing[key] = serial

            tmp_path = f"{file_path}.tmp"
            with open(tmp_path, "w") as f:
                json.dump(existing, f, indent=2, default=str)
            os.replace(tmp_path, file_path)

            self.budgets[key] = budget
            print(f"Saved budget '{key}' successfully")
        except Exception as e:
            print(f"There was an error saving budget: {e}")
    def delete_budget(self, name: str) -> None:
        try:
            file_path = DEFAULT_BUDGETS_PATH
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)

            existing: dict = {}
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r") as f:
                        existing = json.load(f) or {}
                except Exception:
                    existing = {}

            if isinstance(existing, list):
                existing = { (d.get("name") or f"budget_{i}"): d for i, d in enumerate(existing) }

            if name in existing:
                existing.pop(name, None)

            tmp_path = f"{file_path}.tmp"
            with open(tmp_path, "w") as f:
                json.dump(existing, f, indent=2, default=str)
            os.replace(tmp_path, file_path)

            print(f"Deleted budget '{name}' from memory and '{file_path}'")
        except KeyError:
            raise KeyError(f"No budget named '{name}'")
        except Exception as e:
            print(f"Error deleting budget '{name}': {e}")

    def apply_budgets_to_transactions(self, df_master, id_col: str = "tx_id") -> None:
        if df_master is None:
            return
        if id_col not in df_master.columns:
            try:
                import hashlib
                def make_tx_id(r):
                    date_part = r.get("Date")
                    amount_part = r.get("Amount")
                    details_part = r.get("Details") if "Details" in r.index else ""
                    s = f"{date_part!s}|{amount_part!s}|{details_part!s}"
                    return hashlib.sha1(s.encode("utf-8")).hexdigest()
                df_master = df_master.reset_index(drop=True)
                df_master[id_col] = df_master.apply(make_tx_id, axis=1)
            except Exception:
                df_master[id_col] = [str(i) for i in range(len(df_master))]

        for b in self.budgets.values():
            b.transactions = pd.DataFrame()

        for b in self.budgets.values():
            if getattr(b, "tx_ids", None):
                sel = df_master[df_master[id_col].isin(b.tx_ids)].copy()
                b.transactions = sel.reset_index(drop=True)
        budgets_without_ids = [b for b in self.budgets.values() if not getattr(b, "tx_ids", None)]
        if budgets_without_ids:
            for b in budgets_without_ids:
                b.transactions = pd.DataFrame()

            for _, row in df_master.iterrows():
                for b in budgets_without_ids:
                    try:
                        b.add_transaction(row)
                    except Exception:
                        continue

        for b in self.budgets.values():
            if not b.transactions.empty and id_col in b.transactions.columns:
                try:
                    b.tx_ids = b.transactions[id_col].astype(str).tolist()
                except Exception:
                    b.tx_ids = []
            else:
                b.tx_ids = getattr(b, "tx_ids", []) or []

    