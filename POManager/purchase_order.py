from POManager.item import Item
from datetime import datetime

class PurchaseOrder:
    def __init__(self, po_number):
        self.po_number = po_number
        self.id = 0
        self.items = []  # List to store items
        self.total_qty = 0  # Total quantity of items
        self.total_amount = 0  # Total amount of the purchase order
        self.added_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def add_item(self, item):
        if isinstance(item, Item):
            self.items.append(item)
        else:
            raise ValueError("Only Item objects can be added.")

    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)
        else:
            raise ValueError("Item not found in the purchase order.")

    def clear_items(self):
        self.items.clear()

    def to_dict(self):
        return {
            "PO Number": self.po_number,
            "Items": [item.to_dict() for item in self.items]
        }

    def __str__(self):
        return f"Purchase Order {self.po_number} with {len(self.items)} items."

    def update_purchase_order(self):
        po_data = self.db_handler.get_purchase_order_by_po_number(self.po_number)
        if po_data:
            self.total_qty = po_data['total_qty']
            self.total_amount = po_data['total_amount']
        for item in self.items:
            item.update_from_db(self.db_handler)