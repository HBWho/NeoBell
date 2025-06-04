from deepface import DeepFace
import numpy as np
import os
import pickle # For saving/loading the database easily, consider SQLite for more robustness

# Choose your preferred recognition model backend
# Options: 'VGG-Face', 'Facenet', 'Facenet512', 'OpenFace', 'DeepFace', 'DeepID', 'ArcFace', 'Dlib', 'SFace'
RECOGNITION_MODEL_NAME = 'ArcFace' # ArcFace is a strong performer
DISTANCE_METRIC = 'cosine' # or 'euclidean', 'euclidean_l2'

# Path to your database of known faces
KNOWN_FACES_DIR = "known_faces_db"
EMBEDDINGS_DB_PATH = "face_embeddings_db.pkl" # Where pre-computed embeddings will be stored

class FaceRecognizer:
    def __init__(self, model_name=RECOGNITION_MODEL_NAME, 
                 known_faces_dir=KNOWN_FACES_DIR, 
                 embeddings_db_path=EMBEDDINGS_DB_PATH,
                 detector_backend='skip'): # Use 'skip' if faces are already cropped
        self.model_name = model_name
        self.known_faces_dir = known_faces_dir
        self.embeddings_db_path = embeddings_db_path
        self.detector_for_representation = detector_backend # For DeepFace.represent()
        
        self.known_face_embeddings = [] # List of tuples: (label, [list of embeddings for that label])
        self.load_or_build_database()
        print(f"FaceRecognizer initialized with model: {self.model_name}. Database has {len(self.known_face_embeddings)} known individuals.")

    def _generate_embedding(self, face_image_np):
        """Generates embedding for a single cropped and aligned face image."""
        try:
            # DeepFace.represent expects a BGR image if it's a path, or a numpy array.
            # If face_image_np is from extract_faces, it's already aligned and likely RGB.
            # The `detector_backend='skip'` tells represent not to run detection again.
            embedding_objs = DeepFace.represent(
                img_path=face_image_np,
                model_name=self.model_name,
                detector_backend=self.detector_for_representation, # 'skip' if face_image_np is already a cropped face
                enforce_detection=False, # If 'skip', this doesn't matter much for single face
                align=False # Alignment should have been done by detector or when preparing DB
            )
            if embedding_objs and len(embedding_objs) > 0:
                return embedding_objs[0]["embedding"] # Access the 'embedding' key
            return None
        except Exception as e:
            # print(f"Error generating embedding: {e}") # Can be noisy
            return None

    def load_or_build_database(self):
        """Loads pre-computed embeddings if available, otherwise builds them from known_faces_dir."""
        if os.path.exists(self.embeddings_db_path):
            print(f"Loading known face embeddings from {self.embeddings_db_path}...")
            try:
                with open(self.embeddings_db_path, 'rb') as f:
                    self.known_face_embeddings = pickle.load(f)
                if not self.known_face_embeddings: # If file was empty or corrupt
                    print("Embeddings file was empty or invalid. Rebuilding database.")
                    self._build_database()
            except Exception as e:
                print(f"Error loading embeddings file: {e}. Rebuilding database.")
                self._build_database()
        else:
            print("No pre-computed embeddings found. Building database...")
            self._build_database()

    def _build_database(self):
        """Scans known_faces_dir, generates, and saves embeddings."""
        self.known_face_embeddings = []
        if not os.path.isdir(self.known_faces_dir):
            print(f"Error: Known faces directory not found at {self.known_faces_dir}")
            return

        # Use a temporary face detector instance just for building the database
        # This ensures faces are properly extracted and aligned before embedding
        db_builder_detector_backend = 'retinaface' # Or your preferred robust detector
        
        for person_name in os.listdir(self.known_faces_dir):
            person_dir = os.path.join(self.known_faces_dir, person_name)
            if os.path.isdir(person_dir):
                person_embeddings = []
                print(f"Processing images for {person_name}...")
                for image_name in os.listdir(person_dir):
                    image_path = os.path.join(person_dir, image_name)
                    try:
                        # Use DeepFace.extract_faces to get aligned faces first
                        extracted_face_data = DeepFace.extract_faces(
                            img_path=image_path,
                            detector_backend=db_builder_detector_backend,
                            align=True,
                            enforce_detection=True # We expect a face in DB images
                        )
                        if extracted_face_data:
                            # Use the first (and hopefully only) face detected and aligned
                            aligned_face_np = extracted_face_data[0]['face'] 
                            embedding = self._generate_embedding(aligned_face_np)
                            if embedding:
                                person_embeddings.append(embedding)
                                print(f"  Generated embedding for {image_name}")
                            else:
                                print(f"  Could not generate embedding for {image_name}")
                        else:
                            print(f"  No face detected in {image_name} for {person_name}")

                    except Exception as e:
                        print(f"  Error processing {image_path}: {e}")
                
                if person_embeddings:
                    self.known_face_embeddings.append({"label": person_name, "embeddings": person_embeddings})
        
        try:
            with open(self.embeddings_db_path, 'wb') as f:
                pickle.dump(self.known_face_embeddings, f)
            print(f"Face embeddings database saved to {self.embeddings_db_path}")
        except Exception as e:
            print(f"Error saving embeddings database: {e}")


    def recognize_face(self, live_face_embedding, threshold=None):
        """
        Compares a live face embedding against the known database.

        Args:
            live_face_embedding: NumPy array of the embedding from the live camera feed.
            threshold: Distance threshold for recognition. If None, uses DeepFace defaults.
                       Lower threshold means stricter matching.
                       Typical cosine similarity thresholds are around 0.4 to 0.6 (lower is better match).
                       Typical Euclidean L2 thresholds depend on the model (e.g., Facenet ~1.0-1.2).

        Returns:
            A tuple (name, min_distance) or (None, None) if no match above threshold.
        """
        if live_face_embedding is None or not self.known_face_embeddings:
            return None, float('inf')

        min_overall_distance = float('inf')
        recognized_name = "Unknown" # Default

        for entry in self.known_face_embeddings:
            person_label = entry["label"]
            embeddings_for_person = entry["embeddings"]
            
            current_person_min_distance = float('inf')

            for known_embedding in embeddings_for_person:
                try:
                    # Ensure embeddings are numpy arrays for distance calculation
                    known_embedding_np = np.array(known_embedding)
                    live_embedding_np = np.array(live_face_embedding)

                    if DISTANCE_METRIC == 'cosine':
                        distance = DeepFace.dst.findCosineDistance(live_embedding_np, known_embedding_np)
                    elif DISTANCE_METRIC == 'euclidean':
                        distance = DeepFace.dst.findEuclideanDistance(live_embedding_np, known_embedding_np)
                    elif DISTANCE_METRIC == 'euclidean_l2':
                        distance = DeepFace.dst.findEuclideanDistance(
                            DeepFace.dst.l2_normalize(live_embedding_np),
                            DeepFace.dst.l2_normalize(known_embedding_np)
                        )
                    else:
                        raise ValueError(f"Unsupported distance metric: {DISTANCE_METRIC}")
                    
                    if distance < current_person_min_distance:
                        current_person_min_distance = distance
                        
                except Exception as e:
                    print(f"Error calculating distance for {person_label}: {e}")
                    continue # Skip this problematic embedding
            
            # Update overall best match if this person is a better match
            if current_person_min_distance < min_overall_distance:
                min_overall_distance = current_person_min_distance
                recognized_name = person_label

        # Apply threshold
        # Default thresholds from DeepFace.verify for ArcFace + Cosine is often around 0.68
        # You MUST tune this threshold based on your model and desired FAR/FRR
        if threshold is None: 
            # Get default threshold for the model and metric
            # This is a bit of a hack, as DeepFace.verify usually takes two images.
            # We'll use a placeholder for the second image path just to get the threshold.
            # Alternatively, set a sensible default based on experimentation.
            try:
                # This is just to get the threshold, not for actual verification here
                metrics_df = DeepFace.verify(img1_path=np.zeros((112,112,3), dtype=np.uint8), 
                                             img2_path=np.zeros((112,112,3), dtype=np.uint8), 
                                             model_name=self.model_name, distance_metric=DISTANCE_METRIC, 
                                             detector_backend='skip', enforce_detection=False)
                threshold = metrics_df['threshold']
                # print(f"Using default threshold for {self.model_name}/{DISTANCE_METRIC}: {threshold}")
            except:
                # Fallback if the above hack fails or for models not directly in verify's list
                if self.model_name == 'ArcFace' and DISTANCE_METRIC == 'cosine': threshold = 0.68 
                elif self.model_name == 'Facenet512' and DISTANCE_METRIC == 'cosine': threshold = 0.30
                elif self.model_name == 'Facenet512' and DISTANCE_METRIC == 'euclidean_l2': threshold = 1.0
                elif self.model_name == 'SFace' and DISTANCE_METRIC == 'cosine': threshold = 0.593 # from SFace paper
                else: threshold = 0.5 # A generic guess for cosine
                print(f"Using fallback threshold: {threshold}")


        if min_overall_distance <= threshold:
            return recognized_name, min_overall_distance
        else:
            return "Unknown", min_overall_distance # Or just None, min_overall_distance


    def verify_face(self, live_face_embedding, known_person_label, image_index=0, threshold=None):
        """
        Verifies if the live face embedding matches a specific known person.
        This is useful if you have an expected person (e.g., from an allow list).
        """
        # ... (Implementation similar to recognize_face, but only compares against one person's embeddings)
        # This would be an extension if needed. For now, recognize_face is the primary.
        pass


if __name__ == '__main__':
    # --- IMPORTANT: Setup your known_faces_db directory first! ---
    # Example:
    # known_faces_db/
    # ├── Alice/
    # │   ├── alice1.jpg
    # │   └── alice2.jpg
    # └── Bob/
    #     └── bob1.jpg
    #
    # You need to create these directories and add images of people.

    recognizer = FaceRecognizer() # This will build or load the DB

    # To test recognition, you'd need a live face embedding.
    # For this example, let's try to get an embedding from a test image
    # that is NOT in the database, or one that IS.
    
    test_image_path = "path/to/your/live_test_image.jpg" # An image of someone (known or unknown)
    test_frame = cv2.imread(test_image_path)

    if test_frame is not None:
        # 1. Detect face in the test image
        # Use a detector instance (can be from face_detector.py or a temporary one)
        temp_detector = FaceDetector(detector_backend='retinaface')
        detected_faces_data = temp_detector.detect_faces(test_frame, align=True, return_regions=False)

        if detected_faces_data:
            live_face_np = detected_faces_data[0] # Assume first detected face

            # 2. Generate embedding for the live face
            # The recognizer's _generate_embedding expects an already cropped/aligned face
            live_embedding = recognizer._generate_embedding(live_face_np)

            if live_embedding:
                # 3. Recognize
                name, confidence_score = recognizer.recognize_face(live_embedding) # Threshold will be default
                print(f"Recognized: {name} with distance: {confidence_score:.4f}")

                # Example with a custom threshold (lower is stricter for cosine)
                name_strict, confidence_strict = recognizer.recognize_face(live_embedding, threshold=0.5)
                print(f"Recognized (strict threshold 0.5): {name_strict} with distance: {confidence_strict:.4f}")
            else:
                print("Could not generate embedding for the live test image.")
        else:
            print(f"No face detected in the live test image: {test_image_path}")
    else:
        print(f"Could not load live test image: {test_image_path}")