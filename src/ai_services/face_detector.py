from deepface import DeepFace
import cv2 # OpenCV for image handling, though DeepFace often handles it internally
import numpy as np # For numpy array checks

class FaceDetector:
    def __init__(self, detector_backend='retinaface'):
        """
        Initializes the FaceDetector.

        Args:
            detector_backend (str): The face detection backend to use with DeepFace.
                Options: 'opencv', 'ssd', 'dlib', 'mtcnn', 'retinaface', 'mediapipe', 'yolov8'.
                'retinaface' is generally robust.
        """
        self.detector_backend = detector_backend
        # Pre-load models if beneficial, but DeepFace usually handles this on first use.
        # You can trigger a first use here if startup time is critical later:
        # try:
        #     print(f"FaceDetector: Pre-warming detector '{self.detector_backend}'...")
        #     DeepFace.extract_faces(img_path=np.zeros((100,100,3), dtype=np.uint8), 
        #                            detector_backend=self.detector_backend, 
        #                            enforce_detection=False)
        #     print(f"FaceDetector: Detector '{self.detector_backend}' pre-warmed.")
        # except Exception as e:
        #     print(f"FaceDetector: Warning - Could not pre-warm detector '{self.detector_backend}': {e}")
        print(f"FaceDetector initialized with backend: {self.detector_backend}")

    def detect_faces(self, image_np, align=True, return_regions_only=False):
        """
        Detects faces in a BGR NumPy image array.

        Args:
            image_np (np.ndarray): NumPy array representing the image (expected in BGR format).
            align (bool): Whether to perform facial alignment (recommended for better recognition).
            return_regions_only (bool): If True, returns only a list of region_dict.
                                       If False, returns list of dicts with 'face' (np.array) and 'facial_area'.

        Returns:
            If return_regions_only is False:
                A list of dictionaries. Each dictionary corresponds to a detected face and contains:
                - 'face': NumPy array of the cropped and aligned face image (RGB, float 0-1).
                - 'facial_area': dict with 'x', 'y', 'w', 'h' for the bounding box in the original image.
                - 'confidence': detection confidence score.
            If return_regions_only is True:
                A list of dictionaries, each containing 'x', 'y', 'w', 'h', 'confidence'.
            Returns an empty list if no faces are found or an error occurs.
        """
        if not isinstance(image_np, np.ndarray):
            print("FaceDetector ERROR: Input image_np is not a NumPy array.")
            return []
        if image_np.size == 0:
            print("FaceDetector ERROR: Input image_np is empty.")
            return []

        try:
            # DeepFace.extract_faces expects img_path to be a path or a BGR numpy array.
            # It returns a list of dictionaries.
            # Each dict: {'face': np.array (RGB, float 0-1), 
            #             'facial_area': {'x': int, 'y': int, 'w': int, 'h': int}, 
            #             'confidence': float}
            
            detected_outputs_list = DeepFace.extract_faces(
                img_path=image_np, # Pass the BGR numpy array directly
                detector_backend=self.detector_backend,
                align=align,
                enforce_detection=False # Don't raise exception if no face, just return empty list
            )

            if return_regions_only:
                regions = []
                for output in detected_outputs_list:
                    # Ensure confidence is present and positive before adding
                    if output.get('confidence', 0) > 0: # Default to 0 if confidence key missing
                        regions.append(output['facial_area'])
                        regions[-1]['confidence'] = output['confidence'] # Add confidence to region dict
                return regions
            else:
                # Filter out results where face extraction might have failed internally or low confidence
                valid_faces = []
                for output in detected_outputs_list:
                    if isinstance(output.get('face'), np.ndarray) and output.get('confidence', 0) > 0:
                        valid_faces.append(output)
                return valid_faces

        except ValueError as ve: # Catch specific errors from DeepFace if input is problematic
            print(f"FaceDetector ValueError: {ve}. This might be due to image format or content.")
            return []
        except Exception as e:
            # print(f"FaceDetector ERROR: Unexpected error during face detection: {e}") # Can be noisy
            return []

# This block runs ONLY when you execute `python face_detector.py` directly
if __name__ == '__main__':
    # --- Configuration for Test ---
    # !!! REPLACE with the actual path to your config.py !!!
    # This assumes config.py is in the project root, and ai_services is a subdir.
    import sys
    import os
    _CURRENT_DIR_FD = os.path.dirname(os.path.abspath(__file__))
    _PROJECT_ROOT_FD = os.path.dirname(_CURRENT_DIR_FD) # Up one level to ai_services parent
    if _PROJECT_ROOT_FD not in sys.path:
        sys.path.insert(0, _PROJECT_ROOT_FD)
    try:
        import config as app_config
    except ImportError:
        print("ERROR __main__: config.py not found. Please ensure it's in the project root.")
        # Define fallbacks if config.py is not found for basic testing
        class FallbackConfig:
            FACE_DETECTOR_BACKEND = 'mtcnn' # MTCNN is often available with DeepFace
            KNOWN_FACES_DB_DIR = "data/known_faces_db" # Adjust if your structure is different
        app_config = FallbackConfig()
        # Create a dummy known_faces_db for the test image path if it doesn't exist
        dummy_person_path = os.path.join(app_config.KNOWN_FACES_DB_DIR, "person_test")
        os.makedirs(dummy_person_path, exist_ok=True)
        # Create a dummy image if one doesn't exist for testing
        img_path_for_test = os.path.join(dummy_person_path, "test_img.jpg")
        if not os.path.exists(img_path_for_test):
            cv2.imwrite(img_path_for_test, np.zeros((200,200,3), dtype=np.uint8)) # Black image
    # --- End Configuration for Test ---


    detector = FaceDetector(detector_backend=app_config.FACE_DETECTOR_BACKEND)
    
    # Try to find an image in the known_faces_db for testing
    # This requires KNOWN_FACES_DB_DIR to be set in config and have images
    test_image_found = False
    if os.path.exists(app_config.KNOWN_FACES_DB_DIR):
        for root, dirs, files in os.walk(app_config.KNOWN_FACES_DB_DIR):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    img_path = os.path.join(root, file)
                    test_image_found = True
                    break
            if test_image_found:
                break
    
    if not test_image_found:
        # Fallback to a generic placeholder if no image is found in DB
        # Create a dummy image if it doesn't exist
        img_path = "test_face_image.jpg" 
        if not os.path.exists(img_path):
            print(f"No test image found in DB, creating dummy image: {img_path}")
            # Create a simple image with a drawn circle "face" for testing
            dummy_frame = np.full((480, 640, 3), (100, 100, 100), dtype=np.uint8)
            cv2.circle(dummy_frame, (320, 240), 80, (200, 200, 255), -1) # A light "face"
            cv2.imwrite(img_path, dummy_frame)
        print(f"No image found in {app_config.KNOWN_FACES_DB_DIR}. Using placeholder: {img_path}")


    print(f"\n--- Testing FaceDetector with image: {img_path} ---")
    try:
        frame = cv2.imread(img_path)
        if frame is None:
            print(f"Could not read image from {img_path}")
        else:
            print(f"Input image shape: {frame.shape}")
            
            # Test 1: Get face crops and regions
            detected_outputs = detector.detect_faces(frame, align=True, return_regions_only=False)
            
            if detected_outputs:
                print(f"\nDetected {len(detected_outputs)} face(s) with crops and regions:")
                for i, output_data in enumerate(detected_outputs):
                    face_img_np_rgb_float = output_data['face']
                    region = output_data['facial_area']
                    confidence = output_data['confidence']
                    
                    print(f"  Face {i+1}: Region={region}, Confidence={confidence:.4f}, Crop Shape={face_img_np_rgb_float.shape}, Crop Dtype={face_img_np_rgb_float.dtype}")

                    # Display the cropped face (DeepFace returns RGB, float 0-1)
                    face_to_show = cv2.cvtColor(face_img_np_rgb_float, cv2.COLOR_RGB2BGR)
                    if face_to_show.max() <= 1.0 + 1e-6: # Check if it's normalized
                        face_to_show = (face_to_show * 255).astype(np.uint8)
                    else: # Assume it's already 0-255 if max > 1 (less likely from DeepFace extract_faces)
                        face_to_show = face_to_show.astype(np.uint8)
                    
                    cv2.imshow(f"Detected Face Crop {i+1}", face_to_show)

                    # Draw bounding box on original frame
                    x, y, w, h = region['x'], region['y'], region['w'], region['h']
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, f"Conf: {confidence:.2f}", (x, y-5 if y-5 > 5 else y+h+15), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)

                cv2.imshow("Original Frame with Detections", frame)
                print("\nPress any key on an image window to continue...")
                cv2.waitKey(0)
                cv2.destroyAllWindows()
            else:
                print("No faces detected by detect_faces().")

            # Test 2: Get regions only
            # print("\n--- Testing detect_faces with return_regions_only=True ---")
            # regions_only = detector.detect_faces(frame, align=False, return_regions_only=True)
            # if regions_only:
            #     print(f"Detected {len(regions_only)} region(s):")
            #     for i, region in enumerate(regions_only):
            #         print(f"  Region {i+1}: {region}")
            # else:
            #     print("No regions detected with return_regions_only=True.")

    except Exception as e:
        print(f"Error in FaceDetector example usage: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cv2.destroyAllWindows()