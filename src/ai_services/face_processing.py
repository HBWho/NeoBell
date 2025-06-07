import cv2
import pandas as pd

from deepface import DeepFace
from pathlib import Path

_PROJECT_ROOT = Path.cwd().parent
DATA_DIR = _PROJECT_ROOT / "data"
KNOWN_FACES_DB_DIR = DATA_DIR / "known_faces_db"
TEMP_IMAGE = "temp_image.jpg"
MODEL_NAME = "SFace"
DETECTOR = "opencv"
THRESHOLD = 0.55 # the result needs to be less than this to be valid

class FaceProcessing:
    def __init__(self):
        pass

    def take_picture(self):
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
        
    def process_results(self, dfs):
        results = []
        for df in dfs:
            df = df[df['distance'] < THRESHOLD]
            if not df.empty:
                # Extract just the person's name from path
                df['person'] = df['identity'].apply(
                    lambda x: Path(x).parent.name)

                results.append(df[['person', 'distance']])
        
        if not results:
            print("No matches found below threshold")
            return
        
        all_results = pd.concat(results)

        best_match_idx = all_results['distance'].idxmin()
        best_match = all_results.loc[best_match_idx]

        best_person = str(best_match['person'])
        best_distance = float(best_match['distance'])

        print(f"Best Match: {best_person} (Distance: {best_distance:.3f})")
        # print("\nAll Valid Matches:")
        # print(all_results.sort_values('distance').to_string())

    def recognize_face(self):
        print(f"Using face database at: {KNOWN_FACES_DB_DIR}")
        print("Taking a picture...")
        self.take_picture()

        print("Analyzing face...")
        try:
            dfs = DeepFace.find(
                img_path = TEMP_IMAGE, 
                db_path = KNOWN_FACES_DB_DIR,
                model_name = MODEL_NAME,
                detector_backend = DETECTOR,
                enforce_detection = True,
                distance_metric = 'cosine')
            self.process_results(dfs)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if Path(TEMP_IMAGE).exists():
                Path(TEMP_IMAGE).unlink()

if __name__ == "__main__":
    FaceProcessing().recognize_face()
