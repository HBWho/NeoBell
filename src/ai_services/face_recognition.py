from deepface import DeepFace
import cv2

def take_picture():
    # it works
    cam = cv2.VideoCapture(0)

    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    result, image = cam.read()

    if result:
        cv2.imshow("Image", image)
        cv2.imwrite("Image.jpg", image)
        cv2.waitKey(0)
        cv2.destroyWindow("Image")
    else:
        print("No image detected")

def recognize_face():
    DeepFace.stream(db_path = r"C:\Users\gbspa\OneDrive\Documentos\dev\NeoBell\src\data\known_faces_db")

recognize_face()
