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


    def get_primary_face_data(self, frame_bgr, align=True):
        if frame_bgr is None: return None, None, None
        detected_faces_data = self.detector.detect_faces(frame_bgr, align=align, return_regions=True)
        if not detected_faces_data:
            return None, None, None

        face_crop_np_rgb_float, region = detected_faces_data[0]['face'], detected_faces_data[0]['facial_area']
        embedding = self.recognizer._generate_embedding(face_crop_np_rgb_float)
        
        if embedding is None:
            return face_crop_np_rgb_float, None, region
        return face_crop_np_rgb_float, embedding, region

    def capture_registration_sequence(self, camera_manager_instance, num_images=3):
        face_crops_for_reg = []
        embeddings_for_reg = []
        
        self._speak(f"Please look at the camera. I will take {num_images} pictures for registration.")
        
        # Calculate how long to show each "stay still" message based on total duration and num_images
        total_duration = self.config.REGISTRATION_PHOTO_CAPTURE_DURATION
        time_per_photo_segment = total_duration / num_images
        
        for i in range(num_images):
            self._speak(f"Picture {i+1}. Please hold still.")
            
            # Display "Stay Still" for a portion of the segment, then capture
            time.sleep(max(0.5, time_per_photo_segment - 1.5)) # Allow time for prompt, then capture near end of segment
            
            frame = camera_manager_instance.capture_still_frame()
            if frame is None:
                self._speak("I couldn't capture an image. Let's try that picture again.")
                # Simple retry for the current picture (could be more robust)
                time.sleep(1)
                frame = camera_manager_instance.capture_still_frame()
                if frame is None:
                    print(f"FP: Failed to capture frame {i+1} for registration after retry.")
                    continue # Skip this picture

            face_crop, embedding, region = self.get_primary_face_data(frame)

            if face_crop is not None and embedding is not None:
                face_crops_for_reg.append(face_crop)
                embeddings_for_reg.append(embedding)
                print(f"FP: Captured registration image {i+1} and extracted embedding.")
            else:
                self._speak("I couldn't get a clear face for that picture. Please ensure you are looking at the camera.")
                print(f"FP: Failed to get valid face data for registration image {i+1}.")
            
        if len(embeddings_for_reg) < num_images // 2 and num_images > 1 : # Heuristic: if less than half succeeded
             self._speak("I had trouble getting enough clear pictures for a good registration.")
        elif not embeddings_for_reg:
             self._speak("Unfortunately, I could not capture any clear pictures for registration.")


        return face_crops_for_reg, embeddings_for_reg

    # process_frame_for_recognition and run_realtime_recognition can remain as you had them
    # for testing the recognizer with a live feed.