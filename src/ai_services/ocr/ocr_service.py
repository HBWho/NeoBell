import pytesseract
import cv2
import numpy as np
import re

class OCRService:
    def __init__(self, lang='eng'):
        self.lang = lang
        try:
            pytesseract.get_tesseract_version()
            print(f"OCRService initialized with Tesseract. Language: {self.lang}")
        except pytesseract.TesseractNotFoundError:
            print("TesseractNotFoundError: Tesseract is not installed or not in your PATH.")
            print("Please install Tesseract OCR and ensure it's in your system PATH,")
            print("or set pytesseract.pytesseract.tesseract_cmd to its location.")
            raise 

    def find_specific_id_after_keyword(self, text_block, keyword="ID", num_digits=17):
        found_ids = []
        pattern_str = rf"(?i){re.escape(keyword)}[^0-9]*([0-9]{{{num_digits}}})"
        
        for match in re.finditer(pattern_str, text_block):
            id_number = match.group(1)
            found_ids.append(id_number)
            print(f"DEBUG: Found by keyword '{keyword}': {id_number} from match '{match.group(0)}'")

        return list(set(found_ids)) 

    def preprocess_image_for_ocr(self, image_np):
        """
        Applies preprocessing steps to improve OCR accuracy.
        """
        gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)

        binary_img = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2 
        )

        return binary_img

    def extract_text_from_image(self, image_np, preprocess=True, oem=3, psm=6):
        try:
            if preprocess:
                processed_img = self.preprocess_image_for_ocr(image_np)
            else:
                processed_img = image_np 

            custom_config = f'--oem {oem} --psm {psm} -l {self.lang}'
            
            text = pytesseract.image_to_string(processed_img, config=custom_config)
            return text.strip()
        except pytesseract.TesseractError as e:
            print(f"Tesseract Error during text extraction: {e}")
            return ""
        except Exception as e:
            print(f"Generic error during text extraction: {e}")
            return ""

    def find_tracking_numbers(self, text_block):
        """
        Uses regex to find common tracking number patterns in a block of text.
        This needs to be customized based on the carriers you expect.
        """
        patterns = {
            "USPS_Tracking": r'\b(9[0-9]{20,25}|[A-Z]{2}[0-9]{9}[A-Z]{2})\b', # Common USPS patterns
            "FedEx_Express_Ground": r'\b([0-9]{12}|[0-9]{15})\b', # Common FedEx
            "UPS_Tracking": r'\b(1Z[A-Z0-9]{16})\b', # UPS
            "DHL_Express": r'\b([0-9]{10})\b', # DHL (often 10 digits, but can vary)
            "Generic_Alphanumeric_Long": r'\b([A-Z0-9]{10,30})\b' # A fallback for longer codes
        }
        
        found_numbers = {}
        for carrier, pattern in patterns.items():
            matches = re.findall(pattern, text_block, re.IGNORECASE) # re.IGNORECASE can be helpful
            if matches:
                found_numbers[carrier] = list(set(matches))
        return found_numbers

    def find_order_ids(self, text_block, custom_patterns=None):
        """
        Uses regex to find order ID patterns. This is highly dependent on e-commerce platforms.
        """
        # Common patterns (very generic, you'll need to make these more specific)
        patterns = {
            "Amazon_Order": r'\b([0-9]{3}-[0-9]{7}-[0-9]{7})\b',
            "Generic_Order_ID_Short": r'\b(ORDER|ORD)[-_#\s]*([A-Z0-9]{6,15})\b',
            "Generic_Order_ID_Long": r'\b(ORDER|ORD)[-_#\s]*([A-Z0-9]{10,25})\b',
        }
        if custom_patterns: # Allow passing custom regex patterns
            patterns.update(custom_patterns)

        found_ids = {}
        for source, pattern in patterns.items():
            # For patterns with groups, re.findall returns tuples of groups
            # We often want the full match or a specific group
            matches = []
            for match_obj in re.finditer(pattern, text_block, re.IGNORECASE):
                if match_obj.lastindex and match_obj.lastindex >= 2: # If it has groups like (ORDER)(ID_PART)
                    matches.append(match_obj.group(match_obj.lastindex)) # Get the last captured group (ID part)
                else:
                    matches.append(match_obj.group(0)) # Get the full match
            
            if matches:
                found_ids[source] = list(set(matches))
        return found_ids


if __name__ == '__main__':
    try:
        ocr_processor = OCRService()
        img_path = "package.jpg"

        frame = cv2.imread(img_path)
        if frame is None:
            print(f"Could not read image from {img_path}")
        else:
            print(f"Performing OCR on image: {img_path}")
            
            preprocessed_for_display = ocr_processor.preprocess_image_for_ocr(frame.copy())

            extracted_text = ocr_processor.extract_text_from_image(frame) # Uses preprocessing by default
            
            if extracted_text:
                # print(f"extracted_text: {extracted_text}")
                match = re.search(r'ID:\D*(\d\D*){17}', extracted_text)
                if match:
                    # Extract just the digits
                    digits = re.sub(r'\D', '', match.group())
                    # Take first 17 digits in case there were more
                    result = digits[:17]
                    print(result)  # Output: 70267642979184203
                else:
                    print("No matching ID found")

            else:
                print("No text could be extracted from the image.")

    except pytesseract.TesseractNotFoundError:
        print("Tesseract is not configured. OCR example cannot run.")
    except Exception as e:
        print(f"An error occurred in the OCR example: {e}")
