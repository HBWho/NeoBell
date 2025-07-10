from deepface import DeepFace
from pathlib import Path
import cv2
import time
import pandas as pd
import logging

from services.camera_manager import CameraManager
from phrases import VISITOR

logger = logging.getLogger(__name__)

MODEL_NAME = "ArcFace"
DETECTOR = "mtcnn"
DARK_THRESHOLD = 50
BRIGHT_THRESHOLD = 200
ARCFACE_THRESHOLD = 0.68

class FaceProcessing:
    def __init__(self, camera_manager: CameraManager, db_path: str):
        self.camera_manager = camera_manager
        self.db_path = db_path

    def register_face(self, camera_id: int, user_folder: Path, gpio, tts):
        user_folder.mkdir(exist_ok=True)
        temp_image_paths = []

        try:
            tts.speak("The photo will be taken in 3, 2, 1")

            # Capture image with LED off
            path_led_off = self._capture_and_validate_image(
                camera_id, user_folder, "led_off", led_status=False, gpio=gpio
            )
            if path_led_off:
                temp_image_paths.append(path_led_off)

            # Capture image with LED on
            path_led_on = self._capture_and_validate_image(
                camera_id, user_folder, "led_on", led_status=True, gpio=gpio
            )
            if path_led_on:
                temp_image_paths.append(path_led_on)

        finally:
            gpio.set_camera_led(False)

        if not temp_image_paths:
            tts.speak_async("Sorry, I could not take a good quality photo. Please try again.")
            return False

        for i, temp_path_str in enumerate(temp_image_paths):
            temp_path = Path(temp_path_str)
            final_path = user_folder / f"image_{i}.jpg"
        
            try:
                # Rename led_off.jpg -> image_0.jpg, led_on.jpg -> image_1.jpg, etc.
                temp_path.rename(final_path)
                print(f"Saved final image: {final_path.name}")
            except OSError as e:
                print(f"Error renaming {temp_path.name} to {final_path.name}: {e}")
                # If renaming fails, you might want to handle this error
                return False

        tts.speak_async("Registration photos taken successfully.")
        return True

    def _capture_and_validate_image(self, camera_id, folder, name, led_status, gpio, max_attempts=3):
        gpio.set_camera_led(led_status)
        if led_status:
            time.sleep(0.5) # Give LED time to brighten

        temp_path = str(folder / f"{name}.jpg")
        for _ in range(max_attempts):
            self.camera_manager.take_picture(camera_id, temp_path)
            # Check quality AND if there's a face
            if self.check_img_quality(temp_path) and self.is_there_face(temp_path):
                print(f"✅ Valid photo taken: {name}.jpg")
                return temp_path
            time.sleep(0.5)

        print(f"❌ Failed to take a valid photo for: {name}.jpg")
        return None

    def check_img_quality(self, img_path: str) -> bool:
        img = cv2.imread(img_path)
        if img is None:
            print("Img is none")
            return False

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Check brightness
        mean_intensity = gray.mean()
        print(f"mean_intensity: {mean_intensity}")
        is_good_brightness = (mean_intensity >= DARK_THRESHOLD) and (mean_intensity <= BRIGHT_THRESHOLD)
        if not is_good_brightness:
            return False

        return True

    def is_there_face(self, img_path: str) -> bool:
        try:
            extracted_faces = DeepFace.extract_faces(
                img_path=img_path,
                detector_backend=DETECTOR,
                enforce_detection=True # Set to True to raise error if no face
            )
            # If extract_faces doesn't throw an error with enforce_detection=True, a face was found.
            print("Face detected!")
            return True
        except ValueError:
            print("No face detected!")
            return False

    def check_face_in_db(self, img_path: str) -> tuple[bool, str | None, float | None]:
        try:
            dfs = DeepFace.find(
                img_path=img_path,
                db_path=self.db_path,
                detector_backend=DETECTOR,
                model_name=MODEL_NAME,
                enforce_detection=True
            )
            if not dfs or dfs[0].empty:
                print("Face detected, but no potential matches found in the database.")
                return False, None, None, True

            results_df = dfs[0]
            best_match_row = results_df.loc[results_df["distance"].idxmin()]
            best_distance = best_match_row["distance"]

            if best_distance <= ARCFACE_THRESHOLD:
                identity_path = best_match_row["identity"]
                user_id = Path(identity_path).parent.name
                print(f"Match Found for user_id: '{user_id}' with distance {best_distance:.4f}")
                return True, str(user_id), float(best_distance), True
            else:
                print(f"No valid match. Best distance was {best_distance:.4f} (Threshold: {ARCFACE_THRESHOLD})")
                return False, None, float(best_distance), True

        except ValueError:
            # This error is raised by find() if no face is detected in img_path
            return False, None, None, None

    def analyze_person(self, img_path: str) -> tuple[str, str | None]:
        if not self.check_img_quality(img_path):
             return "BAD_QUALITY", None
             
        is_match, user_id, distance, is_face = self.check_face_in_db(img_path=img_path)

        if is_match:
            return "KNOWN_PERSON", user_id
        elif is_face: # Face was detected but did not match anyone
            return "UNKNOWN_PERSON", None
        else: # No face was detected in the first place
            return "NO_FACE", None


# --- Mock Classes for Testing ---
# These dummy classes simulate the behavior of real services for isolated testing.

class MockGPIO:
    """A dummy GPIO class that prints actions instead of controlling hardware."""
    def set_camera_led(self, status: bool):
        print(f"[MockGPIO] Setting Camera LED to: {'ON' if status else 'OFF'}")

class MockTTS:
    """A dummy Text-to-Speech class that prints phrases."""
    def speak(self, text: str):
        print(f"[MockTTS] Speaking: '{text}'")
    
    def speak_async(self, text: str):
        print(f"[MockTTS] Speaking async: '{text}'")

# --- Main Test Function ---

def main():
    """Main function to provide a testing interface for the FaceProcessing class."""
    # Basic setup for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # --- Configuration for the test ---
    CAMERA_ID = 2 # Change this to your camera's ID
    DB_PATH = Path.cwd() / "data" / "test_db"
    DB_PATH.mkdir(exist_ok=True, parents=True)
    print(f"--- Face Processing Test Utility ---")
    print(f"Using Database Path: {DB_PATH}")

    # --- Initialize services and mocks ---
    camera_manager = CameraManager()
    face_processor = FaceProcessing(camera_manager=camera_manager, db_path=str(DB_PATH))
    mock_gpio = MockGPIO()
    mock_tts = MockTTS()

    while True:
        print("\nWhat would you like to test?")
        print("1. Register a new person")
        print("2. Analyze a person from a live photo")
        print("3. Exit")
        choice = input("Enter your choice (1, 2, or 3): ")

        if choice == '1':
            user_id = input("Enter a unique ID for the new person: ").strip()
            if user_id:
                user_folder = DB_PATH / user_id
                print(f"--- Starting registration for '{user_id}' ---")
                success = face_processor.register_face(
                    camera_id=CAMERA_ID,
                    user_folder=user_folder,
                    gpio=mock_gpio,
                    tts=mock_tts
                )
                if success:
                    print(f"--- Registration for '{user_id}' completed successfully. ---")
                else:
                    print(f"--- Registration for '{user_id}' failed. ---")
            else:
                print("User ID cannot be empty.")

        elif choice == '2':
            print("--- Starting analysis ---")
            temp_image_path = "temp_analysis_photo.jpg"
            
            print("Taking a photo for analysis in 3 seconds...")
            time.sleep(3)
            
            if camera_manager.take_picture(CAMERA_ID, temp_image_path):
                print(f"Photo taken and saved to {temp_image_path}. Analyzing...")
                status, user_id = face_processor.analyze_person(temp_image_path)
                print("\n--- Analysis Result ---")
                print(f"Status: {status}")
                if user_id:
                    print(f"User ID: {user_id}")
                print("-----------------------")
                # Path(temp_image_path).unlink(missing_ok=True) # Clean up
            else:
                print("Failed to take a photo for analysis.")
                
        elif choice == '3':
            print("Exiting test utility.")
            break
        else:
            print("Invalid choice. Please try again.")

# This makes the file runnable
if __name__ == "__main__":
    main()
