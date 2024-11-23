from PyQt5.QtWidgets import QApplication,QMainWindow
from POManager.db_handler import DBHandler
from POManager.purchase_order_app import PurchaseOrderApp
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)


    db_handler = DBHandler(host="localhost", user="root", password="", database="purchase_order_app")
    
    main_window = PurchaseOrderApp(db_handler=db_handler)
    main_window.show()

    sys.exit(app.exec_())
