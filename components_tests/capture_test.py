import cv2
import time 

cap = cv2.VideoCapture(2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

if not cap.isOpened():
    print("Error")
    exit()

print("Warming up Camera...")

ret, frame = cap.read()

if ret:
    cv2.imwrite('test.jpg', frame)
    print("Success!")
else:
    print("Failed!")

cap.release()

