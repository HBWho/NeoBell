import cv2
import pytesseract
import re
from pyzbar.pyzbar import decode
from PIL import Image 

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract' # Or your path

def preprocess_image_for_ocr(image_cv):
    """Preprocesses a CV2 image for OCR."""
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)

    # Optional: Denoising (apply to grayscale before thresholding)
    # gray = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
    # Or a simple blur:
    # gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # Thresholding - Otsu can be good, adaptive might be better for uneven lighting
    # thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    # For this specific image, simple global might be okay or adaptive
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    # Invert if text is black on white, and tesseract prefers white text on black bg sometimes
    # or black text on white. Test what works best. Pytesseract generally prefers black text on white.
    # If using THRESH_BINARY_INV, make sure your text is white.
    # If using THRESH_BINARY, text is black.

    # Optional: Morphological operations to clean up noise or connect characters
    # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,1))
    # thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    # thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return thresh

def extract_text_from_image_cv(image_cv):
    """Extracts text from a preprocessed CV2 image."""
    # For some Tesseract versions/configs, specific page segmentation modes can help
    # custom_config = r'--oem 3 --psm 6' # Example
    # text = pytesseract.image_to_string(image_cv, config=custom_config)
    text = pytesseract.image_to_string(image_cv, lang='eng+por')
    return text

def extract_package_info_from_text(text):
    """Extracts structured information from raw OCR text."""
    info = {
        'tracking_numbers': [], # Can be multiple
        'order_id': None,
        'ceps': [], # Brazilian Postal Codes
        'weight': None,
        'recipient_address_block': None, # Approximated
        'sender_address_block': None,    # Approximated
        'raw_text': text
    }

    # Brazilian Tracking Numbers (Correios-like)
    # R 80230180 is a format. Could be R[letter] ######### BR
    # Let's make a more general one for R followed by digits, and common international.
    # Also, the TBR code.
    tracking_patterns = [
        r'\b[A-Z]{1,2}\s?\d{8,10}(?:\s?[A-Z]{2})?\b', # Catches R 80230180 and similar formats like XX123456789YY
        r'\bTBR\d+\b', # For the internal barcode like TBR180191546
        r'\b1Z[0-9A-Z]{16}\b',  # UPS
        r'\b[0-9]{12}\b',      # FedEx Ground, some USPS
        r'\b[A-Z]{2}[0-9]{9}[A-Z]{2}\b' # Standard international mail
    ]
    for pattern in tracking_patterns:
        found = re.findall(pattern, text)
        if found:
            info['tracking_numbers'].extend(found)
    info['tracking_numbers'] = list(set(info['tracking_numbers'])) # Remove duplicates

    # Order ID (Amazon specific)
    order_id_match = re.search(r'Order ID:\s*(\d{3}-\d{7}-\d{7})', text, re.IGNORECASE)
    if order_id_match:
        info['order_id'] = order_id_match.group(1)
    else: # Sometimes it's just the number without "Order ID:" prefix
        order_id_match_num_only = re.search(r'\b(\d{3}-\d{7}-\d{7})\b', text)
        if order_id_match_num_only:
             info['order_id'] = order_id_match_num_only.group(1)


    # Brazilian CEP (Postal Code)
    cep_pattern = r'\b\d{5}-?\d{3}\b' # e.g., 80230-180 or 80230180
    info['ceps'] = list(set(re.findall(cep_pattern, text)))

    # Weight
    weight_match = re.search(r'(\d+\.?\d*)\s*KG', text, re.IGNORECASE)
    if weight_match:
        info['weight'] = f"{weight_match.group(1)} KG"

    # Basic Address Block Approximation (very naive)
    # This is hard. A better way would be to use known ROIs for Amazon labels.
    lines = text.split('\n')
    potential_address_lines = []
    for i, line in enumerate(lines):
        if any(cep.replace("-","") in line.replace("-","") for cep in info['ceps']):
            # Try to grab a few lines before and after the CEP line
            start = max(0, i-3)
            end = min(len(lines), i+2)
            potential_address_lines.extend(lines[start:end])
        # Heuristics for recipient name (often starts with proper names)
        if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+', line) and len(line.split()) > 1 and len(line.split()) < 6 :
             if i+2 < len(lines): # Check if next lines exist
                potential_address_lines.append(line)
                potential_address_lines.append(lines[i+1])
                potential_address_lines.append(lines[i+2])


    # Simplistic separation:
    # Amazon labels often have recipient below sender, or recipient on left.
    # The example has sender on top-right, recipient below sender on left.
    # For now, let's just assume the first CEP found might relate to recipient, second to sender.
    # Or, use keywords. "Gabriel de Almeida Spadafora" is clearly recipient.
    # "Avenida Antonio Candido Machado" is sender.

    # This part is highly heuristic and would need significant improvement for robustness
    recipient_keywords = ["Gabriel de Almeida Spadafora", "Rua Conselheiro Laurindo"] # From image
    sender_keywords = ["Avenida Antonio Candido Machado", "GRU5", "Cajamar"] # From image

    recipient_text = []
    sender_text = []

    for line in lines:
        if any(kw.lower() in line.lower() for kw in recipient_keywords):
            recipient_text.append(line)
        elif any(kw.lower() in line.lower() for kw in sender_keywords):
            sender_text.append(line)

    # If still empty, use the CEP-based lines (very rough)
    if not recipient_text and potential_address_lines:
        info['recipient_address_block'] = "\n".join(list(set(potential_address_lines))) # Crude
    elif recipient_text:
        info['recipient_address_block'] = "\n".join(list(set(recipient_text)))

    if not sender_text and len(info['ceps']) > 1 and potential_address_lines: # If more than one CEP
        # This is just a guess and likely wrong often
        info['sender_address_block'] = "\n".join(list(set(potential_address_lines)))
    elif sender_text:
        info['sender_address_block'] = "\n".join(list(set(sender_text)))


    return info

def read_barcodes_from_image(image_path_or_pil_image):
    """Reads all barcodes from an image file path or PIL image."""
    try:
        if isinstance(image_path_or_pil_image, str):
            img = Image.open(image_path_or_pil_image)
        else: # Assuming PIL image
            img = image_path_or_pil_image
    except Exception as e:
        print(f"Error opening image for barcode reading: {e}")
        return []

    barcodes = decode(img)
    barcode_data = []
    for barcode in barcodes:
        data = barcode.data.decode('utf-8')
        type = barcode.type
        barcode_data.append({
            'data': data,
            'type': type
        })
        # Special handling for Amazon DataMatrix which often contains rich info
        if type == 'DATAMATRIX' and len(data) > 50: # Arbitrary length to guess it's a rich one
            print(f"Found rich DataMatrix: {data[:100]}...") # Print first 100 chars
            # You might parse this 'data' string further if it has a known format
            # (e.g., pipe-delimited, JSON-like)
    return barcode_data


def process_package_label(image_path):
    print(f"DEBUG: Starting process_package_label for: {image_path}") # DEBUG
    img_cv = cv2.imread(image_path)
    if img_cv is None:
        print(f"Error: Could not read image at {image_path}")
        return None

    # 1. Read Barcodes First - often most reliable
    all_barcodes_data = read_barcodes_from_image(image_path) # pyzbar works well with PIL Images
    if not all_barcodes_data:
        print("DEBUG: No barcodes detected. Check image quality or pyzbar installation.")

    # 2. Full Page OCR
    preprocessed_cv_img = preprocess_image_for_ocr(img_cv.copy()) # Use a copy

    debug_image_path = "debug_preprocessed_image.png"
    cv2.imwrite(debug_image_path, preprocessed_cv_img)
    print(f"DEBUG: Preprocessed image saved as {debug_image_path}. Check if text is clear.") # DEBUG

    full_text = extract_text_from_image_cv(preprocessed_cv_img)
    # print("---- Full Text OCR ----\n", full_text, "\n----------------------")
    extracted_info = extract_package_info_from_text(full_text)

    # 3. Consolidate with Barcode Data
    # Add barcode data to tracking numbers if not already picked by OCR
    for bc in all_barcodes_data:
        # Check if barcode data looks like a tracking number and isn't already found
        # (This logic can be refined based on typical barcode contents)
        is_potential_tracking = any(
            re.fullmatch(pat, bc['data']) for pat in [
                r'[A-Z]{1,2}\s?\d{8,10}(?:\s?[A-Z]{2})?', r'TBR\d+',
                r'1Z[0-9A-Z]{16}', r'[0-9]{12}', r'[A-Z]{2}[0-9]{9}[A-Z]{2}'
            ]
        )
        if is_potential_tracking and bc['data'] not in extracted_info['tracking_numbers']:
            extracted_info['tracking_numbers'].append(bc['data'])

    # If OCR failed to get a primary tracking number but barcodes have one:
    if not extracted_info.get('primary_tracking') and extracted_info['tracking_numbers']:
         extracted_info['primary_tracking'] = extracted_info['tracking_numbers'][0] # Take the first one

    # The original detect_roi was generic. For Amazon, fixed ROIs or more intelligent
    # segmentation would be better. For now, let's skip the generic ROI detection
    # as its output wasn't properly integrated.
    # If you want to add specific ROI processing:
    # Example: Define a ROI for the main tracking number (R 80230180) if its position is consistent
    # x, y, w, h = 100, 200, 300, 50 # Example coordinates, TUNE THESE
    # roi_tracking_cv = img_cv[y:y+h, x:x+w]
    # preprocessed_roi_tracking = preprocess_image_for_ocr(roi_tracking_cv)
    # roi_tracking_text = extract_text_from_image_cv(preprocessed_roi_tracking)
    # Potentially update extracted_info['tracking_numbers'] with this more targeted OCR

    final_result = {
        **extracted_info,
        'barcodes': all_barcodes_data,
    }
    # Clean up empty lists/None values if desired before returning
    final_result = {k: v for k, v in final_result.items() if v}

    return final_result
