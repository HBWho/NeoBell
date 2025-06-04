from deepface import DeepFace
import numpy as np
import os
import pickle
import uuid
import cv2 
import time 

# Default values, can be overridden by config passed to constructor
DEFAULT_KNOWN_FACES_DIR = "data/known_faces_db" # Relative to project root
DEFAULT_EMBEDDINGS_DB_PATH = "data/face_embeddings_db.pkl"

class FaceRecognizer:
    def __init__(self, model_name='ArcFace', distance_metric='cosine',
                 known_faces_dir=None, embeddings_db_path=None,
                 detector_backend_for_db_build='retinaface',
                 detector_backend_for_representation='skip'):
        
        self.model_name = model_name
        self.distance_metric = distance_metric
        self.known_faces_dir = known_faces_dir if known_faces_dir else DEFAULT_KNOWN_FACES_DIR
        self.embeddings_db_path = embeddings_db_path if embeddings_db_path else DEFAULT_EMBEDDINGS_DB_PATH
        self.detector_for_db_build = detector_backend_for_db_build
        self.detector_for_representation = detector_backend_for_representation
        
        self.known_face_embeddings = [] # List of dicts: {"label": str, "embeddings": [list_of_np_arrays]}
        
        # Ensure base data directory exists
        os.makedirs(os.path.dirname(self.embeddings_db_path), exist_ok=True)
        os.makedirs(self.known_faces_dir, exist_ok=True)

        self.load_or_build_database()
        print(f"FaceRecognizer initialized: Model '{self.model_name}', Metric '{self.distance_metric}'. DB has {len(self.known_face_embeddings)} individuals.")

    def _generate_embedding(self, face_image_np_rgb_float): # Expects RGB float (0-1) from DeepFace.extract_faces
        try:
            embedding_objs = DeepFace.represent(
                img_path=face_image_np_rgb_float, # Already a face crop
                model_name=self.model_name,
                detector_backend=self.detector_for_representation, # 'skip'
                enforce_detection=False,
                align=False # Alignment should have been done
            )
            if embedding_objs and len(embedding_objs) > 0:
                return embedding_objs[0]["embedding"]
            return None
        except Exception: # Catch broad exceptions from DeepFace
            # print(f"DEBUG FR: Error generating embedding: {e}")
            return None

    def load_or_build_database(self):
        if os.path.exists(self.embeddings_db_path):
            print(f"FR: Loading known face embeddings from {self.embeddings_db_path}...")
            try:
                with open(self.embeddings_db_path, 'rb') as f:
                    self.known_face_embeddings = pickle.load(f)
                if not isinstance(self.known_face_embeddings, list): # Basic sanity check
                    print("FR WARNING: Embeddings file format error. Rebuilding.")
                    self._build_database()
                elif not self.known_face_embeddings:
                     print("FR: Embeddings file was empty. Will build if known_faces_dir has images.")
                     # Don't rebuild if known_faces_dir is also empty, wait for registrations
            except Exception:
                print(f"FR WARNING: Error loading embeddings file. Rebuilding database.")
                self._build_database()
        else:
            print("FR: No pre-computed embeddings found. Building database from known_faces_dir...")
            self._build_database()

    def _build_database(self):
        self.known_face_embeddings = []
        if not os.path.isdir(self.known_faces_dir):
            print(f"FR ERROR: Known faces directory not found at {self.known_faces_dir}. Cannot build DB.")
            return

        print(f"FR: Building embeddings database from: {self.known_faces_dir}")
        for person_name in os.listdir(self.known_faces_dir):
            person_dir = os.path.join(self.known_faces_dir, person_name)
            if os.path.isdir(person_dir):
                person_embeddings_list = []
                print(f"FR: Processing images for {person_name}...")
                for image_name in os.listdir(person_dir):
                    image_path = os.path.join(person_dir, image_name)
                    try:
                        # Use DeepFace.extract_faces to get aligned faces first
                        # It expects BGR numpy array or image path
                        extracted_face_data_list = DeepFace.extract_faces(
                            img_path=image_path, # Can be path or BGR numpy array
                            detector_backend=self.detector_for_db_build,
                            align=True,
                            enforce_detection=True
                        )
                        if extracted_face_data_list:
                            aligned_face_np_rgb_float = extracted_face_data_list[0]['face']
                            embedding = self._generate_embedding(aligned_face_np_rgb_float)
                            if embedding:
                                person_embeddings_list.append(embedding)
                        # else:
                        #     print(f"FR DEBUG: No face detected in {image_name} for {person_name}")
                    except Exception: # Catch broad exceptions from DeepFace
                        # print(f"FR DEBUG: Error processing {image_path} for DB: {e}")
                        pass # Continue to next image
                
                if person_embeddings_list:
                    self.known_face_embeddings.append({"label": person_name, "embeddings": person_embeddings_list})
                    print(f"FR: Added/Updated {person_name} with {len(person_embeddings_list)} embeddings.")
        
        self._save_database()

    def _save_database(self):
        try:
            with open(self.embeddings_db_path, 'wb') as f:
                pickle.dump(self.known_face_embeddings, f)
            print(f"FR: Face embeddings database saved to {self.embeddings_db_path}")
            return True
        except Exception as e:
            print(f"FR ERROR: Error saving embeddings database: {e}")
            return False

    def add_person_and_update_db(self, person_name, new_embeddings_list, new_face_crops_data_rgb_float=None):
        if not new_embeddings_list:
            print(f"FR ERROR: No embeddings provided for {person_name}.")
            return False
        
        if new_face_crops_data_rgb_float:
            person_image_dir = os.path.join(self.known_faces_dir, person_name)
            os.makedirs(person_image_dir, exist_ok=True)
            for i, crop_data_rgb_float in enumerate(new_face_crops_data_rgb_float):
                try:
                    img_to_save = cv2.cvtColor(crop_data_rgb_float, cv2.COLOR_RGB2BGR)
                    if img_to_save.max() <= 1.0 + 1e-6 :
                        img_to_save = (img_to_save * 255).astype(np.uint8)
                    else:
                        img_to_save = img_to_save.astype(np.uint8)
                    
                    # Use a more unique filename to avoid overwrites if called multiple times quickly
                    filename = f"reg_face_{i+1}_{int(time.time())}_{str(uuid.uuid4())[:4]}.jpg"
                    cv2.imwrite(os.path.join(person_image_dir, filename), img_to_save)
                except Exception as e_img:
                    print(f"FR ERROR: Could not save registration image {i+1} for {person_name}: {e_img}")

        existing_person_entry = next((item for item in self.known_face_embeddings if item["label"] == person_name), None)
        if existing_person_entry:
            print(f"FR: Updating existing person in embeddings DB: {person_name}")
            existing_person_entry["embeddings"].extend(new_embeddings_list)
        else:
            print(f"FR: Adding new person to embeddings DB: {person_name}")
            self.known_face_embeddings.append({"label": person_name, "embeddings": new_embeddings_list})
        
        return self._save_database()

    def recognize_face(self, live_face_embedding, recognition_threshold): # Pass threshold
        if live_face_embedding is None or not self.known_face_embeddings:
            return "Unknown", float('inf')

        min_overall_distance = float('inf')
        recognized_name = "Unknown"
        live_embedding_np = np.array(live_face_embedding)

        for entry in self.known_face_embeddings:
            person_label = entry["label"]
            embeddings_for_person = entry["embeddings"]
            current_person_min_distance = float('inf')

            for known_embedding in embeddings_for_person:
                try:
                    known_embedding_np = np.array(known_embedding)
                    if self.distance_metric == 'cosine':
                        distance = DeepFace.dst.findCosineDistance(live_embedding_np, known_embedding_np)
                    elif self.distance_metric == 'euclidean':
                        distance = DeepFace.dst.findEuclideanDistance(live_embedding_np, known_embedding_np)
                    elif self.distance_metric == 'euclidean_l2':
                        distance = DeepFace.dst.findEuclideanDistance(
                            DeepFace.dst.l2_normalize(live_embedding_np),
                            DeepFace.dst.l2_normalize(known_embedding_np)
                        )
                    else: # Should not happen if constructor validates
                        distance = float('inf') 
                    
                    if distance < current_person_min_distance:
                        current_person_min_distance = distance
                except: # Broad except for DeepFace distance errors
                    continue 
            
            if current_person_min_distance < min_overall_distance:
                min_overall_distance = current_person_min_distance
                recognized_name = person_label
        
        if min_overall_distance <= recognition_threshold:
            return recognized_name, min_overall_distance
        else:
            return "Unknown", min_overall_distance