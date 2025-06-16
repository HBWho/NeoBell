import cv2
import re
import logging
from typing import List, Tuple, Union, Optional
from dataclasses import dataclass
from qreader import QReader # QRCode
from pylibdmtx.pylibdmtx import decode as DMReader # DataMatrix

logger = logging.getLogger(__name__)

TEMP_IMAGE = "temp_image.jpg"

@dataclass
class DecodedData:
    data: str
    rect: Optional[object] = None

class OCRProcessing():
    def __init__(self):
        self.qreader = QReader()

    def find_pattern(self, tracking_number: str) -> Tuple[bool, str]:
        """
        Validate a tracking number against known patterns

        Args: 
            tracking_number: The code to validate

        Returns:
            Tuple of (is_valid, carrier_name)
        """
        if not tracking_number:
            return (False, "Empty code")

        code = tracking_number.upper().strip()
    
        # Padrão dos Correios e similares (ex: SW123456789BR)
        if re.fullmatch(r'^[A-Z]{2}\d{9}[A-Z]{2}$', code):
            return (True, "Correios/Direct Log ou outras")
        
        # Padrões da Shopee e outras
        if re.fullmatch(r'^SFX\d{14}BR$', code):
            return (True, "Shopee")
        if re.fullmatch(r'^BR\d{12}[A-Z]$', code):
            return (True, "Shopee")
        if re.fullmatch(r'^BR\d{13}$', code):
            return (True, "Shopee")
        if re.fullmatch(r'^SFS\d{13}BR$', code):
            return (True, "Soma")
        if re.fullmatch(r'^SQ\d{9}BR$', code):
            return (True, "Carrefour")
        
        # Amazon
        if re.fullmatch(r'^AM\d{9}SQ$', code) or re.fullmatch(r'^AM\d{10}SE$', code):
            return (True, "Amazon")
        if re.fullmatch(r'^TBR\d{9}$', code) or re.fullmatch(r'^AM\d{10}SE$', code):
            return (True, "Amazon")
        
        # Outros padrões
        if re.fullmatch(r'^VTX-\d{7}$', code):
            return (True, "BABADOTOP")
        if re.fullmatch(r'^HI\d{9}[A-Z]{2}$', code):
            return (True, "INFRACOMMERCE")
        if re.fullmatch(r'^BRR\d{7}$', code):
            return (True, "DOLCE GUSTO")
        
        # Lojas internacionais
        if re.fullmatch(r'^LP\d{14}$', code):
            return (True, "AliExpress (Logística própria)")
        if re.fullmatch(r'^YT\d{16}$', code):
            return (True, "AliExpress/GearBest/BangGood (Yun Express)")
        if re.fullmatch(r'^YD\d{9}YW$', code):
            return (True, "AliExpress/GearBest/BangGood (Yanwen)")
        if re.fullmatch(r'^SYBAA\d{8}$', code) or re.fullmatch(r'^SYBAB\d{8}$', code):
            return (True, "AliExpress/GearBest/BangGood (Pos Malaysia)")
        if re.fullmatch(r'^NL\d{14}$', code):
            return (True, "AliExpress/GearBest/BangGood (Netherlands Post)")
        if re.fullmatch(r'^SY\d{11}$', code):
            return (True, "AliExpress/GearBest/BangGood (SunYou)")
        
        return (False, "Desconhecido")

    def take_picture(self, camera_id) -> bool:
        """Capture image from camera and save to temp file"""
        logger.info("Taking picture...")
        cam = cv2.VideoCapture(camera_id)
        
        try:
            cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            result, image = cam.read()

            if not result:
                raise ValueError("Failed to capture image from camera")
            cv2.imwrite(TEMP_IMAGE, image)
            return True
        except Exception as e:
            logger.error(f"Error capturing image: {e}")
            return False
        finally:
            cam.release()

    def read_qrcode(self, img_path: str) -> List[DecodedData]:
        """Read all QR codes from image"""
        logger.info("Trying to read QRcode...")
        try:
            img = cv2.imread(img_path)
            if img is None:
                raise ValueError("Could not read image file")
            
            decoded_texts = self.qreader.detect_and_decode(image=img)

            results = []
            for text in decoded_texts:
                if text:
                    results.append(DecodedData(data=str(text)))

            return results
        except Exception as e:
            logger.error(f"Error reading QRCode: {e}")
            return []

    def read_datamatrix(self, img_path: str) -> List[DecodedData]:
        """Read all DataMatrix codes from image"""
        logger.info(f"Trying to read DataMatrix...")
        try:
            img = cv2.imread(img_path)
            if img is None:
                raise ValueError("Could not read image file")
            
            decoded_objects = DMReader(img)

            results = []
            for obj in decoded_objects:
                if obj.data:
                    results.append(DecodedData(
                        data = obj.data.decode('utf-8'),
                        rect = obj.rect
                    ))

            return results
        except Exception as e:
            logger.error(f"Error reading DataMatrix: {e}")
            return []

    def process_codes(self, img_path: str = TEMP_IMAGE) -> None:
        """Main processing function that reads codes and validates them"""
        logger.info(f"Processing codes...")
        qr_codes = self.read_qrcode(img_path)
        dm_codes = self.read_datamatrix(img_path)

        all_codes = qr_codes + dm_codes
        # all_codes = qr_codes

        if not all_codes:
            logger.warning("No codes found in the image")
            return
        
        valid_codes = []
        logger.info("\nFound codes:")
        for code_obj in all_codes:
            code = code_obj.data.strip()
            valid, carrier = self.find_pattern(code)
            valid = True

            valid_codes.append(code)
            logger.info(f"\nCode: {code}")
            logger.info(f"Type: {'QR Code' if code_obj in qr_codes else 'DataMatrix'}")
            logger.info(f"Valid: {'Yes' if valid else 'No'}")
            logger.info(f"Carrier: {carrier}")

        return valid_codes

if __name__ == "__main__":
    ocrp = OCRProcessing()

    ocrp.process_codes(TEMP_IMAGE)

    # if ocrp.take_picture():
    #     ocrp.process_codes()


