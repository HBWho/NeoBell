import os
import time
import logging
from pathlib import Path
from collections import Counter

import cv2
import numpy as np
import pandas as pd
from deepface import DeepFace

from ai_services.camera_manager import CameraManager 

# Configure logging to show info messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants for Face Recognition ---
MODEL_NAME = "Facenet" 
DETECTOR = "opencv"
THRESHOLD = 0.30  # Facenet uses a different distance metric; 0.40 is a common threshold for it.

class FaceProcessing:
    def __init__(self, camera_manager: CameraManager):
        """
        Initializes the FaceProcessing class with a dependency on a CameraManager.
        """
        self.camera_manager = camera_manager

    def register_face_simple(self, camera_id: int, user_folder: Path, num_photos: int = 3) -> bool:
        """
        Captures photos for registration, now intelligently handling multiple faces
        by selecting the closest one.
        """
        logger.info(f"--- Starting Simple Registration for {user_folder.name} ---")
        user_folder.mkdir(exist_ok=True)
        captured_images, photos_saved, max_retries = [], 0, 3
        
        for i in range(num_photos):
            print(f"\nTaking photo {i + 1} of {num_photos}...")
            is_photo_saved = False
            for attempt in range(max_retries):
                print(f"Attempt {attempt + 1}. Please look at the camera.")
                time.sleep(2)
                temp_image_path = f"temp_reg_{i}.jpg"
                
                if not self.camera_manager.take_picture(camera_id, temp_image_path):
                    continue
                
                is_good, result = self._is_photo_quality_good(temp_image_path)

                if is_good:
                    best_face_data = result # This is now the dict for the best face
                    try:
                        # The face is already cropped and aligned, just convert and save
                        final_face_img = (best_face_data['face'] * 255).astype(np.uint8)
                        final_path = str(user_folder / f"image_{i}.jpg")
                        cv2.imwrite(final_path, cv2.cvtColor(final_face_img, cv2.COLOR_RGB2BGR))
                        
                        captured_images.append(final_path)
                        logger.info(f"✅ Saved high-quality face to {final_path}")
                        is_photo_saved = True
                        photos_saved += 1
                        break # Success, move to the next photo
                    except Exception as e:
                        print(f"Could not save extracted face, let's try again. Error: {e}")
                else:
                    # 'result' is now the reason string for failure
                    print(f"❌ Quality check failed: {result}. Let's try that again.")
                
                Path(temp_image_path).unlink(missing_ok=True)

            if not is_photo_saved:
                logger.error(f"Failed to capture a quality photo #{i+1} after all attempts.")
                self._cleanup_failed_registration(user_folder, captured_images)
                return False
        
        return photos_saved == num_photos

    def analyze_live_stream(
        self, camera_id: int, db_path: str, timeout_seconds: int = 5, display_window: bool = False, save_sighting_path: str | None = None
    ) -> tuple[str, str | None]:
        logger.info("Starting live stream analysis...")
        cap = self.camera_manager.open_camera(camera_id)

        if save_sighting_path: os.makedirs(save_sighting_path, exist_ok=True)
        if display_window: cv2.namedWindow("Live Recognition", cv2.WINDOW_NORMAL)
        start_time, seen_states, known_person_buffer = time.time(), [], {}
        display_status = "Status: INITIALIZING..."
        
        try:
            while time.time() - start_time < timeout_seconds:
                ret, frame = cap.read()
                if not ret: break

                # Get frame dimensions for the size check
                frame_h, frame_w, _ = frame.shape
                frame_area = frame_h * frame_w

                faces_to_draw = []
                try:
                    dfs = DeepFace.find(img_path=frame, db_path=db_path, model_name=MODEL_NAME, detector_backend=DETECTOR, enforce_detection=False, silent=True)
                    valid_dfs = []
                    if dfs:
                        for df in dfs:
                            if not df.empty:
                                w, h = df['source_w'].iloc[0], df['source_h'].iloc[0]
                                # NEW: Bounding Box Size Check
                                if (w * h) / frame_area < 0.75:
                                    valid_dfs.append(df)
                                else:
                                    logger.warning("Rejected a face detection because it was too large.")
                    
                    faces_to_draw = valid_dfs
                    closest_face_df = max(faces_to_draw, key=lambda df: df['source_w'].iloc[0] * df['source_h'].iloc[0], default=None)

                    if closest_face_df is not None:
                        is_known, user_id = self._get_match_for_face(closest_face_df)
                        if is_known:
                            known_person_buffer[user_id] = known_person_buffer.get(user_id, 0) + 1
                            display_status = f"Status: DETECTED KNOWN PERSON ({user_id})"
                            if known_person_buffer[user_id] >= 10: # Stricter consensus
                                if save_sighting_path:
                                    filename = f"{time.strftime('%Y%m%d_%H%M%S')}_{user_id}.jpg"
                                    filepath = os.path.join(save_sighting_path, filename)
                                    cv2.imwrite(filepath, frame)
                                    logger.info(f"✅ Saved sighting snapshot to {filepath}")
                                return "KNOWN_PERSON", user_id
                            seen_states.append("KNOWN_PERSON")
                        else:
                            display_status = "Status: DETECTED UNKNOWN PERSON"
                            seen_states.append("UNKNOWN_PERSON")
                    else:
                        display_status = "Status: NO FACE DETECTED"
                        seen_states.append("NO_FACE")
        

                except Exception as e:
                    if "No item found" in str(e):
                        display_status = "Status: DB EMPTY - Looking for new faces"
                        try:
                            # Use extract_faces to find faces for drawing when DB is empty
                            extracted_faces = DeepFace.extract_faces(frame, enforce_detection=True, detector_backend=DETECTOR)
                            if extracted_faces:
                                faces_to_draw = extracted_faces
                                seen_states.append("UNKNOWN_PERSON")
                        except ValueError:
                            seen_states.append("NO_FACE")
                    else:
                        display_status = "Status: SYSTEM ERROR"
                        logger.error(f"An unexpected error occurred: {e}")
                        seen_states.append("NO_FACE")
                        time.sleep(1)

                if display_window:
                    for face_data in faces_to_draw:
                        # Handle DataFrame from find() vs dict from extract_faces()
                        if isinstance(face_data, pd.DataFrame):
                            is_rec, user_id = self._get_match_for_face(face_data)
                            label = str(user_id) if is_rec else "Unknown"
                            color = (0, 255, 0) if is_rec else (0, 0, 255)
                            x, y, w, h = face_data['source_x'].iloc[0], face_data['source_y'].iloc[0], face_data['source_w'].iloc[0], face_data['source_h'].iloc[0]
                        else: # It's a dict from extract_faces
                            label, color = "Unknown", (0, 0, 255)
                            area = face_data['facial_area']
                            x, y, w, h = area['x'], area['y'], area['w'], area['h']
                        
                        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                        cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                    cv2.putText(frame, display_status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.imshow("Live Recognition", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'): break
        finally:
            cap.release()
            if display_window: cv2.destroyAllWindows()

        if not seen_states: return "NO_FACE", None
        if "UNKNOWN_PERSON" in seen_states:
            logger.info("Timeout reached. An unknown person was detected.")
            return "UNKNOWN_PERSON", None
        else:
            logger.info("Timeout reached. No face was detected.")
            return "NO_FACE", None

    # --- Private Helper Methods ---
    def _get_match_for_face(self, df: pd.DataFrame) -> tuple[bool, str | None]:
        if df.empty: return False, None
        df = df[df["distance"] < THRESHOLD].copy()
        if df.empty: return False, None
        df["person"] = df["identity"].apply(lambda x: Path(x).parent.name)
        best_match_idx = df["distance"].idxmin()
        return True, str(df.loc[best_match_idx, "person"])
    
    def _is_photo_quality_good(self, image_path: str) -> tuple[bool, str]:
        """
        Checks photo quality. If multiple faces are found, it selects the largest one
        and checks its quality.
        
        Returns:
            (True, face_object) if quality is good.
            (False, reason_string) if quality is bad.
        """
        try:
            faces = DeepFace.extract_faces(image_path, enforce_detection=False, detector_backend=DETECTOR)
            
            if not faces:
                return False, "No face could be detected."

            # Find the face with the largest area
            best_face = max(faces, key=lambda face: face['facial_area']['w'] * face['facial_area']['h'])
            
            # Check blur and lighting on the *cropped face* for better accuracy
            cropped_face_img = (best_face['face'] * 255).astype(np.uint8)
            gray_face = cv2.cvtColor(cropped_face_img, cv2.COLOR_RGB2GRAY)
            
            if self._is_image_blurry(gray_face, threshold=50.0): # Stricter threshold for cropped faces
                return False, "The clearest face is too blurry."
            
            if not self._is_image_well_lit(gray_face, min_brightness=50, max_brightness=210):
                return False, "The clearest face is too dark or overexposed."

        except Exception as e:
            return False, f"An unexpected error occurred: {e}"
        
        logger.info(f"Found {len(faces)} face(s). Selected the largest one for quality check.")
        return True, best_face
        

    def _is_image_blurry(self, gray_image: np.ndarray, threshold: float) -> bool:
        variance = cv2.Laplacian(gray_image, cv2.CV_64F).var()
        return variance < threshold

    def _is_image_well_lit(self, gray_image: np.ndarray, min_brightness: int, max_brightness: int) -> bool:
        mean_brightness = np.mean(gray_image)
        return min_brightness < mean_brightness < max_brightness
        
    def _cleanup_failed_registration(self, user_folder: Path, captured_images: list):
        logger.warning(f"Registration failed. Cleaning up files for {user_folder.name}...")
        for img_path in captured_images: Path(img_path).unlink(missing_ok=True)
        try: user_folder.rmdir()
        except OSError: logger.warning(f"Could not remove directory {user_folder}.")

    def run_visual_quality_debugger(self, camera_id: int):
        """Opens a live camera feed to provide real-time feedback on photo quality."""
        cap = self.camera_manager.open_camera(camera_id)
        
        cv2.namedWindow("Visual Quality Debugger", cv2.WINDOW_NORMAL)
        print("\n--- Visual Quality Debugger ---\nPress 'q' to quit.")

        while True:
            ret, frame = cap.read()
            if not ret: break
            
            frame_h, frame_w, _ = frame.shape
            frame_area = frame_h * frame_w
            display_frame = frame.copy()

            try:
                faces = DeepFace.extract_faces(frame, detector_backend=DETECTOR, enforce_detection=False)
                face_count = len(faces)
                
                if face_count > 0:
                    best_face = max(faces, key=lambda face: face['facial_area']['w'] * face['facial_area']['h'])
                    x, y, w, h = best_face['facial_area']['x'], best_face['facial_area']['y'], best_face['facial_area']['w'], best_face['facial_area']['h']
                    
                    # NEW: Bounding Box Size Check
                    if (w * h) / frame_area > 0.75:
                        cv2.putText(display_frame, "Detection too large (Rejected)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                    else:
                        cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        # (Other quality check displays can go here)
                        cv2.putText(display_frame, f"Face Detected (GOOD)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    cv2.putText(display_frame, "No Face Detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            except Exception: pass
            cv2.imshow("Visual Quality Debugger", display_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break
        
        cap.release()
        cv2.destroyAllWindows()
        


def main():
    """Main function to test the new, decoupled structure."""
    CAMERA_ID, DB_PATH = 0, "data/known_faces_db"
    SIGHTINGS_PATH = "data/sightings"
    if not os.path.isdir(DB_PATH): os.makedirs(DB_PATH)

    # MODIFIED: The main function now creates and injects the CameraManager
    
    # 1. Create the single CameraManager instance
    camera_manager = CameraManager()
    
    # 2. Pass that instance to the FaceProcessing class
    face_processor = FaceProcessing(camera_manager)
    
    print("What would you like to do?")
    print("1. Register a new person")
    print("2. Recognize a person")
    print("3. Debug photo quality (Visual Tool)")
    choice = input("Enter your choice (1, 2, or 3): ")
    
    # (The rest of the logic remains the same)
    if choice == '1':
        user_id = input("Enter a unique name or ID for the new person: ").strip()
        if user_id:
            face_processor.register_face_simple(camera_id=CAMERA_ID, user_folder=Path(DB_PATH) / user_id, num_photos=3)
        else: print("User ID cannot be empty.")
    elif choice == '2':
        face_processor.analyze_live_stream(camera_id=CAMERA_ID, db_path=DB_PATH, timeout_seconds=20, display_window=True, save_sighting_path=SIGHTINGS_PATH)
    elif choice == '3':
        face_processor.run_visual_quality_debugger(camera_id=CAMERA_ID)
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()