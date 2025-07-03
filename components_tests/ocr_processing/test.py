# Importing library
import cv2
import os
from typing import List, Tuple, Callable, Dict, Any, Optional
from pyzbar.pyzbar import decode
from pyzbar.pyzbar import ZBarSymbol
 
# Make one method to decode the barcode 
def BarcodeReader(image):
    
    # read the image in numpy array using cv2
    img = cv2.imread(image)
    treated_img = _treat_image(img)
     
    # Decode the barcode image
    detectedBarcodes = decode(treated_img, symbols=[ZBarSymbol.QRCODE, ZBarSymbol.CODE128])

    # If not detected then print the message
    if not detectedBarcodes:
        print("Barcode Not Detected or your barcode is blank/corrupted!")
    else:
      
          # Traverse through all the detected barcodes in image
        for barcode in detectedBarcodes:  
          
            # Locate the barcode position in image
            (x, y, w, h) = barcode.rect
            
            # Put the rectangle in image using 
            # cv2 to highlight the barcode
            cv2.rectangle(treated_img, (x-10, y-10),
                          (x + w+10, y + h+10), 
                          (255, 0, 0), 2)
            
            if barcode.data!="":
              
            # Print the barcode data
                print(barcode.data)
                print(barcode.type)
                
    #Display the image
    cv2.imshow("Image", treated_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def _treat_image(
        image: Any,
        resize_width: int = 1024
        ) -> Any:
        """
        Preprocess the image for OCR by converting to grayscale and resizing.
        """
        # 1. Convert to grayscale
        gray_frame = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray_frame, (5, 5), 0)
        binary_frame = cv2.threshold(blur, 0, 255, cv2.THRESH_OTSU)[1]

        # 2. Resize the image
        h, w = gray_frame.shape
        scale = resize_width / w
        new_h, new_w = int(h * scale), resize_width
        resized_gray_frame = cv2.resize(gray_frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

        return binary_frame

if __name__ == "__main__":
  # Take the image from user
    image_name="aa_1751167291971_24404_processed.jpg"
    test_images_directory = "test_images"
    BarcodeReader(os.path.join(test_images_directory, image_name))