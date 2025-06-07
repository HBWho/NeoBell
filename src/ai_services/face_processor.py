import cv2
import time
import numpy as np # For dummy frame
from .face_detector import FaceDetector # Relative import
from .face_recognizer import FaceRecognizer # Relative import
# Assuming tts_service is passed or a local speak function is used for its prompts

# Temporary speak function if TTSService is not passed to methods needing it
def _internal_speak(text): print(f"FP TTS (internal): {text}")

class FaceProcessor:
    def __init__(self, config):
        self.config = config
        self.detector = FaceDetector(detector_backend=config.FACE_DETECTOR_BACKEND)
        self.recognizer = FaceRecognizer(
            model_name=config.FACE_RECOGNITION_MODEL_NAME,
            distance_metric=config.FACE_DISTANCE_METRIC,
            known_faces_dir=config.KNOWN_FACES_DB_DIR,
            embeddings_db_path=config.FACE_EMBEDDINGS_DB_PATH
        )
        self.frame_count = 0
        self.tts_service = None # Can be set via method
        print("FaceProcessor initialized.")

    def set_tts_service(self, tts_service):
        self.tts_service = tts_service

    def _speak(self, text):
        if self.tts_service:
            self.tts_service.speak(text)
        else:
            _internal_speak(text)


    # def get_primary_face_data(self, frame_bgr, align=True):
    #     if frame_bgr is None: return None, None, None
    #     detected_faces_data = self.detector.detect_faces(frame_bgr, align=align, return_regions=True)
    #     if not detected_faces_data:
    #         return None, None, None

    #     face_crop_np_rgb_float, region = detected_faces_data[0]['face'], detected_faces_data[0]['facial_area']
    #     embedding = self.recognizer._generate_embedding(face_crop_np_rgb_float)
        
    #     if embedding is None:
    #         return face_crop_np_rgb_float, None, region
    #     return face_crop_np_rgb_float, embedding, region
    def get_primary_face_data(self, frame_bgr, align=True, source_call="unknown"): # Added source_call for logging
        if frame_bgr is None:
            print(f"FP DEBUG ({source_call}): get_primary_face_data received None frame.")
            return None, None, None
        
        print(f"FP DEBUG ({source_call}): Attempting to detect faces in frame of shape {frame_bgr.shape}...")
        # Temporarily save the frame being processed for inspection
        # cv2.imwrite(f"debug_frame_{source_call}_{int(time.time())}.jpg", frame_bgr)

        detected_faces_data = self.detector.detect_faces(frame_bgr, align=align, return_regions_only=False) # Get full output

        if not detected_faces_data:
            print(f"FP DEBUG ({source_call}): No faces detected by self.detector.detect_faces().")
            # cv2.imwrite(f"debug_no_face_detected_{source_call}_{int(time.time())}.jpg", frame_bgr) # Save frame where no face was found
            return None, None, None
        
        print(f"FP DEBUG ({source_call}): Detected {len(detected_faces_data)} face(s). Processing first one.")
        # For DeepFace extract_faces, each item in list is a dict
        # {'face': face_array, 'facial_area': region_dict, 'confidence': score}
        first_face_output = detected_faces_data[0]
        face_crop_np_rgb_float = first_face_output['face']
        region = first_face_output['facial_area']
        confidence = first_face_output['confidence']
        print(f"FP DEBUG ({source_call}): First face - Region: {region}, Confidence: {confidence:.4f}")

        if not isinstance(face_crop_np_rgb_float, np.ndarray) or face_crop_np_rgb_float.size == 0:
            print(f"FP DEBUG ({source_call}): Detected face crop is invalid or empty.")
            # cv2.imwrite(f"debug_invalid_crop_frame_{source_call}_{int(time.time())}.jpg", frame_bgr)
            # if isinstance(face_crop_np_rgb_float, np.ndarray):
            #     cv2.imwrite(f"debug_invalid_crop_itself_{source_call}_{int(time.time())}.jpg", face_crop_np_rgb_float) # This might fail if not image
            return None, None, region # Return region even if crop/embedding fails

        # Temporarily save the face crop for inspection
        # temp_crop_bgr = cv2.cvtColor(face_crop_np_rgb_float, cv2.COLOR_RGB2BGR)
        # if temp_crop_bgr.max() <= 1.0 + 1e-6 : temp_crop_bgr = (temp_crop_bgr * 255).astype(np.uint8)
        # cv2.imwrite(f"debug_face_crop_{source_call}_{int(time.time())}.jpg", temp_crop_bgr)
        
        print(f"FP DEBUG ({source_call}): Attempting to generate embedding for the detected face crop...")
        embedding = self.recognizer._generate_embedding(face_crop_np_rgb_float)
        
        if embedding is None:
            print(f"FP DEBUG ({source_call}): Embedding generation failed for the face crop.")
            return face_crop_np_rgb_float, None, region # Return crop even if embedding fails
            
        print(f"FP DEBUG ({source_call}): Embedding generated successfully.")
        return face_crop_np_rgb_float, embedding, region

    # def capture_registration_sequence(self, camera_manager_instance, num_images=3):
    #     face_crops_for_reg = []
    #     embeddings_for_reg = []
        
    #     self._speak(f"Please look at the camera. I will take {num_images} pictures for registration.")
        
    #     # Calculate how long to show each "stay still" message based on total duration and num_images
    #     total_duration = self.config.REGISTRATION_PHOTO_CAPTURE_DURATION
    #     time_per_photo_segment = total_duration / num_images
        
    #     for i in range(num_images):
    #         self._speak(f"Picture {i+1}. Please hold still.")
            
    #         # Display "Stay Still" for a portion of the segment, then capture
    #         time.sleep(max(0.5, time_per_photo_segment - 1.5)) # Allow time for prompt, then capture near end of segment
            
    #         frame = camera_manager_instance.capture_still_frame()
    #         if frame is None:
    #             self._speak("I couldn't capture an image. Let's try that picture again.")
    #             # Simple retry for the current picture (could be more robust)
    #             time.sleep(1)
    #             frame = camera_manager_instance.capture_still_frame()
    #             if frame is None:
    #                 print(f"FP: Failed to capture frame {i+1} for registration after retry.")
    #                 continue # Skip this picture

    #         face_crop, embedding, region = self.get_primary_face_data(frame)

    #         if face_crop is not None and embedding is not None:
    #             face_crops_for_reg.append(face_crop)
    #             embeddings_for_reg.append(embedding)
    #             print(f"FP: Captured registration image {i+1} and extracted embedding.")
    #         else:
    #             self._speak("I couldn't get a clear face for that picture. Please ensure you are looking at the camera.")
    #             print(f"FP: Failed to get valid face data for registration image {i+1}.")
            
    #     if len(embeddings_for_reg) < num_images // 2 and num_images > 1 : # Heuristic: if less than half succeeded
    #          self._speak("I had trouble getting enough clear pictures for a good registration.")
    #     elif not embeddings_for_reg:
    #          self._speak("Unfortunately, I could not capture any clear pictures for registration.")

    #     return face_crops_for_reg, embeddings_for_reg

    def capture_registration_sequence(self, camera_manager_instance, num_images=3):
        face_crops_for_reg = []
        embeddings_for_reg = []
        
        self._speak(f"Please look at the camera. I will take {num_images} pictures for registration.")
        
        total_duration = self.config.REGISTRATION_PHOTO_CAPTURE_DURATION
        time_per_photo_segment = total_duration / num_images
        
        for i in range(num_images):
            self._speak(f"Picture {i+1}. Please hold still.")
            time.sleep(max(0.5, time_per_photo_segment - 1.0))
            
            print(f"FP DEBUG (RegSeq {i+1}): Capturing frame via camera_manager...")
            frame = camera_manager_instance.capture_still_frame()
            
            if frame is None:
                self._speak("I couldn't capture an image from the camera for that picture.")
                print(f"FP ERROR (RegSeq {i+1}): camera_manager.capture_still_frame() returned None.")
                continue 

            print(f"FP DEBUG (RegSeq {i+1}): Frame captured, processing for face data...")
            face_crop_rgb_float, embedding, region = self.get_primary_face_data(frame, source_call=f"RegSeq_{i+1}") # Renamed for clarity

            if face_crop_rgb_float is not None and embedding is not None:
                face_crops_for_reg.append(face_crop_rgb_float) # Store the original RGB float crop
                embeddings_for_reg.append(embedding)
                print(f"FP SUCCESS (RegSeq {i+1}): Captured registration image and extracted embedding.")

                if self.config.APP_DEBUG_MODE:
                    try:
                        # --- START FIX FOR DISPLAY ---
                        # 1. Ensure float32 if it's float64
                        if face_crop_rgb_float.dtype == np.float64:
                            img_to_display_float32 = face_crop_rgb_float.astype(np.float32)
                        else:
                            img_to_display_float32 = face_crop_rgb_float
                        
                        # 2. Scale if it's normalized (0-1) and convert to uint8
                        # DeepFace extract_faces usually returns RGB float (0-1)
                        if img_to_display_float32.min() >= 0 and img_to_display_float32.max() <= 1.0 + 1e-5:
                            img_to_display_uint8_rgb = (img_to_display_float32 * 255).astype(np.uint8)
                        elif img_to_display_float32.min() >=0 and img_to_display_float32.max() <= 255 + 1e-5 and img_to_display_float32.dtype != np.uint8:
                            img_to_display_uint8_rgb = img_to_display_float32.astype(np.uint8)
                        elif img_to_display_float32.dtype == np.uint8:
                            img_to_display_uint8_rgb = img_to_display_float32 # Already uint8 RGB
                        else:
                            print(f"FP DEBUG: Reg crop {i+1} has unexpected float range or type for display. Skipping display.")
                            continue # Skip display for this problematic crop

                        # 3. Convert RGB uint8 to BGR uint8 for OpenCV display
                        display_crop_bgr_uint8 = cv2.cvtColor(img_to_display_uint8_rgb, cv2.COLOR_RGB2BGR)
                        # --- END FIX FOR DISPLAY ---

                        # cv2.imshow(f"Registration Capture {i+1}", display_crop_bgr_uint8)
                        cv2.waitKey(500) 
                        cv2.destroyWindow(f"Registration Capture {i+1}")
                    except Exception as e_disp:
                        print(f"FP DEBUG: Error displaying reg crop: {e_disp}")
                        import traceback
                        traceback.print_exc() # Print full traceback for display error
            else:
                self._speak("I couldn't get a clear face for that picture. Please ensure you are looking at the camera.")
                print(f"FP FAILED (RegSeq {i+1}): Failed to get valid face_crop or embedding. Crop: {'Valid' if face_crop_rgb_float is not None else 'None'}, Embedding: {'Valid' if embedding is not None else 'None'}")
            
        # ... (rest of the function) ...
        if len(embeddings_for_reg) < num_images // 2 +1  and num_images > 0 : 
             self._speak("I had trouble getting enough clear pictures for a good registration.")
        elif not embeddings_for_reg and num_images > 0:
             self._speak("Unfortunately, I could not capture any clear pictures for registration.")
        elif embeddings_for_reg:
             self._speak("Photo capture complete.")
        return face_crops_for_reg, embeddings_for_reg


