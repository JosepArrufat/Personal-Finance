class Budget():
    def __init__(self, max_expense, current_expense, name, items=[]):
        self.max_expense = max_expense
        self.current_expense = current_expense
        self.name = name
        self.transactions = items #Pass monthly transactions
    def add_transaction(self, transaction):
        self.transactions.append(transaction)
        self.current_expense += transaction.amount
    def remove_transaction(self, transaction):
        # Implement some find algorythim
        pass
    def get_current_expenses(self):
        return self.current_expense
    def get_remaining(self):
        return self.max_expense - self.current_expense
    def is_exceeded(self):
        return self.max_expense < self.current_expense
    def sort_by_type(self):
        pass
    def sort_by_date(self):
        pass
    def sort_by_amount(self):
        pass
    def sort_by_category(self):
        pass
    

