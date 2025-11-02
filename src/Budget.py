from dataclasses import dataclass, field
from datetime import date
from datetime import datetime, date
from typing import Iterable, Literal
from dataclasses import asdict
import pandas as pd

@dataclass
class BudgetLine:
    category: str = ""
    include_tags: tuple[str, ...] = ()
    exclude_tags: tuple[str, ...] = ()

    def matches(self, row: pd.Series) -> bool:
        tx_category = row.get("Category", "").lower()
        raw_tags = row.get("tags", ())
        if isinstance(raw_tags, str):
            tx_tags = [t.strip().lower() for t in raw_tags.split(",") if t.strip()]
        elif isinstance(raw_tags, (list, tuple)):
            tx_tags = [str(t).strip().lower() for t in raw_tags if str(t).strip()]
        else:
            tx_tags = []
        exclude_lower = {str(t).lower() for t in (self.exclude_tags or [])}
        include_lower = {str(t).lower() for t in (self.include_tags or [])}

        if exclude_lower and any(t in exclude_lower for t in tx_tags):
            return False
        if include_lower and any(t in include_lower for t in tx_tags):
            return True
        if self.category:
            return tx_category == self.category.lower()
        return True

@dataclass
class Budget:
    name:str
    start_date: date
    end_date: date
    limit: float
    budget_lines: list[BudgetLine] = field(default_factory=list)
    transactions: pd.DataFrame = field(default_factory=lambda: pd.DataFrame())
    tx_ids: list[str] = field(default_factory=list)
    
    def add_line(self, line: BudgetLine) -> None:
        self.budget_lines.append(line)
    def add_transaction(self, row: pd.Series) -> None:
        tx_date = row.get("Date")
        if isinstance(tx_date, pd.Timestamp):
            tx_date = tx_date.date()
        elif isinstance(tx_date, datetime):
            tx_date = tx_date.date()
        elif isinstance(tx_date, date):
            pass
        elif isinstance(tx_date, str):
            try:
                tx_date = datetime.strptime(tx_date, "%Y-%m-%d").date()
            except ValueError:
                print(f"Skipping row due to invalid date")
                return
        else:
            print(f"Skipping row due to invalid date")
            return
        row_match = self.assign_line(row)
        if not row_match:
            return
        if row_match:
            print(row)
        start = self.start_date if isinstance(self.start_date, date) else self.start_date.date()
        end = self.end_date if isinstance(self.end_date, date) else self.end_date.date()
        
        if start <= tx_date <= end:
            if self.transactions.empty:
                self.transactions = pd.DataFrame([row])
            else:
                self.transactions = pd.concat(
                    [self.transactions, 
                    pd.DataFrame([row])], 
                    ignore_index=True
                )
    def assign_line(self, row: pd.Series) -> BudgetLine | None:
        for line in self.budget_lines:
            if line.matches(row):
                return line
        return None
    def total_spent(self) -> float: #transactions is all of them and no filter
        return self.transactions["Amount"].sum() if not self.transactions.empty else 0.0
    def per_category_spent(self) -> dict[str, float]:
        spent: dict[str, float] = {}
        for _, row in self.transactions.iterrows():
            line = self.assign_line(row)
            if not line:
                continue
            spent[line.category] = spent.get(line.category, 0.0) + row["Amount"]
        return spent
    def per_tag_spent(self) -> dict[str, float]:
        spent: dict[str, float] = {}
        for _, row in self.transactions.iterrows():
            line = self.assign_line(row)
            if not line:
                continue
            tags = row.get("tags", ())
            for tag in tags:
                spent[tag] = spent.get(tag, 0.0) + row["Amount"]
        return spent
    def get_transactions(self) -> pd.DataFrame:
        return self.transactions
    def get_num_transactions(self) -> int:
        return len(self.tx_ids)
    def to_dict(self) -> dict:
        data = {
            "name": self.name,
            "start_date": self.start_date.isoformat() if isinstance(self.start_date, date) else self.start_date,
            "end_date": self.end_date.isoformat() if isinstance(self.end_date, date) else self.end_date,
            "limit": self.limit,
            "budget_lines": [asdict(bl) for bl in self.budget_lines],
            "tx_ids": list(self.tx_ids) if self.tx_ids else [],
        }
        return data

    def summary(self) -> dict:
        total = self.total_spent()
        remaining = self.limit - total
        return {
            "limit": self.limit,
            "total_spent": total,
            "remaining": remaining,
            "is_exceeded": total > self.limit,
            "per_category_spent": self.per_category_spent(),
            "per_tag_spent": self.per_tag_spent()
        }
    @classmethod
    def from_dict(cls, d: dict) -> "Budget":
        sd = d.get("start_date")
        ed = d.get("end_date")
        try:
            if isinstance(sd, str):
                sd = date.fromisoformat(sd)
            if isinstance(ed, str):
                ed = date.fromisoformat(ed)
        except Exception:
            pass

        lines = []
        for bl in d.get("budget_lines", []):
            try:
                lines.append(BudgetLine(**bl))
            except Exception:
                continue
        b = cls(
            name=d.get("name", ""),
            start_date=sd,
            end_date=ed,
            limit=d.get("limit", 0.0),
            budget_lines=lines,
        )
        b.transactions = pd.DataFrame()
        b.tx_ids = d.get("tx_ids", []) or []
        return b
    
    