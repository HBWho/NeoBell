import cv2
import os
import time
import re
import logging
import threading
import queue
from typing import List, Tuple, Callable, Dict, Any, Optional
from dataclasses import dataclass

# Third-party libraries
from pyzbar import pyzbar
from pylibdmtx.pylibdmtx import decode as DMReader

logger = logging.getLogger(__name__)

TEMP_IMAGE_PREFIX = "ocr_temp_image"
DATA_MATRIX_TIMEOUT_MS = 800

@dataclass
class DecodedData:
    """Represents a decoded code with its data and location."""
    data: str
    rect: Optional[object] = None

class OCRProcessing:
    """
    Handles QR code and DataMatrix scanning from a camera feed.
    This class is designed to be a specialized service, focusing only on finding
    and decoding codes. The "completer" logic with callbacks is handled in the main
    find_validated_code method.
    """
    def __init__(self):
        """Initializes the OCR processing service."""
        self.start_time = None
        self.cap = None
        logger.info("OCRProcessing service initialized.")

    def _valid_pattern(self, tracking_number: str) -> bool:
        """
        Validates if a tracking number matches any known carrier patterns.
        This is a quick local check to avoid unnecessary calls to external services.
        """
        if not tracking_number:
            return False

        code = tracking_number.upper().strip()
        
        # A list of regex patterns for different carriers.
        # This makes it easier to add new patterns in the future.
        patterns = [
            r'^[A-Z]{2}\d{9}[A-Z]{2}$',  # Correios/Direct Log
            r'^SFX\d{14}BR$',          # Shopee
            r'^BR\d{12}[A-Z]$',         # Shopee
            r'^BR\d{13}$',              # Shopee
            r'^AM\d{9}SQ$',             # Amazon
            r'^AM\d{10}SE$',            # Amazon
            r'^TBR\d{9}$',              # Amazon
            r'^LP\d{14}$',              # AliExpress
        ]
        
        return any(re.fullmatch(pattern, code) for pattern in patterns)

    def _treat_image(self, image: Any, target_width: int = 1280) -> Any:
        """
        Preprocess the image for OCR by resizing and converting to grayscale with Gaussian blur.
        """
        # If the image is bigger than the target width, resize it
        if image.shape[1] > target_width:
            scale = target_width / image.shape[1]
            new_size = (target_width, int(image.shape[0] * scale))
            image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)

        gray_frame = cv2.cvtColor(image.copy(), cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray_frame, (5, 5), 0)
        binary_frame = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 21, 5
        )
        return binary_frame

    def _get_center_roi(self, frame: Any, scale: float = 0.5) -> Any:
        """
        Extracts a centered Region of Interest (ROI) from the frame based on a scale factor.
        """
        height, width = frame.shape[:2]
        
        roi_width = int(width * scale)
        roi_height = int(height * scale)
        
        # Calcula as coordenadas do canto superior esquerdo para centralizar a ROI
        x_offset = (width - roi_width) // 2
        y_offset = (height - roi_height) // 2
        
        # Recorta a ROI usando a indexação do NumPy
        roi = frame[y_offset:y_offset + roi_height, x_offset:x_offset + roi_width]
        
        return roi

    def _create_overlapping_tiles(self, image: Any, tile_size_wh: Tuple[int, int], overlap_percent: float) -> List[Any]:
        """
        Generates a list of "tiles" (sub-images) with overlap from the original image.
        """
        img_h, img_w = image.shape[:2]
        tile_w, tile_h = tile_size_wh

        # Calculate step size based on overlap
        step_w = int(tile_w * (1 - overlap_percent))
        step_h = int(tile_h * (1 - overlap_percent))
        
        # Ensure step is at least 1 to avoid infinite loops
        step_w = max(1, step_w)
        step_h = max(1, step_h)

        tiles = []
        for y in range(0, img_h, step_h):
            for x in range(0, img_w, step_w):
                roi = image[y:y + tile_h, x:x + tile_w]
                if roi.shape[0] > 0 and roi.shape[1] > 0:
                    tiles.append(roi.copy())
        return tiles

    def _frame_processing_task(self, camera_id: int, img_path: str, code_queue: queue.Queue, stop_event: threading.Event):
        """
        Continuously captures frames from the specified camera and processes them
        for QR and DataMatrix codes.
        """
        logger.info(f"Starting frame processing task with camera ID: {camera_id} and image path: {img_path}")
        if camera_id >= 0:
            self.cap = cv2.VideoCapture(camera_id)
            if not self.cap.isOpened():
                logger.error(f"Cannot open camera with ID {camera_id}.")
                return

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        processed_codes = set()
        lock = threading.Lock()

        while not stop_event.is_set():
            if camera_id >= 0:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
            elif img_path:
                frame = cv2.imread(img_path)
                if frame is None:
                    logger.error(f"Cannot read image from path: {img_path}")
                    return

            if not self.start_time:
                self.start_time = time.time()

            def detection_worker(detector_func, images: List[Any], thread_name: str):
                """A generic worker to run a detector function."""
                try:
                    start_time = time.time()
                    # Execute the provided detector function (for QR or DataMatrix)
                    for img in images:
                        if stop_event.is_set():
                            return
                        detected_codes = detector_func(img)
                        if not detected_codes:
                            continue
                        for code_data, code_type in detected_codes:
                            code = str(code_data).strip()
                            if not code:
                                continue
                            # Check pattern and if it's new before queueing
                            with lock:
                                if code not in processed_codes:
                                    # Add to cache even if pattern is invalid to avoid re-checking
                                    processed_codes.add(code) 
                                    if self._valid_pattern(code):
                                        logger.info(f"Found valid pattern {code_type} code: {code}. Adding to queue for verification.")
                                        code_queue.put(code)

                except Exception as e:
                    logger.warning(f"A detection worker failed: {e}")
                finally:
                    total_time = time.time() - start_time
                    if total_time > 1.0:  # If processing takes too long, log a warning
                        logger.warning(f"Detection worker '{thread_name}' took too long: {total_time:.2f}s")

            recorded_frame = self._get_center_roi(frame, scale=0.6)
            processed_frame = self._treat_image(recorded_frame)

            # Define the specific functions for the detectors
            pyzbar_detector = lambda f: [(code.data.decode('utf-8'), code.type) for code in pyzbar.decode(f)]
            dm_detector = lambda f: [(obj.data.decode('utf-8'), 'DATAMATRIX') for obj in DMReader(f, timeout=DATA_MATRIX_TIMEOUT_MS) if obj.data]
            
            # Create and start parallel threads for the current frame
            pyzbar_thread = threading.Thread(target=detection_worker, args=(pyzbar_detector, [processed_frame], "pyzbar_thread"), daemon=True)
            dm_thread = threading.Thread(target=detection_worker, args=(dm_detector, [processed_frame], "dm_thread"), daemon=True)
            
            pyzbar_thread.start()
            dm_thread.start()

            # tiles = self._create_overlapping_tiles(processed_frame, tile_size_wh=(350, 350), overlap_percent=0.2)

            # slice_thread_pyzbar = threading.Thread(target=detection_worker, args=(pyzbar_detector, tiles, f"pyzbar_slice"), daemon=True)
            # slice_thread_dm = threading.Thread(target=detection_worker, args=(dm_detector, tiles, f"dm_slice"), daemon=True)
            # slice_thread_pyzbar.start()
            # slice_thread_dm.start()

            # Brief sleep to yield CPU and prevent hammering the camera
            if camera_id >= 0:
                # # Show in the Screen
                cv2.imshow("Camera OCR Processing", processed_frame)
                # Close window if user presses 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    stop_event.set()
                    break
                time.sleep(0.2)
            else:
                break

    def _code_checker_task(self, code_queue: queue.Queue, result_queue: queue.Queue, stop_event: threading.Event, code_verification_callback: Callable[[str], Dict]):
        """
        A worker thread function that takes codes from a queue, checks them
        via the provided callback, and puts a positive result onto the result queue.
        """
        while not stop_event.is_set():
            try:
                # Wait for a code to appear in the queue. Timeout prevents blocking forever.
                code = code_queue.get(timeout=0.1)

                logger.info(f"Checking code with callback: {code}")
                response = code_verification_callback(code)
                
                # Check for a positive, valid response from callback.
                if response and (response.get('package_same') or (response.get('package_found') and response.get('details', {}).get('status') == 'pending')):
                    logger.info(f"Callback validation successful for code: {code}")
                    result = {"status": "success", "code": code, "response": response}
                    result_queue.put(result)
                    stop_event.set() # Signal all other threads to stop
                else:
                    logger.warning(f"Callback validation failed for code: {code}. Response: {response}")

            except queue.Empty:
                continue # No code in queue, loop again.
            except Exception as e:
                logger.error(f"An error occurred during callback check for code {code}: {e}", exc_info=True)

        logger.info("Callback checker task finished.")

    def find_validated_code(
        self, 
        img_path: str,
        camera_id: int, 
        fast_mode: bool,
        code_verification_callback: Callable[[str], Dict], 
        timeout_sec: float,
        retries: int,
        on_timeout: Callable[[], None]
    ) -> Dict:
        """
        Main public method. Starts camera reading and callback checking in parallel.
        It returns as soon as a valid code is confirmed by the callback or when the global timeout is reached.
        This is the "completer" or "race" logic.

        Args:
            camera_id: The ID of the camera to use.
            code_verification_callback: A function that takes a code (str) and returns a response (dict).
            timeout_sec: The maximum time in seconds to wait for a validated code.

        Returns:
            A dictionary with the status and result.
            - On success: {'status': 'success', 'code': '...', 'response': {...}}
            - On timeout: {'status': 'timeout'}
        """
        code_queue = queue.Queue()
        result_queue = queue.Queue()
        stop_event = threading.Event()
        self.start_time = None

        # Create and start the worker threads
        processor = threading.Thread(target=self._frame_processing_task, args=(camera_id, img_path, code_queue, stop_event))
        checker = threading.Thread(target=self._code_checker_task, args=(code_queue, result_queue, stop_event, code_verification_callback))
        
        processor.start()
        checker.start()

        try:
            for attempt in range(retries):
                try:
                    # This is the core of the race condition logic.
                    # It waits on the result_queue for a maximum of timeout_sec.
                    # If a result is put on the queue by the checker_task, it returns immediately.
                    # If not, it will raise a queue. Empty exception, indicating a timeout.
                    return result_queue.get(timeout=timeout_sec)
                except queue.Empty:
                    logger.warning(f"Attempt {attempt+1}/{retries}: Operation timed out after {timeout_sec} seconds. No validated package found.")
                    on_timeout()
                    continue
        except Exception as e:
            logger.error(f"An error occurred during OCR processing: {e}", exc_info=True)
            return {"status": "error"}
        finally:
            # This cleanup is crucial. It ensures that no matter how the function exits
            # (success or timeout), the background threads are properly stopped.
            logger.info("Cleaning up resources and stopping threads...")
            stop_event.set()
            if self.cap:
                self.cap.release()
                self.cap = None
            cv2.destroyAllWindows()

            processor.join(timeout=1.0) # Give the processor a moment to close the camera
            checker.join(timeout=1.0) # Give the checker a moment to finish
            if processor.is_alive():
                logger.warning("Processor thread did not shut down cleanly.")
            if checker.is_alive():
                logger.warning("Checker thread did not shut down cleanly.")
            if self.start_time:
                logger.info(f"Total processing time: {time.time() - self.start_time:.2f} seconds")

        return {"status": "timeout"}



