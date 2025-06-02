from deepface import DeepFace
import cv2 

# Options: 'opencv', 'ssd', 'dlib', 'mtcnn', 'retinaface', 'mediapipe'
DETECTOR_BACKEND = 'retinaface' # RetinaFace is generally robust

class FaceDetector:
    def __init__(self, detector_backend=DETECTOR_BACKEND):
        self.detector_backend = detector_backend
        # You might pre-load models here if DeepFace allows/benefits from it,
        # but often DeepFace handles model loading on first use.
        print(f"FaceDetector initialized with backend: {self.detector_backend}")

    def detect_faces(self, image_np, align=True, return_regions=False):
        """
        Detects faces in an image.

        Args:
            image_np: NumPy array representing the image (BGR format from OpenCV).
            align: Whether to perform facial alignment (recommended for better recognition).
            return_regions: If True, returns the bounding box regions along with face images.

        Returns:
            A list of detected face images (NumPy arrays).
            If return_regions is True, returns a list of tuples: (face_image_np, region_dict).
            Returns empty list or list of empty tuples if no faces are found or an error occurs.
        """
        try:
            # DeepFace.extract_faces can detect and optionally align.
            # It returns a list of dictionaries, each containing 'face' (the numpy array of the face)
            # and 'facial_area' (x, y, w, h).
            # Note: DeepFace expects images in BGR format by default if using OpenCV paths,
            # but if passing a numpy array, ensure it's in the format DeepFace expects or convert it.
            # Typically, if you read with cv2.imread, it's BGR.
            
            # Convert BGR to RGB if your detector expects RGB, though many DeepFace backends handle BGR.
            # For RetinaFace with DeepFace, it usually handles BGR input fine.

            detected_outputs = DeepFace.extract_faces(
                img_path=image_np,
                detector_backend=self.detector_backend,
                align=align,
                enforce_detection=False # Don't raise exception if no face, just return empty
            )

            faces = []
            if return_regions:
                for output in detected_outputs:
                    if output['confidence'] > 0: # Filter by confidence if available and desired
                        faces.append((output['face'], output['facial_area']))
            else:
                for output in detected_outputs:
                     if output['confidence'] > 0:
                        faces.append(output['face'])
            
            return faces

        except Exception as e:
            # print(f"Error in face detection: {e}") # Can be noisy
            return [] if not return_regions else []

    def list_faces(detected_face_data, verbose=False):
        for i, (face_img_np, region) in enumerate(detected_face_data):
            if not verbose:
                print(f"Region for face {i+1}: {region}")
            else:
                if face_img_np.dtype != 'uint8':
                    face_img_np = (face_img_np * 255).astype('uint8')

                face_to_show = cv2.cvtColor(face_img_np, cv2.COLOR_RGB2BGR)
                
                if face_to_show.max() <= 1.0:
                    face_to_show = (face_to_show * 255).astype("uint8")

                cv2.imshow(f"Detected Face {i+1}", face_to_show)

                x, y, w, h = region['x'], region['y'], region['w'], region['h']
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                cv2.imshow("Original Frame with Detections", frame)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

if __name__ == '__main__':
    detector = FaceDetector()
    img_path = "face_db/known_faces/person0/img0.jpg" 
    
    try:
        frame = cv2.imread(img_path)
        if frame is None:
            print(f"Could not read image from {img_path}")
        else:
            print(f"Image shape: {frame.shape}")
            
            detected_face_data = detector.detect_faces(frame, return_regions=True)
            if detected_face_data:
                print(f"Detected {len(detected_face_data)} face(s).")
                # show_faces(detected_face_data)
            else:
                print("No faces detected.")
    except Exception as e:
        print(f"Error in example usage: {e}")
