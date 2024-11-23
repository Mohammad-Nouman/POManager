from PyQt5.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QFrame,
    QTableWidget, QTableWidgetItem, QScrollBar,QMessageBox,QInputDialog, QFileDialog,QFormLayout,QGroupBox,QDialog,QWidget

)
from PyQt5.QtCore import Qt

from POManager.purchase_order import PurchaseOrder  # Importing the PurchaseOrder class
from POManager.item import Item  # Importing the Item class
from POManager.image_processor import ImageProcessor

import traceback

class PurchaseOrderApp(QWidget):
    def __init__(self, db_handler):
        super().__init__()
        self.db_handler = db_handler
        self.purchase_orders = []  # List to hold purchase orders
        self.create_widgets()  # Call the function to create UI components

        # Load the existing purchase orders from the database
        self.load_purchase_orders()

    def create_widgets(self):
        # Main layout for the widget
        main_layout = QVBoxLayout(self)

        # Title Label
        self.title_label = QLabel("Purchase Order Management")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; text-align: center;")
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)

        # Search Section
        search_frame = QFrame(self)
        search_layout = QHBoxLayout(search_frame)
        search_frame.setLayout(search_layout)
        main_layout.addWidget(search_frame)

        self.search_label = QLabel("Search Purchase Orders:")
        self.search_label.setStyleSheet("font-size: 14px;")
        search_layout.addWidget(self.search_label)

        self.search_entry = QLineEdit(self)
        self.search_entry.setPlaceholderText("Enter PO Number")
        search_layout.addWidget(self.search_entry)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_purchase_order)
        search_layout.addWidget(self.search_button)

        # Buttons Section
        button_frame = QFrame(self)
        button_layout = QHBoxLayout(button_frame)
        button_frame.setLayout(button_layout)
        main_layout.addWidget(button_frame)

        self.add_button = QPushButton("Add New Purchase Order")
        self.add_button.setFixedWidth(200)
        self.add_button.clicked.connect(self.add_purchase_order)
        button_layout.addWidget(self.add_button)

        self.update_button = QPushButton("Update Purchase Order")
        self.update_button.setFixedWidth(200)
        self.update_button.clicked.connect(self.update_purchase_order)
        button_layout.addWidget(self.update_button)

        self.delete_button = QPushButton("Delete Purchase Order")
        self.delete_button.setFixedWidth(200)
        self.delete_button.clicked.connect(self.delete_purchase_order)
        button_layout.addWidget(self.delete_button)

        # Table for displaying Purchase Orders
        self.tree = QTableWidget(self)
        self.tree.setColumnCount(5)
        self.tree.setHorizontalHeaderLabels(["ID", "PO Number", "Order Date", "Total Qty", "Total Amount"])
        self.tree.verticalHeader().setVisible(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setEditTriggers(QTableWidget.NoEditTriggers)  # Disable direct editing
        self.tree.setSelectionBehavior(QTableWidget.SelectRows)
        self.tree.setSelectionMode(QTableWidget.SingleSelection)
        self.tree.horizontalHeader().setStretchLastSection(True)  # Stretch last column
        self.tree.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)

        # Add the table to the layout
        main_layout.addWidget(self.tree)

        # Add Scrollbar to the table
        self.scrollbar = QScrollBar(Qt.Vertical, self)
        self.tree.setVerticalScrollBar(self.scrollbar)

    def load_purchase_orders(self):
        try:
            # Load all purchase orders from the database
            purchase_orders_from_db = self.db_handler.get_purchase_orders()
            for po_data in purchase_orders_from_db:
                # Debugging step: print loaded PO data
                print(f"Loading Purchase Order: {po_data}")

                # Create a PurchaseOrder object
                po = PurchaseOrder(po_data['po_number'])
                po.id = po_data['id']
                po.added_date = po_data['order_date']
                po.total_qty = po_data['total_qty']
                po.total_amount = po_data['total_amount']

                # Add the items to the PurchaseOrder object
                items_data = self.db_handler.get_items_by_purchase_order_id(po_data['id'])  # Use correct key
                for item_data in items_data:
                    item = Item(
                        cart_part_no=item_data['cart_part_no'],
                        nomenclature=item_data['nomenclature'],
                        qty=item_data['qty'],
                        rate_include_gst=item_data['rate_include_gst'],
                        country_of_origin=item_data.get('country_of_origin', ''),
                        a_unit=item_data.get('a_unit', '')
                    )
                    po.add_item(item)

                # Add the PurchaseOrder object to the local list
                self.purchase_orders.append(po)

                # Insert PurchaseOrder into the QTableWidget
                row_position = self.tree.rowCount()  # Get current row count
                self.tree.insertRow(row_position)  # Add a new row

                # Populate the row with PurchaseOrder data
                self.tree.setItem(row_position, 0, QTableWidgetItem(str(po.id)))
                self.tree.setItem(row_position, 1, QTableWidgetItem(po.po_number))
                self.tree.setItem(row_position, 2, QTableWidgetItem(po.added_date.strftime("%Y-%m-%d") if po.added_date else "N/A"))
                self.tree.setItem(row_position, 3, QTableWidgetItem(str(po.total_qty)))
                self.tree.setItem(row_position, 4, QTableWidgetItem(f"{po.total_amount:,.2f}"))  # Format with commas and 2 decimals

        except Exception as e:
            print(f"Error loading purchase orders: {e}")
            # Show error using QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to load purchase orders:\n{e}")

    def search_purchase_order(self):
        """Filter the QTableWidget to display only matching purchase orders."""
        search_term = self.search_entry.text().strip()  # Get text from QLineEdit
        if not search_term:
            QMessageBox.warning(self, "Empty Search", "Please enter a search term.")
            return

        # Clear the table before populating search results
        self.tree.setRowCount(0)  # Remove all rows in QTableWidget
        try:
            # Query to search purchase orders by PO Number
            query = "SELECT * FROM PurchaseOrder WHERE po_number LIKE %s"
            search_results = self.db_handler.fetch_query(query, (f"%{search_term}%",))

            if not search_results:
                QMessageBox.information(self, "No Results", "No matching purchase orders found.")
                return

            # Populate the QTableWidget with search results
            for po_data in search_results:
                # Format data for display
                order_date = po_data.get('order_date', 'N/A')
                total_amount = po_data.get('total_amount', 0)

                # Format the date if available
                if order_date != 'N/A':
                    order_date = order_date.strftime("%Y-%m-%d")  # Assuming it's a datetime object

                # Format the total amount for better readability
                formatted_total_amount = f"{total_amount:,.2f}"

                # Add a new row and populate it
                row_position = self.tree.rowCount()
                self.tree.insertRow(row_position)

                self.tree.setItem(row_position, 0, QTableWidgetItem(str(po_data.get('id', 'N/A'))))
                self.tree.setItem(row_position, 1, QTableWidgetItem(po_data.get('po_number', 'N/A')))
                self.tree.setItem(row_position, 2, QTableWidgetItem(order_date))
                self.tree.setItem(row_position, 3, QTableWidgetItem(str(po_data.get('total_qty', 'N/A'))))
                self.tree.setItem(row_position, 4, QTableWidgetItem(formatted_total_amount))

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while searching:\n{str(e)}")

    def add_purchase_order(self):
        """Adds a new Purchase Order."""
        # Step 1: Get the Purchase Order Number
        po_number, ok = QInputDialog.getText(self, "Add Purchase Order", "Enter Purchase Order Number:")
        if not ok or not po_number.strip():
            QMessageBox.warning(self, "Invalid Input", "Purchase Order Number is required.")
            return

        po_number = po_number.strip()

        try:
            # Check if the Purchase Order already exists
            if self.db_handler.purchase_order_exists(po_number):
                QMessageBox.critical(self, "Duplicate Purchase Order", f"Purchase Order {po_number} already exists. Please enter a new number.")
                return
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while checking the purchase order:\n{str(e)}")
            return

        # Step 2: Ask the user to upload an image
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload Image", "", "Image Files (*.png *.jpg *.jpeg)")
        if not file_path:
            QMessageBox.warning(self, "No Image", "No image file selected.")
            return

        # Step 3: Process the image to extract items
        try:
            image_processor = ImageProcessor(file_path)
            items = image_processor.process_and_extract_items(po_number)
        except Exception as e:
            QMessageBox.critical(self, "Processing Error", f"An error occurred while processing the image:\n{str(e)}")
            return

        if not items:
            QMessageBox.warning(self, "No Items Found", "No items were extracted from the image.")
            return

        # Step 4: Initialize PurchaseOrder and calculate total quantity and total amount
        new_po = PurchaseOrder(po_number)
        total_qty = 0
        total_amount = 0

        for item in items:
            new_po.add_item(item)
            if item.qty and item.rate_include_gst:
                total_qty += item.qty
                total_amount += item.qty * item.rate_include_gst

        new_po.total_qty = total_qty
        new_po.total_amount = total_amount

        # Step 5: Save the Purchase Order in the database (without saving items yet)
        try:
            # Save the PO and get the PO ID
            new_po.id = self.db_handler.add_purchase_order(new_po)
            self.purchase_orders.append(new_po)

            # Insert the Purchase Order into the QTableWidget
            row_position = self.tree.rowCount()
            self.tree.insertRow(row_position)

            self.tree.setItem(row_position, 0, QTableWidgetItem(str(new_po.id)))
            self.tree.setItem(row_position, 1, QTableWidgetItem(new_po.po_number))
            self.tree.setItem(row_position, 2, QTableWidgetItem(new_po.added_date if new_po.added_date else "N/A"))
            self.tree.setItem(row_position, 3, QTableWidgetItem(str(new_po.total_qty)))
            self.tree.setItem(row_position, 4, QTableWidgetItem(f"{new_po.total_amount:,.2f}"))

            # Step 6: Open the edit items window for further item editing
            self.open_edit_items_window(po_number, items, new_po, add=True)

            # Show success message to the user
            QMessageBox.information(self, "Success", f"Purchase Order {po_number} added successfully! Now you can edit the items.")
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while saving the purchase order:\n{str(e)}")
            traceback.print_exc()  # Print full traceback for debugging

    def update_purchase_order(self):
        """Update the selected purchase order."""
        # Get the currently selected row in the QTableWidget
        selected_row = self.tree.currentRow()

        if selected_row >= 0:  # Check if a row is selected
            try:
                # Retrieve the Purchase Order number from the selected row
                po_number = self.tree.item(selected_row, 1).text()  # Assuming the PO Number is in column 1

                # Find the corresponding PurchaseOrder object
                selected_po = next((po for po in self.purchase_orders if po.po_number == po_number), None)
                if not selected_po:
                    QMessageBox.warning(self, "Error", "Selected purchase order could not be found.")
                    return

                # Retrieve the PurchaseOrder details from the database
                purchaseOd = self.db_handler.get_purchase_order_by_po_number(selected_po.po_number)

                # Open the edit items window
                self.open_edit_items_window(selected_po.po_number, purchaseOd.items, purchaseOd, False)

                # Notify the user of the update action
                QMessageBox.information(self, "Update PO", f"Update PO: {selected_po.po_number}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while updating the purchase order:\n{str(e)}")
        else:
            QMessageBox.warning(self, "No Selection", "Please select a purchase order to update.")

    def delete_purchase_order(self):
        """Delete the selected purchase order."""
        # Get the currently selected row in the QTableWidget
        selected_row = self.tree.currentRow()

        if selected_row >= 0:  # Check if a row is selected
            try:
                # Retrieve the Purchase Order number from the selected row
                po_number = self.tree.item(selected_row, 1).text()  # Assuming the PO Number is in column 1

                # Find the corresponding PurchaseOrder object
                selected_po = next((po for po in self.purchase_orders if po.po_number == po_number), None)
                if not selected_po:
                    QMessageBox.warning(self, "Error", "Selected purchase order could not be found.")
                    return

                # Confirm before deletion
                confirm = QMessageBox.question(
                    self,
                    "Confirm Deletion",
                    f"Are you sure you want to delete Purchase Order {selected_po.po_number}? This will also delete its associated items.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if confirm == QMessageBox.Yes:
                    # Perform the deletion in the database
                    self.db_handler.delete_purchase_order(selected_po.po_number)

                    # Remove from the QTableWidget (UI)
                    self.tree.removeRow(selected_row)

                    # Remove the purchase order from the internal list
                    self.purchase_orders.remove(selected_po)

                    QMessageBox.information(self, "Success", f"Purchase Order {selected_po.po_number} and its items have been deleted successfully.")
                else:
                    QMessageBox.information(self, "Deletion Canceled", "Purchase Order deletion was canceled.")
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"An error occurred while deleting the purchase order:\n{str(e)}")
        else:
            QMessageBox.warning(self, "No Selection", "Please select a purchase order to delete.")

    def open_edit_items_window(self, po_number, items, new_po, add):
        """Open a window to edit items for a purchase order."""
        # Create the QDialog window
        edit_window = QDialog(self)
        edit_window.setWindowTitle(f"Edit Items for PO {po_number}")
        edit_window.resize(800, 600)
        
        layout = QVBoxLayout(edit_window)

        # Table for displaying items
        columns = ["Cart Part No", "Country of Origin", "A/Unit", "Qty", "Rate Include GST", "Nomenclature"]
        table = QTableWidget(len(items), len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make the table read-only

        # Populate the table with data
        for row, item in enumerate(items):
            table.setItem(row, 0, QTableWidgetItem(item.cart_part_no))
            table.setItem(row, 1, QTableWidgetItem(item.country_of_origin))
            table.setItem(row, 2, QTableWidgetItem(item.a_unit))
            table.setItem(row, 3, QTableWidgetItem(str(item.qty)))
            table.setItem(row, 4, QTableWidgetItem(f"{item.rate_include_gst:.2f}"))
            table.setItem(row, 5, QTableWidgetItem(item.nomenclature))
        layout.addWidget(table)

        # Form for editing selected item
        form_layout = QFormLayout()
        cart_part_no_edit = QLineEdit()
        country_of_origin_edit = QLineEdit()
        a_unit_edit = QLineEdit()
        qty_edit = QLineEdit()
        rate_include_gst_edit = QLineEdit()
        nomenclature_edit = QLineEdit()

        form_layout.addRow("Cart Part No:", cart_part_no_edit)
        form_layout.addRow("Country of Origin:", country_of_origin_edit)
        form_layout.addRow("A/Unit:", a_unit_edit)
        form_layout.addRow("Qty:", qty_edit)
        form_layout.addRow("Rate Include GST:", rate_include_gst_edit)
        form_layout.addRow("Nomenclature:", nomenclature_edit)

        form_group = QGroupBox("Edit Item Details")
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        selected_row = None

        def on_item_select():
            nonlocal selected_row
            selected_row = table.currentRow()
            if selected_row >= 0:
                # Populate the form with the selected item's details
                cart_part_no_edit.setText(table.item(selected_row, 0).text())
                country_of_origin_edit.setText(table.item(selected_row, 1).text())
                a_unit_edit.setText(table.item(selected_row, 2).text())
                qty_edit.setText(table.item(selected_row, 3).text())
                rate_include_gst_edit.setText(table.item(selected_row, 4).text())
                nomenclature_edit.setText(table.item(selected_row, 5).text())

        def validate_entries():
            try:
                qty = int(qty_edit.text())
                rate_include_gst = float(rate_include_gst_edit.text())
                if qty <= 0 or rate_include_gst <= 0:
                    raise ValueError("Qty and Rate Include GST must be positive values.")
            except ValueError as e:
                QMessageBox.critical(edit_window, "Input Error", f"Invalid input: {str(e)}")
                return False
            return True

        def save_changes():
            nonlocal selected_row
            if selected_row is not None and validate_entries():
                # Update the items list with new values
                updated_item = items[selected_row]
                updated_item.cart_part_no = cart_part_no_edit.text()
                updated_item.country_of_origin = country_of_origin_edit.text()
                updated_item.a_unit = a_unit_edit.text()
                updated_item.qty = int(qty_edit.text())
                updated_item.rate_include_gst = float(rate_include_gst_edit.text())
                updated_item.nomenclature = nomenclature_edit.text()

                # Update the table with new values
                table.setItem(selected_row, 0, QTableWidgetItem(updated_item.cart_part_no))
                table.setItem(selected_row, 1, QTableWidgetItem(updated_item.country_of_origin))
                table.setItem(selected_row, 2, QTableWidgetItem(updated_item.a_unit))
                table.setItem(selected_row, 3, QTableWidgetItem(str(updated_item.qty)))
                table.setItem(selected_row, 4, QTableWidgetItem(f"{updated_item.rate_include_gst:.2f}"))
                table.setItem(selected_row, 5, QTableWidgetItem(updated_item.nomenclature))

                QMessageBox.information(edit_window, "Success", "Item updated successfully!")

        def save_items_and_po():
            total_qty = sum(item.qty for item in items)
            total_amount = sum(item.qty * item.rate_include_gst for item in items)

            new_po.total_qty = total_qty
            new_po.total_amount = total_amount
            new_po.items = items

            try:
                if add:
                    self.db_handler.add_purchase_order_items(new_po)
                else:
                    self.db_handler.update_purchase_order(new_po)
                    self.db_handler.update_purchase_order_items(new_po)

                QMessageBox.information(edit_window, "Success", "Purchase Order and Items saved successfully!")
                edit_window.accept()  # Close the dialog
            except Exception as e:
                QMessageBox.critical(edit_window, "Error", f"Error saving items and PO: {str(e)}")

        # Buttons for actions
        button_layout = QHBoxLayout()
        save_changes_button = QPushButton("Save Changes")
        save_changes_button.clicked.connect(save_changes)
        save_items_button = QPushButton("Save Items and PO")
        save_items_button.clicked.connect(save_items_and_po)

        button_layout.addWidget(save_changes_button)
        button_layout.addWidget(save_items_button)
        layout.addLayout(button_layout)

        # Connect the item selection to the form population
        table.itemSelectionChanged.connect(on_item_select)

        edit_window.exec_()
