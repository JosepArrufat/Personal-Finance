from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, Literal

@dataclass
class Transaction:
    date: date
    amount: float
    details: str
    category: str
    debit_credit: Literal["debit", "credit"]
    tags: tuple[str, ...] = ()

@dataclass
class BudgetLine:
    category: str = ""
    include_tags: tuple[str, ...] = ()
    exclude_tags: tuple[str, ...] = ()

    def matches(self, tx: Transaction):
        if self.category and tx.category != self.category:
            return False
        if self.exclude_tags and any(t in self.exclude_tags for t in tx.tags):
            return False
        if self.include_tags:
            return any(t in self.include_tags for t in tx.tags)
        return True


@dataclass
class Budget:
    name:str
    start_date: date
    end_date: date
    limit: float
    budget_lines: list[BudgetLine] = field(default_factory=list)
    transactions: list[Transaction] = field(default_factory=list)
    
    def add_line(self, line: BudgetLine) -> None:
        self.budget_lines.append(line)
    def add_transaction(self, tx: Transaction) -> None:
        if self.start_date <= tx.date <= self.end_date:
            self.transactions.append(tx)
    def assign_line(self, tx: Transaction) -> BudgetLine | None:
        for line in self.budget_lines:
            if line.matches(tx):
                return line
        return None
    def total_spent(self) -> float:
        total = 0
        for tx in self.transactions:
            total += tx.amount
        return total
    def per_line_spent(self) -> dict[str, float]:
        spent: dict[str, float] = {}
        for tx in self.transactions:
            line = self.assign_line(tx)
            if not line:
                continue
            spent[line.category] = spent.get(line.category, 0.0) + tx.amount
        return spent
    def per_tag_spent(self) -> dict[str, float]:
        spent: dict[str, float] = {}
        for tx in self.transactions:
            for tag in tx.tags:
                spent[tag] = spent.get(tag, 0.0) + tx.amount
        return spent

    def summary(self) -> dict:
        total = self.total_spent()
        remaining = self.limit - total
        return {
            "limit": self.limit,
            "total_spent": total,
            "remaining": remaining,
            "is_exceeded": total > self.limit,
            "per_line_spent": self.per_line_spent(),
            "per_tag_spent": self.per_tag_spent()
        }
    

# # Example usage
# b = Budget("November", date(2025, 11, 1), date(2025, 11, 30), limit=800.0)
# b.add_line(BudgetLine(category="groceries"))
# b.add_line(BudgetLine(category="restaurants"))

# b.add_transaction(Transaction(date(2025, 11, 2), 32.5, "groceries", ("costco",)))
# b.add_transaction(Transaction(date(2025, 11, 7), 45.0, "restaurants", ("takeout",)))
# b.add_transaction(Transaction(date(2025, 11, 10), 10.0, "groceries", ("refund",)))

# print(b.summary()) 