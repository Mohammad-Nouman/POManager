from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, 
    QHBoxLayout, QPushButton, QWidget, QMessageBox, QDialog, QFormLayout, QLineEdit, QLabel,QInputDialog
)

class PurchaseOrderManager(QMainWindow):
    def __init__(self, db_handler):
        super().__init__()
        self.db_handler = db_handler
        self.setWindowTitle("Purchase Order Management")
        self.resize(800, 400)

        # Main widget and layout
        main_widget = QWidget(self)
        main_layout = QVBoxLayout(main_widget)

        # Table to display Purchase Orders
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["PO Number", "Order Date", "Total Qty", "Total Amount"])
        self.table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.table)

        # Buttons for operations
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Purchase Order")
        add_button.clicked.connect(self.add_purchase_order)
        delete_button = QPushButton("Delete Purchase Order")
        delete_button.clicked.connect(self.delete_purchase_order)
        update_button = QPushButton("Update Purchase Order")
        update_button.clicked.connect(self.update_purchase_order)
        search_button = QPushButton("Search Purchase Order")
        search_button.clicked.connect(self.search_purchase_order)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(update_button)
        button_layout.addWidget(search_button)
        main_layout.addLayout(button_layout)

        self.setCentralWidget(main_widget)
        self.load_purchase_orders()

    def load_purchase_orders(self):
        """Load purchase orders into the table."""
        purchase_orders = self.db_handler.fetch_query("SELECT * FROM PurchaseOrder")
        self.table.setRowCount(len(purchase_orders))
        for row, po in enumerate(purchase_orders):
            self.table.setItem(row, 0, QTableWidgetItem(po["po_number"]))
            self.table.setItem(row, 1, QTableWidgetItem(po["order_date"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(po["total_qty"])))
            self.table.setItem(row, 3, QTableWidgetItem(f"{po['total_amount']:.2f}"))

    def get_selected_row(self):
        """Get the currently selected row."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a purchase order.")
            return None
        return self.table.row(selected_items[0])

    def add_purchase_order(self):
        self.edit_purchase_order_window()

    def delete_purchase_order(self):
        row = self.get_selected_row()
        if row is not None:
            po_number = self.table.item(row, 0).text()
            self.confirm_and_delete(po_number)

    def confirm_and_delete(self, po_number):
        result = QMessageBox.question(self, "Delete", f"Are you sure you want to delete Purchase Order: {po_number}?", 
                                      QMessageBox.Yes | QMessageBox.No)
        if result == QMessageBox.Yes:
            query = "DELETE FROM PurchaseOrder WHERE po_number = %s"
            self.db_handler.execute_query(query, (po_number,))
            self.table.removeRow(self.table.currentRow())
            QMessageBox.information(self, "Success", "Purchase order deleted successfully.")

    def update_purchase_order(self):
        row = self.get_selected_row()
        if row is not None:
            po_number = self.table.item(row, 0).text()
            self.edit_purchase_order_window(po_number)

    def search_purchase_order(self):
        search_query, ok = QInputDialog.getText(self, "Search", "Enter PO Number to search:")
        if ok and search_query:
            purchase_order = self.db_handler.fetch_query("SELECT * FROM PurchaseOrder WHERE po_number = %s", (search_query,))
            if purchase_order:
                self.table.clearContents()
                self.table.setRowCount(1)
                po = purchase_order[0]
                self.table.setItem(0, 0, QTableWidgetItem(po["po_number"]))
                self.table.setItem(0, 1, QTableWidgetItem(po["order_date"]))
                self.table.setItem(0, 2, QTableWidgetItem(str(po["total_qty"])))
                self.table.setItem(0, 3, QTableWidgetItem(f"{po['total_amount']:.2f}"))
            else:
                QMessageBox.warning(self, "Not Found", "No purchase order found with this PO Number.")

    def edit_purchase_order_window(self, po_number=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Purchase Order")
        dialog.resize(400, 300)

        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        po_number_entry = QLineEdit()
        if po_number:
            po_number_entry.setText(po_number)
        form_layout.addRow("PO Number:", po_number_entry)

        # Add other fields like Order Date, Total Qty, etc.
        order_date_entry = QLineEdit()
        total_qty_entry = QLineEdit()
        total_amount_entry = QLineEdit()

        form_layout.addRow("Order Date:", order_date_entry)
        form_layout.addRow("Total Qty:", total_qty_entry)
        form_layout.addRow("Total Amount:", total_amount_entry)

        layout.addLayout(form_layout)

        save_button = QPushButton("Save Changes")
        save_button.clicked.connect(lambda: self.save_purchase_order(dialog, po_number_entry.text(), order_date_entry.text(), total_qty_entry.text(), total_amount_entry.text()))
        layout.addWidget(save_button)
        dialog.exec_()

    def save_purchase_order(self, dialog, po_number, order_date, total_qty, total_amount):
        if not po_number or not order_date or not total_qty or not total_amount:
            QMessageBox.warning(self, "Invalid Input", "Please fill in all fields.")
            return

        self.db_handler.insert_purchase_order(po_number, order_date, total_qty, total_amount)
        dialog.accept()
        self.load_purchase_orders()
