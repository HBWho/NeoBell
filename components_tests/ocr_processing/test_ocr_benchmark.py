import os
import time
import logging
import random
from typing import Dict, List

# To run this test, you need to have ocr_processing.py in the same directory
# or in a path that Python can find.
from ocr_processing import OCRProcessing

# --- Basic Setup ---
# Configure logging to see detailed output from the OCRProcessing class
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger("OCR_Benchmark")

# --- MOCK AWS SERVICE ---
# This function simulates calling an AWS service to validate a tracking code.
def mock_aws_checker(
    code: str,
) -> Dict:
    """
    A mock function to simulate an AWS validation endpoint.

    Args:
        code (str): The tracking code to validate.

    Returns:
        Dict: A response dictionary similar to the real one.
    """
    logger.info(f"[Mock AWS] Received code for validation: {code}")
    # Simulate the time it takes for the network request and response
    time.sleep(random.uniform(0.3, 0.8))
    known_valid_codes = ["TBR170845346", "TBR180191546", "TBR186143394", "BR254001448750A"]

    if code in known_valid_codes:
        logger.info(f"[Mock AWS] Code '{code}' is VALID.")
        return {
            'package_found': True,
            'details': {'status': 'pending'} # Simulate a valid status
        }
    else:
        logger.info(f"[Mock AWS] Code '{code}' is INVALID.")
        return {
            'package_found': False
        }

def run_benchmark():
    """
    Main function to run the OCR processing benchmark on local image files.
    """
    # Instantiate your OCR processing class
    ocr_processor = OCRProcessing()

    # --- BENCHMARK LOOP ---
    if False:
        # --- CONFIGURATION ---
        test_images_directory = "test_images"

        # --- INITIALIZATION ---
        if not os.path.exists(test_images_directory):
            logger.error(f"Error: Test directory '{test_images_directory}/' not found.")
            logger.error("Please create it and place your test images with QR/DataMatrix codes inside.")
            return

        image_files = [f for f in os.listdir(test_images_directory) if f.endswith(('.png', '.jpg', '.jpeg'))]

        if not image_files:
            logger.warning(f"No image files found in '{test_images_directory}/'.")
            return

        logger.info(f"--- Starting OCR Benchmark on {len(image_files)} images ---")

        timeout_sec = 5.0
        
        for image_file in image_files:
            image_path = os.path.join(test_images_directory, image_file)
            logger.info(f"\n--- Processing: {image_file} ---")

            start_time = time.time()
            
            # 1. Process the static image to find all codes (QR and DataMatrix)
            # We use a simplified version of the logic in find_validated_code
            # since we are not dealing with a live camera feed.
            result = ocr_processor.find_validated_code(
                img_path=image_path,
                camera_id=-1,
                fast_mode=False,
                code_verification_callback=mock_aws_checker,
                timeout_sec=timeout_sec,
                retries=3,
                on_timeout=lambda: logger.warning(f"❌ FAILURE: Timeout occurred after seconds.")
            )
            
            total_time = time.time() - start_time

            # --- RESULTS ---
            if result["status"] == "success":
                logger.info(f"✅ SUCCESS: Valid code '{result['code']}' found and validated.")
                logger.info(f"Total time for {image_file}: {total_time:.4f} seconds.")
            else:
                logger.warning(f"❌ FAILURE: No valid codes were found in this image.")
                logger.info(f"Total time for {image_file}: {total_time:.4f} seconds (no codes found).")
    
    if True:
        while True:
            start_time = time.time()

            timeout_sec = 5.0

            logger.info(f"\n--- Processing: Camera {0} ---")
                
            # 1. Process the static image to find all codes (QR and DataMatrix)
            # We use a simplified version of the logic in find_validated_code
            # since we are not dealing with a live camera feed.
            result = ocr_processor.find_validated_code(
                img_path='',
                camera_id=0,
                fast_mode=True,
                code_verification_callback=mock_aws_checker,
                timeout_sec=timeout_sec,
                retries=3,
                on_timeout=lambda: logger.warning(f"❌ FAILURE: Timeout occurred after seconds.")
            )
            
            total_time = time.time() - start_time

            # --- RESULTS ---
            if result["status"] == "success":
                logger.info(f"✅ SUCCESS: Valid code '{result['code']}' found and validated.")
                logger.info(f"Total time for Camera {0}: {total_time:.4f} seconds.")
            else:
                logger.warning(f"❌ FAILURE: No valid codes were found in this image.")
            logger.info(f"Total time for Camera {0}: {total_time:.4f} seconds (no codes found).")

if __name__ == "__main__":
    try:
        run_benchmark()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user (Ctrl+C).")
    except Exception as e:
        logger.error(f"An error occurred during benchmarking: {e}")
    finally:
        logger.info("System has shut down.")

