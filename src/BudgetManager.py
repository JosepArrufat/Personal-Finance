#New budget manager:
#store budget list, compare budgets, manage loading and saving
from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, Dict, Optional
import json
import os

from Budget import Budget

@dataclass
class BudgetManager:
    budgets: Dict[str, Budget]
    _dirty: bool = field(default=False, repr=False)
    def get_budget(self, name: str) ->  Budget | None:
        return self.budgets[name]
    def add_or_update_budget(self, budget: Budget):
        self.budgets[budget.name] = budget
        self._dirty = False
    def load_all(self, file_path: str = "budgets.json") -> None:    
        if not os.path.exists(file_path):
            print(f"No valid path was provided")
            return
        else:
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    loaded_budgets: Dict[str, Budget] = {}
                    for budget_dict in data:
                        budget_obj = Budget(**budget_dict)
                        loaded_budgets[budget_obj.name] = budget_obj
                    self.budgets = loaded_budgets
                    self._dirty = False
                    print(f"Loaded budgets succesfuly")
            except Exception as e:
                print(f"Error loading Budgets data: {e}")
                self.budgets = {}
    def save_all(self, file_path:str = "budgets.json") -> None:
        if not self._dirty:
            print(f"No budgets to save")
            return
        else:
            try:
                data_to_save = {name: budget.__dict__ for name, budget in self.budget.items()}
                with open(file_path, "w") as f:
                    json.dump(data_to_save, f)
                    self._dirty = False
                    print("Saved budgets succesfully")
            except Exception as e:
                print(f"There was en error saving files: {e}")
    def filter_budgets_per_date(self, start_date: Optional[date]=float("-inf"), end_date: Optional[date]=float("inf")) -> Iterable[Budget]:
        for budget in self.budgets:
            if budget.start_date >= start_date and budget.end_date <= end_date:
                yield budget
    def total_spent_line(self, line: str,start_date: Optional[date]=float("-inf"), end_date: Optional[date]=float("inf")) -> float:
        filtered_budgets = self.filter_budgets_by_date(start_date, end_date)
        return sum(budget.total_spend() for budget in self.budgets.values() if line in budget.budget_lines)
    def total_spent_tag(self, tag: str, start_date: Optional[date]=float("-inf"), end_date: Optional[date]=float("inf")) -> float:
        total_spent = 0.0
        filtered_budgets = self.filter_budgets_by_date(start_date, end_date)
        for budget in filtered_budgets.values():
            transactions = budget.transactions
            for tx in transactions:
                if tag in tx.tags:
                    total_spent += tx.amount
        return total_spent

    