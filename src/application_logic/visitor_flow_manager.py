import time
import cv2 
import os
import uuid

# --- Attempt to import services and AI components ---
_SERVICE_IMPORT_SUCCESS = True
_AI_IMPORT_SUCCESS = True
_HARDWARE_IMPORT_SUCCESS = True

try:
    import sys
    _CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    _PROJECT_ROOT = os.path.dirname(_CURRENT_DIR) 
    if _PROJECT_ROOT not in sys.path:
        sys.path.insert(0, _PROJECT_ROOT)

    from services.tts import TTSService
    from services.stt import STTService
except ImportError as e_svc:
    print(f"FATAL VFM: Could not import TTS or STT services: {e_svc}. Cannot continue.")
    _SERVICE_IMPORT_SUCCESS = False
    # Exiting or raising might be appropriate if these are critical
    raise SystemExit(f"Failed to load core services: {e_svc}")

try:
    from ai_services.face_processor import FaceProcessor
except ImportError as e_ai:
    print(f"WARNING VFM: Could not import FaceProcessor: {e_ai}. Face features will be disabled.")
    _AI_IMPORT_SUCCESS = False
    FaceProcessor = None # Define as None if import fails

try:
    from hardware_interfaces.camera_manager import CameraManager
except ImportError as e_hw:
    print(f"WARNING VFM: Could not import CameraManager: {e_hw}. Video/Image capture will fail.")
    _HARDWARE_IMPORT_SUCCESS = False
    class CameraManager: # Basic Dummy if real one fails
        def __init__(self, *args, **kwargs): print("Using Dummy CameraManager due to import error.")
        def set_tts_service(self, tts): pass
        def capture_still_frame(self): return np.zeros((480,640,3), dtype=np.uint8) # Dummy black frame
        def start_video_recording(self, *args, **kwargs): return None


# Import MediaManager from the same application_logic directory
from .media_manager import MediaManager # Relative import


class VisitorFlowManager:
    def __init__(self, app_config): # Pass the loaded config object
        self.config = app_config
        self.tts_service = TTSService(
            engine_path=self.config.ESPEAK_NG_PATH,
            lang=self.config.TTS_LANG
        )
        self.stt_service = STTService(
            model_path=self.config.VOSK_MODEL_PATH,
            sample_rate=self.config.STT_SAMPLE_RATE,
            lang_code=self.config.STT_LANG
        )
        
        if _AI_IMPORT_SUCCESS and FaceProcessor:
            self.face_processor = FaceProcessor(config=self.config)
            self.face_processor.set_tts_service(self.tts_service) # Give FP access to TTS for its prompts
        else:
            self.face_processor = None
            self.tts_service.speak("Warning: Face recognition system is currently unavailable.")

        if _HARDWARE_IMPORT_SUCCESS:
            self.camera_manager = CameraManager(
                camera_id=self.config.CAMERA_HW_ID,
                default_width=self.config.CAMERA_RESOLUTION_WIDTH,
                default_height=self.config.CAMERA_RESOLUTION_HEIGHT,
                default_fps=self.config.CAMERA_FPS
            )
            self.camera_manager.set_tts_service(self.tts_service)
        else: # Fallback to a more functional dummy if import failed
            class BasicDummyCam:
                def __init__(self, *args, **kwargs): self.tts_service = None
                def set_tts_service(self, tts): self.tts_service = tts
                def _speak(self, text): print(f"DummyCamSpeak: {text}") if not self.tts_service else self.tts_service.speak(text)
                def capture_still_frame(self): self._speak("Simulating frame capture."); return np.zeros((100,100,3), dtype=np.uint8)
                def start_video_recording(self, output_dir, filename_prefix, duration_seconds, **kwargs):
                    self._speak("Simulating video recording."); time.sleep(2); return os.path.join(output_dir, f"{filename_prefix}.avi")
            self.camera_manager = BasicDummyCam()
            self.camera_manager.set_tts_service(self.tts_service)


        self.media_manager = MediaManager(config=self.config)
        
        print("VisitorFlowManager initialized.")

    def _request_face_positioning(self):
        self.tts_service.speak("Please look directly into the camera so I can see your face clearly.")
        time.sleep(2)

    def handle_visitor_intent(self):
        self.tts_service.speak("Okay, I understand you're a visitor and would like to leave a message.")
        
        if not self.face_processor:
            self.tts_service.speak("My face recognition system is currently unavailable. I'll proceed to record your message directly.")
            self._initiate_video_message_recording(visitor_name="Visitor (FaceRec N/A)")
            return

        recognized_name = None
        for attempt in range(self.config.VISITOR_MAX_VERIFICATION_ATTEMPTS):
            self._request_face_positioning()
            live_frame = self.camera_manager.capture_still_frame()
            
            if live_frame is None:
                self.tts_service.speak("I couldn't capture an image from the camera.")
                if attempt < self.config.VISITOR_MAX_VERIFICATION_ATTEMPTS - 1:
                    self.tts_service.speak("Let's try that again.")
                    continue
                else:
                    self.tts_service.speak("I'm having trouble with the camera. We'll proceed without identification.")
                    break 

            _face_crop, live_embedding, _region = self.face_processor.get_primary_face_data(live_frame)

            if live_embedding:
                name, distance = self.face_processor.recognizer.recognize_face(live_embedding, self.config.FACE_RECOGNITION_THRESHOLD)
                if name != "Unknown": # recognize_face returns "Unknown" if below threshold
                    recognized_name = name
                    self.tts_service.speak(f"Hello {recognized_name}! Nice to see you again.")
                    break
                else:
                    self.tts_service.speak("I don't quite recognize you.")
            else:
                self.tts_service.speak("I couldn't detect a face clearly for recognition.")
            
            if attempt < self.config.VISITOR_MAX_VERIFICATION_ATTEMPTS - 1:
                self.tts_service.speak("Let's try to verify one more time.")
            else:
                self.tts_service.speak("I couldn't recognize you from my records.")
        
        if recognized_name:
            self._initiate_video_message_recording(visitor_name=recognized_name)
        else:
            self._offer_and_perform_registration()

    def _offer_and_perform_registration(self):
        self.tts_service.speak("Would you like to register so I can recognize you next time? This involves taking a few pictures. Please say yes or no.")
        response = self.stt_service.transcribe_audio(duration_seconds=4, device_id=self.config.STT_MIC_ID)

        if response and "yes" in response.lower(): # Simple "yes" check
            self.tts_service.speak("Great! Let's get you registered.")
            
            # capture_registration_sequence in FaceProcessor now handles its own TTS prompts
            face_crops, embeddings = self.face_processor.capture_registration_sequence(
                camera_manager_instance=self.camera_manager, # Pass camera manager
                num_images=self.config.REGISTRATION_NUM_PHOTOS
            )

            if embeddings and len(embeddings) >= self.config.REGISTRATION_NUM_PHOTOS // 2 + 1 : # Need at least half + 1 good captures
                self.tts_service.speak("Thank you for the pictures. Now, could you please tell me your first name?")
                visitor_name_spoken = self.stt_service.transcribe_audio(duration_seconds=6, device_id=self.config.STT_MIC_ID)
                
                name_to_register = "Visitor" # Default
                if visitor_name_spoken and visitor_name_spoken.strip() and "ERROR" not in visitor_name_spoken:
                    name_to_register = visitor_name_spoken.strip().capitalize()
                else:
                    self.tts_service.speak("I didn't quite catch your name. I'll use a generic label for now.")
                    name_to_register = f"Visitor_{str(uuid.uuid4())[:6]}"


                if self.media_manager.save_registration_data(
                    name=name_to_register,
                    face_crops_data_rgb_float=face_crops,
                    face_embeddings_data=embeddings,
                    face_recognizer_instance=self.face_processor.recognizer
                ):
                    self.tts_service.speak(f"Thank you, {name_to_register}! You are now registered.")
                    self._initiate_video_message_recording(visitor_name=name_to_register)
                else:
                    self.tts_service.speak("I encountered an issue saving your registration. Let's record your message anyway.")
                    self._initiate_video_message_recording(visitor_name=f"{name_to_register} (RegSaveFail)")
            else:
                self.tts_service.speak("I couldn't capture enough clear images for registration. Let's record your message without it this time.")
                self._initiate_video_message_recording(visitor_name="Visitor (RegPhotoFail)")
        else:
            self.tts_service.speak("Okay, no problem. Let's proceed to record your message.")
            self._initiate_video_message_recording(visitor_name="Visitor (DeclinedReg)")

    def _initiate_video_message_recording(self, visitor_name=None):
        name_for_prompt = visitor_name.split()[0] if visitor_name and visitor_name not in ["Unknown", "Visitor"] else "there"
        self.tts_service.speak(f"Alright {name_for_prompt}, I'm ready to record your video message for the resident.")
        
        filename_prefix = f"message_by_{(visitor_name if visitor_name else 'UnknownVisitor').replace(' ', '_')}"
        
        video_path_temp = self.camera_manager.start_video_recording(
            output_dir=self.config.VIDEO_MESSAGES_DIR, # Temporary save location
            filename_prefix=filename_prefix,
            duration_seconds=self.config.VIDEO_MESSAGE_MAX_DURATION_SECONDS
            # stt_service_for_silence=self.stt_service # For future silence detection
        )

        if video_path_temp and os.path.exists(video_path_temp):
            self.tts_service.speak("Thank you, your message has been recorded.")
            # MediaManager will move it to final storage and handle cloud upload queue
            self.media_manager.save_video_message(video_path_temp, visitor_name=visitor_name)
        else:
            self.tts_service.speak("I'm sorry, there was an error trying to record your message.")


if __name__ == "__main__":
    print("Starting Visitor Flow Manager Test (Full Integration Attempt)...")
    
    # Load configuration
    import config as app_config # Assuming config.py is in the project root

    # Ensure essential paths from config are set correctly on your system
    # Especially VOSK_MODEL_PATH, KNOWN_FACES_DB_DIR, EMBEDDINGS_DB_PATH
    # And device IDs STT_MIC_ID, CAMERA_HW_ID

    # --- Pre-flight checks ---
    if not os.path.exists(app_config.VOSK_MODEL_PATH):
        print(f"FATAL: Vosk model not found at {app_config.VOSK_MODEL_PATH}. Please check config.py and download the model.")
        exit()
    
    # Initialize FaceRecognizer DB if it doesn't exist or known_faces_db is empty
    # This ensures FaceProcessor can load/build its recognizer database.
    if _AI_IMPORT_SUCCESS and FaceProcessor:
        if not os.path.exists(app_config.FACE_EMBEDDINGS_DB_PATH) or \
           (os.path.exists(app_config.KNOWN_FACES_DB_DIR) and not os.listdir(app_config.KNOWN_FACES_DB_DIR) and \
            os.path.exists(app_config.FACE_EMBEDDINGS_DB_PATH) and os.path.getsize(app_config.FACE_EMBEDDINGS_DB_PATH) < 100): # Heuristic for empty pkl
            print("Embeddings DB likely empty or missing, and known_faces_db might be empty. Initializing FaceProcessor to build/check DB...")
            try:
                # This instantiation will trigger FaceRecognizer's load_or_build_database
                fp_init_check = FaceProcessor(config=app_config)
                del fp_init_check # Clean up
                print("FaceProcessor initialization check done (DB should be built/loaded if KFD had images).")
            except Exception as e_fp_init_check:
                print(f"Error during pre-initialization check of FaceProcessor: {e_fp_init_check}")
    
    if not _SERVICE_IMPORT_SUCCESS or not _AI_IMPORT_SUCCESS or not _HARDWARE_IMPORT_SUCCESS:
        print("One or more critical modules (Services, AI, Hardware) failed to import. Functionality will be severely limited or script may exit.")
        # Decide if you want to exit if, for example, FaceProcessor is critical
        if not _AI_IMPORT_SUCCESS and FaceProcessor is None : # Check if FaceProcessor itself is None
             print("FATAL: FaceProcessor could not be loaded. Visitor flow cannot run as intended.")
             exit()


    visitor_manager = VisitorFlowManager(app_config=app_config)
    
    visitor_manager.tts_service.speak("NeoBell system ready. Simulating visitor arrival for message.")
    time.sleep(1)
    
    visitor_manager.handle_visitor_intent()
    
    print("\nVisitor Flow Manager Test Finished.")