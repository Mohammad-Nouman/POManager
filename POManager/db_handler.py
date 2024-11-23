import mysql.connector
from mysql.connector import Error
from POManager.purchase_order import PurchaseOrder
from POManager.item import Item

class DBHandler:
    def __init__(self, host, user, password, database):
        try:
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            if self.connection.is_connected():
                print("Connected to MySQL database")
                self.create_tables_if_not_exists()
        except Error as e:
            print(f"Error: {e}")
            self.connection = None

    def execute_query(self, query, params=None):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            self.connection.commit()
        except Error as e:
            print(f"Error: {e}")

    def fetch_query(self, query, params=None):
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error as e:
            print(f"Error: {e}")
            return None
        
    def fetch_one_query(self, query, params=None):
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            return cursor.fetchone()
        except Error as e:
            print(f"Error: {e}")
            return None

    def close_connection(self):
        if self.connection.is_connected():
            self.connection.close()
            print("MySQL connection closed.")

    def create_tables_if_not_exists(self):
        # SQL queries to create tables if they don't exist
        create_purchase_order_table = """
        CREATE TABLE IF NOT EXISTS PurchaseOrder (
            id INT AUTO_INCREMENT PRIMARY KEY,
            po_number VARCHAR(255) NOT NULL,
            order_date DATE,
            total_qty INT,
            total_amount DECIMAL(10, 2)
        );
        """
        
        create_item_table = """
        CREATE TABLE IF NOT EXISTS Item (
            id INT AUTO_INCREMENT PRIMARY KEY,
            purchase_order_id INT,
            cart_part_no VARCHAR(255),
            country_of_origin VARCHAR(100),
            a_unit VARCHAR(100),
            qty INT,
            rate_include_gst DECIMAL(10, 2),
            nomenclature TEXT,
            FOREIGN KEY (purchase_order_id) REFERENCES PurchaseOrder(id) ON DELETE CASCADE
        );
        """

        create_delivery_tracking_table = """
        CREATE TABLE IF NOT EXISTS DeliveryTracking (
            id INT AUTO_INCREMENT PRIMARY KEY,
            item_id INT,
            challan_no VARCHAR(255),
            delivery_date DATE,
            delivered_qty INT,
            rejected_qty INT,
            approved_qty INT,
            FOREIGN KEY (item_id) REFERENCES Item(id) ON DELETE CASCADE
        );
        """

        create_item_status_table = """
        CREATE TABLE IF NOT EXISTS ItemStatus (
            id INT AUTO_INCREMENT PRIMARY KEY,
            item_id INT,
            remaining_qty INT,
            FOREIGN KEY (item_id) REFERENCES Item(id) ON DELETE CASCADE
        );
        """

        # Execute table creation queries
        self.execute_query(create_purchase_order_table)
        self.execute_query(create_item_table)
        self.execute_query(create_delivery_tracking_table)
        self.execute_query(create_item_status_table)

    def insert_purchase_order(self, po_number, order_date, total_qty, total_amount):
        query = "INSERT INTO PurchaseOrder (po_number, order_date, total_qty, total_amount) VALUES (%s, %s, %s, %s)"
        params = (po_number, order_date, total_qty, total_amount)
        self.execute_query(query, params)

    def purchase_order_exists(self, po_number):
        """Check if a purchase order exists in the database."""
        query = "SELECT COUNT(*) FROM PurchaseOrder WHERE po_number = %s"
        result = self.fetch_query(query, (po_number,))
        return result[0]['COUNT(*)'] > 0

    def add_purchase_order_items(self, purchase_order):
        try:
            # Insert items into the items table
            for item in purchase_order.items:
                item_query = """
                INSERT INTO Item (purchase_order_id, cart_part_no, country_of_origin, a_unit, qty, rate_include_gst, nomenclature)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                self.execute_query(item_query, (
                    purchase_order.id,
                    item.cart_part_no,
                    item.country_of_origin,
                    item.a_unit,
                    item.qty,
                    item.rate_include_gst,
                    item.nomenclature
                ))
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e
        
    def update_purchase_order_items(self, purchase_order):
        try:
            # Update items in the items table
            for item in purchase_order.items:
                item_query = """
                UPDATE Item 
                SET 
                    cart_part_no = %s,
                    country_of_origin = %s,
                    a_unit = %s,
                    qty = %s,
                    rate_include_gst = %s,
                    nomenclature = %s
                WHERE id = %s
                """
                self.execute_query(item_query, (
                    item.cart_part_no,
                    item.country_of_origin,
                    item.a_unit,
                    item.qty,
                    item.rate_include_gst,
                    item.nomenclature,
                    item.id  # Assuming each item has a unique `id`
                ))
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e

    def add_purchase_order(self, purchase_order):
        try:
            # Insert into the purchase_orders table
            query = "INSERT INTO PurchaseOrder (po_number, order_date, total_qty, total_amount) VALUES (%s, %s, %s, %s)"
            self.execute_query(query, (purchase_order.po_number, purchase_order.added_date, purchase_order.total_qty, purchase_order.total_amount))

            purchase_order_id_query = "SELECT LAST_INSERT_ID()"
            purchase_order_id = self.fetch_query(purchase_order_id_query)[0]['LAST_INSERT_ID()']

            self.connection.commit()
            return purchase_order_id
        except Exception as e:
            self.connection.rollback()
            raise e

    def update_purchase_order(self, purchase_order):
        try:
            # Update the purchase order in the database
            query = """
            UPDATE PurchaseOrder 
            SET order_date = %s, 
                total_qty = %s, 
                total_amount = %s 
            WHERE po_number = %s
            """
            self.execute_query(query, (
                purchase_order.added_date,
                purchase_order.total_qty,
                purchase_order.total_amount,
                purchase_order.po_number
            ))

            self.connection.commit()  # Commit the transaction
        except Exception as e:
            self.connection.rollback()  # Rollback on error
            raise e

    def insert_delivery_tracking(self, item_id, challan_no, delivery_date, delivered_qty, rejected_qty, approved_qty):
        query = "INSERT INTO DeliveryTracking (item_id, challan_no, delivery_date, delivered_qty, rejected_qty, approved_qty) VALUES (%s, %s, %s, %s, %s, %s)"
        params = (item_id, challan_no, delivery_date, delivered_qty, rejected_qty, approved_qty)
        self.execute_query(query, params)

    def insert_item_status(self, item_id, remaining_qty):
        query = "INSERT INTO ItemStatus (item_id, remaining_qty) VALUES (%s, %s)"
        params = (item_id, remaining_qty)
        self.execute_query(query, params)

    def get_purchase_order_by_po_number(self, po_number):
        # Fetch the Purchase Order details
        query = "SELECT id, po_number, order_date, total_qty, total_amount FROM PurchaseOrder WHERE po_number = %s"
        params = (po_number,)
        result = self.fetch_query(query, params)


        if result:
            # Create a PurchaseOrder object
            po_data = result[0]
            purchase_order = PurchaseOrder(po_number)
            purchase_order.id = po_data['id']
            purchase_order.added_date = po_data['order_date']
            purchase_order.total_qty = po_data['total_qty']
            purchase_order.total_amount = po_data['total_amount']
            # Fetch all items associated with the Purchase Order
            item_query = """
                SELECT id,cart_part_no, country_of_origin, a_unit, qty, rate_include_gst, nomenclature 
                FROM Item 
                WHERE purchase_order_id = %s
            """
            item_params = (purchase_order.id,)
            items_result = self.fetch_query(item_query, item_params)

            # Add each item to the PurchaseOrder object
            for item_data in items_result:
                id,cart_part_no, country_of_origin, a_unit, qty, rate_include_gst, nomenclature = item_data.values()
                item = Item(
                    cart_part_no=cart_part_no,
                    country_of_origin=country_of_origin,
                    a_unit=a_unit,
                    qty=qty,
                    rate_include_gst=rate_include_gst,
                    nomenclature=nomenclature
                )
                item.id =id
                purchase_order.add_item(item)           

            return purchase_order  # Return the fully populated PurchaseOrder object

        return None  # Return None if the Purchase Order is not found

    def get_purchase_orders(self):
        query = "SELECT * FROM PurchaseOrder"
        result = self.fetch_query(query)
        if result:
            return result
        return []

    def get_items_by_purchase_order_id(self, purchase_order_id):
        query = "SELECT * FROM Item WHERE purchase_order_id = %s"
        params = (purchase_order_id,)
        result = self.fetch_query(query, params)
        return result

    def get_delivery_tracking_by_item_id(self, item_id):
        query = "SELECT * FROM DeliveryTracking WHERE item_id = %s"
        params = (item_id,)
        result = self.fetch_query(query, params)
        return result

    def get_item_status_by_item_id(self, item_id):
        query = "SELECT * FROM ItemStatus WHERE item_id = %s"
        params = (item_id,)
        result = self.fetch_query(query, params)
        return result

    def delete_items_for_po(self, po_number):
        query = "DELETE FROM Item WHERE purchase_order_id = (SELECT id FROM PurchaseOrder WHERE po_number = %s)"
        self.execute_query(query, (po_number,))
    
    def delete_purchase_order(self, po_number):
        try:
            # First, delete the items associated with the PO
            self.delete_items_for_po(po_number)
            
            # Now, delete the purchase order itself
            query = "DELETE FROM PurchaseOrder WHERE po_number = %s"
            self.execute_query(query, (po_number,))
        except Exception as e:
            raise Exception(f"An error occurred while deleting the purchase order: {str(e)}")