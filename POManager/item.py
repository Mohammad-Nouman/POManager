class Item:
    def __init__(self, cart_part_no, country_of_origin=None, a_unit=None, qty=None, rate_include_gst=None, nomenclature=None):
        self.cart_part_no = cart_part_no
        self.country_of_origin = country_of_origin
        self.a_unit = a_unit
        self.qty = qty
        self.rate_include_gst = rate_include_gst
        self.nomenclature = nomenclature
        self.id  = None

    def to_dict(self):
        return {
            'id':self.id,
            "Cart Part No": self.cart_part_no,
            "Country of Origin": self.country_of_origin,
            "A/Unit": self.a_unit,
            "Qty": self.qty,
            "Rate Include GST": self.rate_include_gst,
            "Nomenclature": self.nomenclature
        }
    
    def update_from_db(self, db_handler):
        item_data = db_handler.get_item_status_by_item_id(self.id)
        if item_data:
            self.remaining_qty = item_data[0]['remaining_qty']