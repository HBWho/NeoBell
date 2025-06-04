import os
import shutil 
import uuid

class MediaManager:
    def __init__(self, config):
        self.config = config
        # Ensure directories from config exist
        os.makedirs(self.config.REGISTRATION_IMAGES_DIR, exist_ok=True)
        os.makedirs(self.config.VIDEO_MESSAGES_DIR, exist_ok=True)
        print("MediaManager initialized.")

    def save_registration_data(self, name, face_crops_data_rgb_float, face_embeddings_data, face_recognizer_instance):
        """
        Saves registration data: updates recognizer DB and stores face crop images.
        The FaceRecognizer's add_person_and_update_db now handles saving images to its known_faces_db.
        This method primarily orchestrates calling the recognizer.
        """
        print(f"MM: Processing registration for '{name}'.")
        if not face_recognizer_instance or not hasattr(face_recognizer_instance, 'add_person_and_update_db'):
            print("MM ERROR: FaceRecognizer instance is invalid or missing 'add_person_and_update_db' method.")
            return False

        # The FaceRecognizer will save images to its KNOWN_FACES_DB_DIR/name/
        # and update its embeddings pickle file.
        success = face_recognizer_instance.add_person_and_update_db(
            person_name=name,
            new_embeddings_list=face_embeddings_data,
            new_face_crops_data_rgb_float=face_crops_data_rgb_float # Pass crops for saving
        )
        
        if success:
            print(f"MM: Registration data for '{name}' successfully processed by FaceRecognizer.")
            return True
        else:
            print(f"MM ERROR: Failed to save registration for '{name}' via FaceRecognizer.")
            return False

    def save_video_message(self, temp_video_path, visitor_name=None):
        if not temp_video_path or not os.path.exists(temp_video_path):
            print(f"MM ERROR: Video file not found at {temp_video_path}")
            return None

        effective_name = visitor_name.replace(' ', '_') if visitor_name else "UnknownVisitor"
        timestamp = int(time.time())
        final_filename = f"message_by_{effective_name}_{timestamp}.avi" # Match CameraManager output
        final_video_path = os.path.join(self.config.VIDEO_MESSAGES_DIR, final_filename)

        try:
            shutil.move(temp_video_path, final_video_path)
            print(f"MM: Video message moved to {final_video_path} for visitor: {visitor_name or 'Unknown'}.")
            # Here you would add logic to queue final_video_path for S3 upload via CloudStorageService
            # e.g., self.cloud_storage_service.queue_upload(final_video_path, f"videos/{final_filename}")
            return final_video_path
        except Exception as e:
            print(f"MM ERROR: Could not move video file from {temp_video_path} to {final_video_path}: {e}")
            return None