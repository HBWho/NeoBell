import os

# --- General Paths ---
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
MODELS_DIR = os.path.join(_PROJECT_ROOT, "models")
MEDIA_STORAGE_DIR = os.path.join(DATA_DIR, "media_storage")
REGISTRATION_IMAGES_DIR = os.path.join(MEDIA_STORAGE_DIR, "registration_images")
VIDEO_MESSAGES_DIR = os.path.join(MEDIA_STORAGE_DIR, "video_messages")

# --- Audio Configuration ---
STT_MIC_ID = None # None for default mic, or specify index (e.g., 9 for your Windows HyperX)
                    # !!! MUST BE SET FOR RADXA LINUX (e.g., find with arecord -l) !!!
VOSK_MODEL_PATH = os.path.join(MODELS_DIR, "vosk-model-small-en-us-0.15") # Or 'vosk-model-small-pt-0.3' for Portuguese
STT_SAMPLE_RATE = 16000
STT_LANG = "en-us" # or "pt-br" if using Portuguese Vosk model

# --- TTS Configuration ---
ESPEAK_NG_PATH = None # None will try to use 'espeak-ng' from PATH
                      # Windows example: r"C:\Program Files\eSpeak NG\espeak-ng.exe"
TTS_LANG = "en" # eSpeak language code (e.g., "pt" for Portuguese)

# --- Camera Configuration ---
CAMERA_HW_ID = 0 # Default camera index. !!! ADJUST FOR YOUR SYSTEM !!!
CAMERA_RESOLUTION_WIDTH = 640
CAMERA_RESOLUTION_HEIGHT = 480
CAMERA_FPS = 15 # For video recording

# --- Face Recognition Configuration ---
FACE_DETECTOR_BACKEND = 'retinaface'
FACE_RECOGNITION_MODEL_NAME = 'ArcFace'
FACE_DISTANCE_METRIC = 'cosine'
FACE_RECOGNITION_THRESHOLD = 0.68 # Default for ArcFace/Cosine, TUNE THIS!
KNOWN_FACES_DB_DIR = os.path.join(DATA_DIR, "known_faces_db")
FACE_EMBEDDINGS_DB_PATH = os.path.join(DATA_DIR, "face_embeddings_db.pkl")
REGISTRATION_NUM_PHOTOS = 3
REGISTRATION_PHOTO_CAPTURE_DURATION = 10 # Total seconds user should stay still
REGISTRATION_DELAY_BETWEEN_PICS = 2.0 # Seconds

# --- Visitor Flow Configuration ---
VISITOR_MAX_VERIFICATION_ATTEMPTS = 2
VIDEO_MESSAGE_MAX_DURATION_SECONDS = 20

# --- Ensure directories exist ---
os.makedirs(MEDIA_STORAGE_DIR, exist_ok=True)
os.makedirs(REGISTRATION_IMAGES_DIR, exist_ok=True)
os.makedirs(VIDEO_MESSAGES_DIR, exist_ok=True)
os.makedirs(KNOWN_FACES_DB_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True) 

# --- Debugging ---
APP_DEBUG_MODE = True # Set to False for less verbose output in production