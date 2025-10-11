class Transaction():
    def __init__(self, date, details, amount, currency, type, category="Undefined", tag="Undefined"):
        self.date = date
        self.details = details
        self.amount = amount
        self.currency = currency
        self.type = type
        self.category = category
        self.tag = tag
    def change_category(self, new_category):
        self.category = new_category
    def add_tag(self, new_tag):
        self.tag = new_tag
    
    