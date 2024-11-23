from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, 
    QHBoxLayout, QPushButton, QWidget, QMessageBox, QDialog, QFormLayout, QLineEdit, QLabel
)


class ItemDetailManager(QMainWindow):
    def __init__(self, db_handler, po_number):
        super().__init__()
        self.db_handler = db_handler
        self.po_number = po_number
        self.setWindowTitle(f"Item Details - {po_number}")
        self.resize(900, 500)

        # Main widget and layout
        main_widget = QWidget(self)
        main_layout = QVBoxLayout(main_widget)

        # Table to display items
        self.table = QTableWidget(self)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Cart Part No", "Country of Origin", "A/Unit", "Qty",
            "Rate Include GST", "Nomenclature", "Delivered Qty", "Remaining Qty"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.table)

        # Buttons for actions
        button_layout = QHBoxLayout()
        update_button = QPushButton("Update Delivery Info")
        update_button.clicked.connect(self.update_delivery_info)
        status_button = QPushButton("Update Item Status")
        status_button.clicked.connect(self.update_item_status)
        button_layout.addWidget(update_button)
        button_layout.addWidget(status_button)
        main_layout.addLayout(button_layout)

        self.setCentralWidget(main_widget)
        self.load_items()

    def load_items(self):
        """Load items into the table."""
        query = "SELECT * FROM Items WHERE po_number = %s"
        items = self.db_handler.fetch_query(query, (self.po_number,))

        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(item["cart_part_no"]))
            self.table.setItem(row, 1, QTableWidgetItem(item["country_of_origin"]))
            self.table.setItem(row, 2, QTableWidgetItem(item["a_unit"]))
            self.table.setItem(row, 3, QTableWidgetItem(str(item["qty"])))
            self.table.setItem(row, 4, QTableWidgetItem(f"{item['rate_include_gst']:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(item["nomenclature"]))
            self.table.setItem(row, 6, QTableWidgetItem(str(item["delivered_qty"])))
            self.table.setItem(row, 7, QTableWidgetItem(str(item["remaining_qty"])))

    def get_selected_row(self):
        """Get the currently selected row."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select an item.")
            return None
        return self.table.row(selected_items[0])

    def update_delivery_info(self):
        row = self.get_selected_row()
        if row is not None:
            cart_part_no = self.table.item(row, 0).text()
            self.show_delivery_info_dialog(cart_part_no)

    def show_delivery_info_dialog(self, cart_part_no):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Delivery Info - {cart_part_no}")
        dialog.resize(400, 300)

        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        challan_entry = QLineEdit()
        delivery_date_entry = QLineEdit()
        delivered_qty_entry = QLineEdit()

        form_layout.addRow("Challan Number:", challan_entry)
        form_layout.addRow("Delivery Date:", delivery_date_entry)
        form_layout.addRow("Delivered Quantity:", delivered_qty_entry)

        layout.addLayout(form_layout)

        save_button = QPushButton("Save Delivery Info")
        save_button.clicked.connect(lambda: self.save_delivery_info(
            dialog, cart_part_no, challan_entry.text(), delivery_date_entry.text(), delivered_qty_entry.text()
        ))
        layout.addWidget(save_button)
        dialog.exec_()

    def save_delivery_info(self, dialog, cart_part_no, challan_no, delivery_date, delivered_qty):
        if not challan_no or not delivery_date or not delivered_qty:
            QMessageBox.warning(self, "Invalid Input", "Please fill in all fields.")
            return

        query = """UPDATE Items 
                   SET challan_number = %s, delivery_date = %s, delivered_qty = %s 
                   WHERE cart_part_no = %s AND po_number = %s"""
        self.db_handler.execute_query(query, (challan_no, delivery_date, delivered_qty, cart_part_no, self.po_number))
        QMessageBox.information(self, "Success", "Delivery Info updated successfully.")
        dialog.accept()
        self.load_items()

    def update_item_status(self):
        row = self.get_selected_row()
        if row is not None:
            cart_part_no = self.table.item(row, 0).text()
            self.show_item_status_dialog(cart_part_no)

    def show_item_status_dialog(self, cart_part_no):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Item Status - {cart_part_no}")
        dialog.resize(400, 300)

        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        remaining_qty_entry = QLineEdit()
        approved_qty_entry = QLineEdit()
        rejected_qty_entry = QLineEdit()

        form_layout.addRow("Remaining Quantity:", remaining_qty_entry)
        form_layout.addRow("Approved Quantity:", approved_qty_entry)
        form_layout.addRow("Rejected Quantity:", rejected_qty_entry)

        layout.addLayout(form_layout)

        save_button = QPushButton("Save Item Status")
        save_button.clicked.connect(lambda: self.save_item_status(
            dialog, cart_part_no, remaining_qty_entry.text(), approved_qty_entry.text(), rejected_qty_entry.text()
        ))
        layout.addWidget(save_button)
        dialog.exec_()

    def save_item_status(self, dialog, cart_part_no, remaining_qty, approved_qty, rejected_qty):
        if not remaining_qty or not approved_qty or not rejected_qty:
            QMessageBox.warning(self, "Invalid Input", "Please fill in all fields.")
            return

        query = """UPDATE Items 
                   SET remaining_qty = %s, approved_qty = %s, rejected_qty = %s 
                   WHERE cart_part_no = %s AND po_number = %s"""
        self.db_handler.execute_query(query, (remaining_qty, approved_qty, rejected_qty, cart_part_no, self.po_number))
        QMessageBox.information(self, "Success", "Item Status updated successfully.")
        dialog.accept()
        self.load_items()
