import cv2
import re

from qreader import QReader # QRCode
from pylibdmtx.pylibdmtx import decode as DMReader # DataMatrix

TEMP_IMAGE = "temp_image.jpg"

class OCRProcessing:
    def __init__(self):
        pass

    def find_pattern(self, tracking_number):
        code = tracking_number.upper().strip()
    
        # Padrão dos Correios e similares (ex: SW123456789BR)
        if re.fullmatch(r'^[A-Z]{2}\d{9}[A-Z]{2}$', codigo):
            return (True, "Correios/Direct Log/Sequoia ou outras")
        
        # Padrões da Sequoia/Shopee
        if re.fullmatch(r'^SFX\d{14}BR$', codigo):
            return (True, "Shopee (Sequoia)")
        if re.fullmatch(r'^BR\d{12}[A-Z]$', codigo):
            return (True, "Shopee (Sequoia)")
        if re.fullmatch(r'^BR\d{13}$', codigo):
            return (True, "Shopee (Sequoia)")
        if re.fullmatch(r'^SFS\d{13}BR$', codigo):
            return (True, "Soma (Sequoia)")
        if re.fullmatch(r'^SQ\d{9}BR$', codigo):
            return (True, "Carrefour (Sequoia)")
        
        # Amazon (Sequoia)
        if re.fullmatch(r'^AM\d{9}SQ$', codigo) or re.fullmatch(r'^AM\d{10}SE$', codigo):
            return (True, "Amazon (Sequoia)")
        
        # Outros padrões Sequoia
        if re.fullmatch(r'^VTX-\d{7}$', codigo):
            return (True, "BABADOTOP (Sequoia)")
        if re.fullmatch(r'^HI\d{9}[A-Z]{2}$', codigo):
            return (True, "INFRACOMMERCE (Sequoia)")
        if re.fullmatch(r'^BRR\d{7}$', codigo):
            return (True, "DOLCE GUSTO (Sequoia)")
        
        # Lojas internacionais
        if re.fullmatch(r'^LP\d{14}$', codigo):
            return (True, "AliExpress (Logística própria)")
        if re.fullmatch(r'^YT\d{16}$', codigo):
            return (True, "AliExpress/GearBest/BangGood (Yun Express)")
        if re.fullmatch(r'^YD\d{9}YW$', codigo):
            return (True, "AliExpress/GearBest/BangGood (Yanwen)")
        if re.fullmatch(r'^SYBAA\d{8}$', codigo) or re.fullmatch(r'^SYBAB\d{8}$', codigo):
            return (True, "AliExpress/GearBest/BangGood (Pos Malaysia)")
        if re.fullmatch(r'^NL\d{14}$', codigo):
            return (True, "AliExpress/GearBest/BangGood (Netherlands Post)")
        if re.fullmatch(r'^SY\d{11}$', codigo):
            return (True, "AliExpress/GearBest/BangGood (SunYou)")
        
        return (False, "Desconhecido")


    def take_picture(self):
        print("Taking picture...")
        cam = cv2.VideoCapture(0)
        
        try:
            cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            result, image = cam.read()

            if not result:
                raise ValueError("Failed to capture image from camera")
            cv2.imwrite(TEMP_IMAGE, image)
        finally:
            cam.release()

    def read_qrcode(self, img_path):
        print("Trying to read QRcode...")
        try:
            img = cv2.imread(img_path)
            qreader_out = QReader().detect_and_decode(image=img)

            return qreader_out
        except Exception as e:
            print(f"Error reading QRCode: {e}")

    def read_datamatrix(self, img_path):
        print(f"Trying to read DataMatrix...")
        try:
            img = cv2.imread(img_path)
            dmreader_out = DMReader(img)

            return dmreader_out
        except Exception as e:
            print(f"Error reading DataMatrix: {e}")


if __name__ == "__main__":
    ocrp = OCRProcessing()
    # ocrp.take_picture()
    print(f"QRcode: {read_qrcode(TEMP_IMAGE)}")
    print(f"DataMatrix: {read_datamatrix(TEMP_IMAGE)}")


