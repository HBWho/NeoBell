import google.generativeai as genai
from dotenv import load_dotenv
import os
import time
import sys

# --- Add project root to sys.path to allow finding modules ---
# This assumes main.py is in the project root.
# Adjust if your main.py is located elsewhere relative to your module directories.
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# --- Import Configuration First ---
try:
    import config as app_config
except ImportError:
    print("FATAL: config.py not found. Please ensure it exists in the project root.")
    sys.exit(1)

# --- Import Custom Modules ---
_CRITICAL_MODULE_LOAD_ERROR = False
from services.tts import TTSService
from services.stt import STTService
from hal.camera_manager import CameraManager
from application_logic.visitor_flow_manager import VisitorFlowManager


# --- Load Environment Variables ---
load_dotenv()

# --- Gemini API Configuration ---
GEMINI_API_KEY = None
gemini_model = None

if not _CRITICAL_MODULE_LOAD_ERROR: # Only proceed if core imports were okay
    try:
        GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
        if not GEMINI_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable not set or .env file not loaded.")
        genai.configure(api_key=GEMINI_API_KEY)
        
        gemini_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-latest", # Or "gemini-1.5-pro-latest"
            system_instruction= (
                "You are NeoBell, an AI assistant for a smart doorbell. "
                "Your primary task is to understand if a person at the door wants to 'deliver a package' "
                "or if they are a 'visitor' (which implies they might want to leave a message or speak to a resident). "
                "Respond ONLY with 'PACKAGE_DELIVERY', 'VISITOR_MESSAGE', or 'UNCLEAR'."
            )
        )
        print("Gemini API configured and model initialized successfully.")
    except Exception as e:
        print(f"ERROR Main: Error during Gemini setup: {e}")
        gemini_model = None # Ensure it's None if setup fails


# --- Initialize Services (using settings from config.py) ---
# These will be initialized only if _CRITICAL_MODULE_LOAD_ERROR is False
tts = None
stt = None
visitor_flow_mgr = None
# delivery_flow_mgr = None # For later

if not _CRITICAL_MODULE_LOAD_ERROR:
    try:
        tts = TTSService(
            engine_path=app_config.ESPEAK_NG_PATH,
            lang=app_config.TTS_LANG
        )
        stt = STTService(
            model_path=app_config.VOSK_MODEL_PATH,
            sample_rate=app_config.STT_SAMPLE_RATE,
            lang_code=app_config.STT_LANG
        )
        # Pass the app_config to the flow managers so they can access all settings
        visitor_flow_mgr = VisitorFlowManager(app_config=app_config)
        # delivery_flow_mgr = DeliveryFlowManager(app_config=app_config) 

        # Pre-flight check for STT model
        if not stt.is_ready:
            tts.speak("Warning: The speech recognition model could not be loaded. My understanding will be limited.")

    except Exception as e_init:
        print(f"ERROR Main: Failed to initialize core services: {e_init}")
        _CRITICAL_MODULE_LOAD_ERROR = True # Prevent main loop from running without services


def get_initial_intent_from_gemini(user_reply_text):
    """
    Sends the user's reply to Gemini for initial intent classification.
    Returns "PACKAGE_DELIVERY", "VISITOR_MESSAGE", or "UNCLEAR".
    """
    if not gemini_model:
        print("ERROR Main: Gemini model not available for intent classification.")
        return "ERROR_MODEL"

    # The system instruction for gemini_model is already set to guide its response.
    # We just send the user's reply in the context of NeoBell's initial question.
    prompt = f"""
    NeoBell asked: "Hello, I am NeoBell. How can I help you today? For example, are you here to deliver a package, or are you a visitor?"
    User replied: "{user_reply_text}"
    Classify the user's main intent.
    """
    # The system prompt for the model already constrains the output to the desired categories.

    if app_config.APP_DEBUG_MODE:
        print(f"DEBUG Main: Sending to Gemini for initial intent: User reply was '{user_reply_text}'")
    
    try:
        response = gemini_model.generate_content(prompt) # Use generate_content for single-turn
        classified_intent = response.text.strip().upper()

        # Validate against expected intents
        valid_intents = ["PACKAGE_DELIVERY", "VISITOR_MESSAGE", "UNCLEAR"]
        if classified_intent in valid_intents:
            return classified_intent
        else:
            if app_config.APP_DEBUG_MODE:
                print(f"WARNING Main: Gemini returned an unexpected initial classification: '{classified_intent}'. Defaulting to UNCLEAR.")
            return "UNCLEAR"
    except Exception as e:
        print(f"ERROR Main: Error communicating with Gemini API for initial intent: {e}")
        return "ERROR_API"

def main_neo_bell_interaction_loop():
    if _CRITICAL_MODULE_LOAD_ERROR or not tts or not stt:
        print("FATAL: Critical services (TTS/STT or others) not initialized. NeoBell cannot run.")
        if tts: tts.speak("I'm sorry, there's a problem with my core systems, and I can't operate right now.")
        return

    if not gemini_model:
        tts.speak("I am currently unable to process requests due to a connection issue. Please try again later.")
        return

    # 1. NeoBell Greets and asks for general intent
    # Modified greeting to be more open
    greeting = "Hello, I am NeoBell. Are you here to deliver a package, or are you a visitor?"
    tts.speak(greeting)
    
    time.sleep(0.5) 

    # 2. Listen and Transcribe User's Reply
    if app_config.APP_DEBUG_MODE: print("DEBUG Main: NeoBell is listening for initial intent...")
    # TODO: buy a mic
    # transcribed_text = stt.transcribe_audio(
    #     duration_seconds=9, 
    #     device_id=app_config.STT_MIC_ID # Use configured STT device ID
    # )
    transcribed_text = "Hello. I am a visitor"

    if not transcribed_text: # Handles None or empty string from STT
        tts.speak("I didn't quite catch that. Could you please repeat how I can help you?")
        if app_config.APP_DEBUG_MODE: print("DEBUG Main: STT returned no text for initial intent.")
        return # End this interaction attempt, main loop might retry or wait for new trigger

    # 3. Classify Initial Intent with Gemini
    intent = get_initial_intent_from_gemini(transcribed_text)
    if app_config.APP_DEBUG_MODE: print(f"DEBUG Main: Initial Classified Intent from Gemini: {intent}")

    # 4. Act on Intent
    if intent == "PACKAGE_DELIVERY":
        tts.speak("Okay, I can help with a package delivery.")
        if app_config.APP_DEBUG_MODE: print("FLOW Main: Initiating Package Delivery Flow...")
        # delivery_flow_mgr.handle_delivery_intent() # Call when implemented
        # For now:
        tts.speak("The package delivery flow is not fully implemented yet.")
    elif intent == "VISITOR_MESSAGE": # Changed from SEND_MESSAGE to match Gemini's expected output
        # tts.speak("Alright, I understand you are a visitor.") # This will be handled by visitor_flow_mgr
        if app_config.APP_DEBUG_MODE: print("FLOW Main: Initiating Visitor Message Flow...")
        if visitor_flow_mgr:
            visitor_flow_mgr.handle_visitor_intent() # This now orchestrates the full visitor interaction
        else:
            tts.speak("Sorry, the visitor message system is currently unavailable.")
    elif intent == "UNCLEAR":
        tts.speak("I'm sorry, I'm not quite sure how to help. Could you please tell me if you're here for a delivery or as a visitor?")
    elif intent == "ERROR_MODEL" or intent == "ERROR_API":
        tts.speak("I'm having a little trouble understanding things right now. Please try again in a moment.")
    else: # Should not happen if Gemini adheres to system prompt
        tts.speak("I'm a bit confused by that. Let's try again later.")

if __name__ == "__main__":
    if _CRITICAL_MODULE_LOAD_ERROR:
        print("Exiting due to critical module loading errors.")
    elif not gemini_model:
        print("Exiting: Gemini model not initialized properly.")
        if tts: tts.speak("My connection to advanced understanding is not working. Please try later.")
    elif not stt or not stt.is_ready:
        print("Exiting: STT Service not ready (Vosk model likely not loaded).")
        if tts: tts.speak("I'm having trouble with my hearing system right now.")
    else:
        # This loop would be triggered by an external event in a real system
        # (e.g., person detected at the door, button press)
        # For testing, we run it once.
        print("\n--- Starting NeoBell Main Interaction ---")
        # main_neo_bell_interaction_loop()
        cm = CameraManager(camera_id=0, default_width=1920, default_height=1080, default_fps=60)
        cm.start_video_recording(output_dir=".")
        cm.stop_video_recording()

        print("\n--- NeoBell Main Interaction Finished ---")
