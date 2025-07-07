import os
import time
import logging
from pathlib import Path
from collections import Counter

import cv2
import numpy as np
import pandas as pd
from deepface import DeepFace

from services.camera_manager import CameraManager 
from phrases import VISITOR

# Configure logging to show info messages
logger = logging.getLogger(__name__)

# --- Constants for Face Recognition ---
MODEL_NAME = "Facenet" 
DETECTOR = "opencv"
THRESHOLD = 0.20  # Facenet uses a different distance metric; 0.40 is a common threshold for it.

class FaceProcessing:
    def __init__(self, camera_manager: CameraManager):
        """
        Initializes the FaceProcessing class with a dependency on a CameraManager.
        """
        self.camera_manager = camera_manager

    def register_face_in_batch(
        self, camera_id: int, user_folder: Path, gpio, tts, num_photos_per_set: int = 5
    ) -> bool:
        """
        Captures a batch of photos with and without LED, then processes them all at once.
        """
        logger.info(f"--- Starting Batch Registration for {user_folder.name} ---")
        user_folder.mkdir(exist_ok=True)
        temp_image_paths = []
        
        try:
            # --- CAPTURE PHASE ---
            # Set 1: LED OFF
            tts.speak_async(VISITOR["register_photo_wo_lighting"])
            gpio.set_camera_led(False)
            time.sleep(2) # Give user time to prepare
            for i in range(num_photos_per_set):
                logger.info(f"Capturing LED OFF image {i+1}...")
                temp_path = str(user_folder / f"temp_led_off_{i}.jpg")
                if self.camera_manager.take_picture(camera_id, temp_path):
                    temp_image_paths.append(temp_path)
                time.sleep(0.5) # Small delay between shots

            # Set 2: LED ON
            tts.speak_async(VISITOR["register_photo_w_lighting"])
            gpio.set_camera_led(True)
            time.sleep(1.5) # Give LED time to turn on fully
            for i in range(num_photos_per_set):
                logger.info(f"Capturing LED ON image {i+1}...")
                temp_path = str(user_folder / f"temp_led_on_{i}.jpg")
                if self.camera_manager.take_picture(camera_id, temp_path):
                    temp_image_paths.append(temp_path)
                time.sleep(0.5)

        finally:
            gpio.set_camera_led(False) # Always ensure LED is off after capture

        # --- PROCESSING PHASE ---
        tts.speak_async(VISITOR["register_photo_complete"])
        
        good_faces = []
        for image_path in temp_image_paths:
            is_good, result = self._is_photo_quality_good(image_path)
            if is_good:
                good_faces.append(result) # result is the face_data dict
        
        # Clean up all temporary full-size images
        for image_path in temp_image_paths:
            Path(image_path).unlink(missing_ok=True)
            
        logger.info(f"Found {len(good_faces)} high-quality faces out of {len(temp_image_paths)} taken.")

        # --- SAVE PHASE ---
        # Require at least 3 good photos to create a valid profile
        MINIMUM_GOOD_PHOTOS = 3
        if len(good_faces) < MINIMUM_GOOD_PHOTOS:
            logger.error(f"Not enough good photos ({len(good_faces)}) to complete registration.")
            self._cleanup_failed_registration(user_folder, []) # Just ensure folder is gone
            return False
            
        # Save the good, aligned faces to the final directory
        for i, face_data in enumerate(good_faces):
            try:
                final_face_img = (face_data['face'] * 255).astype(np.uint8)
                final_path = str(user_folder / f"image_{i}.jpg")
                cv2.imwrite(final_path, cv2.cvtColor(final_face_img, cv2.COLOR_RGB2BGR))
            except Exception as e:
                logger.error(f"Could not save final processed face #{i}: {e}")
        
        logger.info(f"Successfully saved {len(good_faces)} processed faces to user profile.")
        return True

    def analyze_live_stream(
        self, camera_id: int, db_path: str, timeout_seconds: int = 5, display_window: bool = False, save_sighting_path: str | None = None, debug_mode: bool = False
    ) -> tuple[str, str | None]:
        logger.info("Starting live stream analysis...")
        cap = self.camera_manager.open_camera(camera_id)

        if save_sighting_path: os.makedirs(save_sighting_path, exist_ok=True)
        
        # --- DEBUG --- Create debug directory if needed
        if debug_mode:
            debug_path = "data/debug_frames"
            os.makedirs(debug_path, exist_ok=True)
            logger.info(f"--- DEBUG MODE ON: Saving frames to {debug_path} ---")

        if display_window: cv2.namedWindow("Live Recognition", cv2.WINDOW_NORMAL)
        start_time, seen_states, known_person_buffer = time.time(), [], {}
        display_status = "Status: INITIALIZING..."
        
        try:
            while time.time() - start_time < timeout_seconds:
                ret, frame = cap.read()
                if not ret: break

                # --- DEBUG --- Save a snapshot of the frame being analyzed
                if debug_mode:
                    debug_filename = f"data/debug_frames/frame_{time.strftime('%H%M%S')}.jpg"
                    cv2.imwrite(debug_filename, frame)

                frame_h, frame_w, _ = frame.shape
                frame_area = frame_h * frame_w
                faces_to_draw = []

                try:
                    dfs = DeepFace.find(img_path=frame, db_path=db_path, model_name=MODEL_NAME, detector_backend=DETECTOR, enforce_detection=False, silent=True)
                    if debug_mode: logger.info(f"DeepFace.find() returned {len(dfs) if dfs else 0} results.")

                    valid_dfs = []
                    if dfs:
                        for df in dfs:
                            valid_dfs.append(df)
                            # if not df.empty:
                            #     logger.info(f"df: {df}")
                            #     w, h = df['source_w'].iloc[0], df['source_h'].iloc[0]
                            #     if (w * h) / frame_area < 1.00: valid_dfs.append(df)
                            #     else: logger.info("Rejected a face detection because it was too large.")
                    
                    if debug_mode: logger.info(f"Found {len(valid_dfs)} valid faces after filtering.")
                    
                    faces_to_draw = valid_dfs
                    closest_face_df = max(faces_to_draw, key=lambda df: df['source_w'].iloc[0] * df['source_h'].iloc[0], default=None)

                    if closest_face_df is not None:
                        is_known, user_id, distance = self._get_match_for_face(closest_face_df)
                        if is_known:
                            if debug_mode: logger.info(f"✅ Match successful for '{user_id}' with distance {distance:.4f} (Threshold: {THRESHOLD})")
                            known_person_buffer[user_id] = known_person_buffer.get(user_id, 0) + 1
                            display_status = f"Status: DETECTED KNOWN PERSON ({user_id})"
                            if known_person_buffer[user_id] >= 2:
                                if save_sighting_path:
                                    filename = f"{time.strftime('%Y%m%d_%H%M%S')}_{user_id}.jpg"
                                    filepath = os.path.join(save_sighting_path, filename)
                                    cv2.imwrite(filepath, frame)
                                    logger.info(f"✅ Saved sighting snapshot to {filepath}")
                                return "KNOWN_PERSON", user_id
                            seen_states.append("KNOWN_PERSON")
                        else:
                            if debug_mode: logger.info("❌ Match failed. Closest face did not meet threshold.")
                            display_status = "Status: DETECTED UNKNOWN PERSON"
                            seen_states.append("UNKNOWN_PERSON")
                    else:
                        if debug_mode: logger.info("No face was detected or passed filters in this frame.")
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
            self.camera_manager.release_camera(camera_id)
            if display_window: cv2.destroyAllWindows()
        
        if not seen_states: return "NO_FACE", None

        logger.info(f"seen_states: {seen_states}")
        if "UNKNOWN_PERSON" in seen_states:
            logger.info("Timeout reached. An unknown person was detected.")
            return "UNKNOWN_PERSON", None
        else:
            logger.info("Timeout reached. No face was detected.")
            return "NO_FACE", None

    # --- Private Helper Methods ---
    def _get_match_for_face(self, df: pd.DataFrame) -> tuple[bool, str | None, float | None]:
        if df.empty: return False, None, None
        # Find the single best match in the DataFrame before filtering
        best_match_idx = df["distance"].idxmin()
        best_distance = df.loc[best_match_idx, "distance"]
        
        if best_distance < THRESHOLD:
            user_id = Path(df.loc[best_match_idx, "identity"]).parent.name
            return True, str(user_id), float(best_distance)
        
        return False, None, float(best_distance)
    
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
            
            # if not faces:
            #     return False, "No face could be detected."

            # Find the face with the largest area
            best_face = max(faces, key=lambda face: face['facial_area']['w'] * face['facial_area']['h'])
            
            # Check blur and lighting on the *cropped face* for better accuracy
            cropped_face_img = (best_face['face'] * 255).astype(np.uint8)
            gray_face = cv2.cvtColor(cropped_face_img, cv2.COLOR_RGB2GRAY)
            
            # if self._is_image_blurry(gray_face, threshold=50.0): # Stricter threshold for cropped faces
            #     return False, "The clearest face is too blurry."
            
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
        
        cv2.destroyAllWindows()
        


def main():
    """Main function to test the new, decoupled structure."""
    CAMERA_ID, DB_PATH = 2, "data/known_faces_db"
    SIGHTINGS_PATH = "data/sightings"
    if not os.path.isdir(DB_PATH): os.makedirs(DB_PATH) 
    camera_manager = CameraManager()
    face_processor = FaceProcessing(camera_manager)
    
    print("What would you like to do?")
    print("1. Register a new person")
    print("2. Recognize a person")
    print("3. Debug photo quality (Visual Tool)")
    print("4. Run recognition in HEADLESS DEBUG MODE") # NEW
    choice = input("Enter your choice (1, 2, 3, or 4): ")
    
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
    elif choice == '4':
        print("\n--- Running Recognition in Headless Debug Mode ---")
        print("Detailed logs will be printed. Check the 'data/debug_frames' folder for snapshots.")
        face_processor.analyze_live_stream(
            camera_id=CAMERA_ID,
            db_path=DB_PATH,
            timeout_seconds=10,
            display_window=False, # No window will be shown
            debug_mode=True      # Activate detailed logging and frame saving
        )
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
