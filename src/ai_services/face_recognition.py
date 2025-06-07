from deepface import DeepFace
import os
import cv2
from pathlib import Path

_PROJECT_ROOT = Path.cwd().parent
DATA_DIR = _PROJECT_ROOT / "data"
KNOWN_FACES_DB_DIR = DATA_DIR / "known_faces_db"
print(KNOWN_FACES_DB_DIR)

filename="Image.jpg"

def take_picture():
    # it works
    cam = cv2.VideoCapture(0)
    
    try:
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        result, image = cam.read()

        if result:
            # cv2.imshow("Image", image)
            cv2.imwrite(filename, image)
            # cv2.waitKey(0)
            # cv2.destroyWindow("Image")
        else:
            print("No image detected")
    finally:
        cam.release()

def recognize_face():
    print("Taking a picture...")
    take_picture()

    print("Analyzing face...")
    try:
        dfs = DeepFace.find(img_path = filename, 
                      db_path = KNOWN_FACES_DB_DIR,
                      model_name = 'SFace')
        print("Analysis complete")
        print(dfs)
    except Exception as e:
        print(f"Error: {e}")

recognize_face()
