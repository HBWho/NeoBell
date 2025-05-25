from deepface import DeepFace
import cv2

img_path = "/home/radxa/Desktop/NeoBell/components_test/face_db/known_faces/GABRIEL_SPADAFORA.jpg"

try:
    img = cv2.imread(img_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    print("Analyzing...")
    result = DeepFace.analyze(img_path, actions=['emotion', 'age', 'gender', 'race'])

    print("Analysis Results: ")
    print(f"Emotion: {result[0]['dominant_emotion']}")
    print(f"Age: {result[0]['age']}")
    print(f"Gender: {result[0]['gender']}")
    print(f"Dominant Race: {result[0]['dominant_race']}")

except Exception as e:
    print(f"Error: {e}")
