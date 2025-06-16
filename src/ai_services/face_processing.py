import cv2
import time
import pandas as pd
import sounddevice as sd
import numpy as np
import threading
import logging
from deepface import DeepFace
from pathlib import Path
# from ffmpeg import input as ffmpeg_input, output as ffmpeg_output, run as ffmpeg_run

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path.cwd().parent
DATA_DIR = _PROJECT_ROOT / "data"
KNOWN_FACES_DB_DIR = DATA_DIR / "known_faces_db"
TEMP_IMAGE = "temp_image.jpg"
TEMP_VIDEO = "temp_video.avi"
TEMP_AUDIO = "temp_audio.wav"
MODEL_NAME = "SFace"
DETECTOR = "opencv"
THRESHOLD = 0.55 # the result needs to be less than this to be valid

class FaceProcessing():
    def __init__(self):
        pass

    def take_picture(self, camera_id, filename = TEMP_IMAGE):
        cam = cv2.VideoCapture(camera_id)

        try:
            cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            result, image = cam.read()

            if not result:
                raise ValueError("Failed to capture image from camera")
            cv2.imwrite(filename, image)
        finally:
            cam.release()

    def record_video(self, camera_id):
        cap = cv2.VideoCapture(camera_id)

        # Get camera frame dimensions
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Define the codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(TEMP_VIDEO, fourcc, 30.0, (frame_width, frame_height))
        
        start_time = time.time()
        
        logger.info("Recording for 10 seconds...")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.error("Error: Could not read frame")
                break
                
            # Write the frame to the output file
            out.write(frame)
            
            # Display the frame (optional)
            # cv2.imshow('Recording...', frame)
            
            # Check if 10 seconds have passed
            if time.time() - start_time >= 10:
                break
                
            # Press 'q' to exit early (optional)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Release everything when done
        cap.release()
        out.release()
        # cv2.destroyAllWindows()
        logger.info(f"Video saved as {TEMP_VIDEO}")
        
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
            logger.warning("No matches found below threshold")
            return 0, "Unknown", "Unknown"
        
        all_results = pd.concat(results)

        best_match_idx = all_results['distance'].idxmin()
        best_match = all_results.loc[best_match_idx]

        best_person = str(best_match['person'])
        best_distance = float(best_match['distance'])

        logger.info(f"Best Match: {best_person} (Distance: {best_distance:.3f})")
        # TODO
        return 1, f"{best_person}", "123"
        # logger.info("\nAll Valid Matches:")
        # logger.info(all_results.sort_values('distance').to_string())

    def recognize_face(self, camera_id, db_path):
        logger.info(f"Using face database at: {KNOWN_FACES_DB_DIR}")
        logger.info("Taking a picture...")
        self.take_picture(camera_id)

        logger.info("Analyzing face...")
        try:
            dfs = DeepFace.find(
                img_path = TEMP_IMAGE, 
                db_path = db_path,
                model_name = MODEL_NAME,
                detector_backend = DETECTOR,
                enforce_detection = True,
                distance_metric = 'cosine')
            a, b, c = self.process_results(dfs)
            return a, b, c
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            if Path(TEMP_IMAGE).exists():
                Path(TEMP_IMAGE).unlink()

if __name__ == "__main__":
    FaceProcessing().recognize_face()
