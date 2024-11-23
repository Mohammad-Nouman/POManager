import re
import pytesseract
from POManager.item import Item
from POManager.purchase_order import PurchaseOrder
import cv2

class ImageProcessor:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = None
        self.gray_image = None
        self.text = ""

    def load_image(self):
        """Load the image from the file path."""
        self.image = cv2.imread(self.image_path)
        if self.image is None:
            raise ValueError("Image could not be loaded.")
        return self.image

    def convert_to_gray(self):
        """Convert the image to grayscale."""
        if self.image is None:
            raise ValueError("Image not loaded.")
        self.gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        return self.gray_image

    def extract_text(self):
        """Extract text from the grayscale image using OCR."""
        if self.gray_image is None:
            raise ValueError("Image not processed into grayscale.")
        self.text = pytesseract.image_to_string(self.gray_image)
        return self.text

    def process_image(self):
        """Process the image and return extracted text."""
        self.load_image()
        self.convert_to_gray()
        return self.extract_text()

    def extract_table_section(self, text):
        """Extracts the relevant section of the table from the OCR text."""
        table_section = re.search(r'Nomen.*Amount.', text, re.DOTALL)
        if table_section:
            return table_section.group(0)
        return ""
    
    # Function to clean nomenclature by removing special characters
    def clean_nomenclature(self, nomenclature_tokens):
        cleaned_tokens = []
        for token in nomenclature_tokens:
            if token.isdigit():  # Skip tokens that are digits
                continue
            token = re.sub(r'[^\w\s]', '', token)  # Remove special characters
            if token:  # Add non-empty tokens
                cleaned_tokens.append(token)
        return cleaned_tokens

    # Function to extract item details from the table section
    def extract_item_details(self, table_text):
        print(table_text)
        lines = table_text.split('\n')
        extracted_items = []
        current_item = {}
        nomenclature_tokens = []
        country_codes = ['USA', 'PAK', 'UNITED STATES', 'ITALY', 'JAPAN', 'OEM', 'GEN', 'CHINA', 'KOREA']
        unit_value = ['NOS', 'SET', 'Nos']

        for line in lines:
            tokens = re.split(r'\s+', line.strip())

            for token in tokens:
                if '-' in token:
                    if current_item:
                        current_item['Nomenclature'] = ' '.join(self.clean_nomenclature(nomenclature_tokens)).strip()
                        extracted_items.append(current_item)
                    current_item = {'Cart Part No': token}  # Start new item
                    nomenclature_tokens = []

                elif token.upper() in country_codes:
                    current_item['Country of Origin'] = token

                elif token in unit_value:
                    current_item['A/Unit'] = token

                elif token.isdigit() and 'Qty' not in current_item:
                    current_item['Qty'] = int(token)

                elif '.' in token or ',' in token:
                    token = token.replace(',', '')
                    if 'Qty' in current_item:
                        current_item['Rate Include GST'] = float(token)

                elif re.match(r'^\d{1,3}(,\d{3})*(\.\d{1,2})?$', token):
                    rate = float(token.replace(',', ''))
                    current_item['Total Cost'] = rate

                else:
                    nomenclature_tokens.append(token)

        if current_item:
            current_item['Nomenclature'] = ' '.join(self.clean_nomenclature(nomenclature_tokens)).strip()
            extracted_items.append(current_item)

        return extracted_items

    # Function to process the image, extract details, and return the items
    def process_and_extract_items(self,po_number):
        text = self.process_image()
        table_text = self.extract_table_section(text)
        extracted_items = self.extract_item_details(table_text)

        purchase_order = PurchaseOrder(po_number)
        items = []

        for item in extracted_items:
            if "Cart Part No" not in item or item["Cart Part No"] == "Total:-":
                continue  # Skip this item if 'Cart Part No' is missing
            item_data = {
                "cart_part_no": item.get("Cart Part No"),
                "country_of_origin": item.get("Country of Origin"),
                "a_unit": item.get("A/Unit"),
                "qty": item.get("Qty"),
                "rate_include_gst": item.get("Rate Include GST"),
                "nomenclature": item.get("Nomenclature")
            }
            new_item = Item(**item_data)
            purchase_order.add_item(new_item)
            items.append(new_item)

        return items
