import cv2
from deepface import DeepFace
import time
import os
import datetime

from gpio import activate_pin, deactivate_pin

KNOWN_FACES_DIR = "face_db/known_faces"
CONFIDENCE_THRESHOLD = 0.68
FRAME_INTERVAL = 30
DISPLAY_SCALE = 0.5

known_faces = []
known_names = []

print("Loading known faces...")
for filename in os.listdir(KNOWN_FACES_DIR):
    if filename.endswith(('.jpg', '.jpeg', '.png')):
        path = os.path.join(KNOWN_FACES_DIR, filename)
        name = os.path.splitext(filename)[0]
        known_faces.append(path)
        known_names.append(name)
        print(f"Loaded: {name}")

if not known_faces:
    print("No known faces found!")
    exit()

print(f"Loaded {len(known_faces)} known faces")

##

cap = cv2.VideoCapture(0)
if not cap. isOpened():
    print("Error: Could not open webcam.")
    exit()

print("Starting real-time face recognition...")
print("Press 'q' to quit")

frame_count = 0
last_name = "Unkown"
last_match_time = 0
processing = False

try: 
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image")
            break

        if frame_count % FRAME_INTERVAL == 0 and not processing:
            processing = True

            temp_path = "temp_frame.jpg"
            cv2.imwrite(temp_path, frame)

            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Processing frame...")

            try:
                best_match = None
                best_distance = float('inf')
                matched_name = "Unknown"

                for i, known_face in enumerate(known_faces):
                    try:
                        result = DeepFace.verify(img1_path=temp_path, img2_path=known_face, enforce_detection=False)
                        distance = result['distance']

                        if distance < best_distance:
                            best_distance = distance
                            best_match = result
                            matched_name = known_names[i]

                    except Exception as e:
                        continue

                if best_match and best_match['distance'] < CONFIDENCE_THRESHOLD:
                    last_name = matched_name
                    last_match_time = time.time()
                    access_granted = True
                    print(f"ACCESS GRANTED: Recognized {matched_name} (distance: {best_match['distance']:.4f})")
                else:
                    access_granted = False
                    if best_match:
                        print(f"ACCESS DENIED: Unknown person (best distance: {best_match['distance']:.4f})")
                    else:
                        print(f"ACCESS DENIED: No face detected")

            except Exception as e:
                print(f"Error during processing: {e}")
                last_name = "Error"
                access_granted = False

            if os.path.exists(temp_path):
                os.remove(temp_path)

            processing = False

        frame_count += 1
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nInterrupted by user")
finally:
    cap.release()
    print("Face recognition terminated")


