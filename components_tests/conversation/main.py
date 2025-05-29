# main.py
import google.generativeai as genai
from dotenv import load_dotenv
import os
import time # For delays

# Import your custom modules
from tts import speak
from stt import record_with_pyaudio_and_transcribe # Assuming stt.py is in the same directory

load_dotenv()

# --- Gemini API Configuration ---
GEMINI_API_KEY = None
gemini_model = None
gemini_chat_session = None # For more general chat later, if needed

try:
    GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=GEMINI_API_KEY)
    
    gemini_model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest",
        system_instruction="You are NeoBell, a helpful AI assistant for a smart doorbell system. You help users deliver packages or leave messages for residents. Keep responses concise, friendly, and clear. When asked to classify intent, be precise."
    )
    # For general conversation later, you might use:
    # gemini_chat_session = gemini_model.start_chat(history=[])
    print("Gemini API configured and model initialized successfully.")
except Exception as e:
    print(f"Error during Gemini setup: {e}")
    # Application might not be able to run full functionality

# --- STT Configuration ---
# This will be different on Windows vs. Radxa.
# For Windows testing, based on your PyAudio success:
STT_DEVICE_ID = 1
# For Radxa, you'll need to determine this. Example:
# STT_DEVICE_ID = 0 # Or whatever index your USB mic gets on Radxa

def get_intent_from_gemini(user_reply_text):
    """
    Sends the user's reply to Gemini for intent classification.
    Returns "PACKAGE_DELIVERY", "SEND_MESSAGE", or "UNCLEAR".
    """
    if not gemini_model:
        print("Gemini model not available for intent classification.")
        return "ERROR_MODEL"

    classification_prompt = f"""
    NeoBell (the AI assistant) just asked the user: "Hello, I am NeoBell. Are you here to deliver a package or send a message?"
    The user replied: "{user_reply_text}"

    Based on the user's reply, is their primary intent to "deliver a package", "send a message", or is it "unclear/other"?
    Respond with ONLY one of the following:
    - PACKAGE_DELIVERY
    - SEND_MESSAGE
    - UNCLEAR
    """
    print(f"DEBUG: Sending to Gemini for intent: User reply was '{user_reply_text}'")
    try:
        # For classification, a direct generate_content is often cleaner
        response = gemini_model.generate_content(classification_prompt)
        classified_intent = response.text.strip().upper()

        if classified_intent in ["PACKAGE_DELIVERY", "SEND_MESSAGE", "UNCLEAR"]:
            return classified_intent
        else:
            print(f"Warning: Gemini returned an unexpected classification: {classified_intent}")
            return "UNCLEAR" # Default to unclear
    except Exception as e:
        print(f"Error communicating with Gemini API for intent: {e}")
        return "ERROR_API"

def main_neo_bell_interaction():
    if not gemini_model: # Check if Gemini setup failed
        speak("I am currently unable to process requests. Please try again later.")
        return

    # 1. NeoBell Greets
    greeting = "Hello, I am NeoBell. Are you here to deliver a package or send a message?"
    speak(greeting)
    
    time.sleep(0.5) # Small pause for user

    # 2. Listen and Transcribe
    # The stt.py function handles its own STT model loading check
    print("NeoBell is listening...")
    transcribed_text = record_with_pyaudio_and_transcribe(
        duration_seconds=7, 
        device_id_to_test=STT_DEVICE_ID
    )

    if not transcribed_text or "ERROR" in transcribed_text: # Basic check for None or error strings from STT
        speak("I didn't quite catch that. Could you please try again if you need help?")
        print(f"STT Error or no text: {transcribed_text}")
        return

    # 3. Classify Intent with Gemini
    intent = get_intent_from_gemini(transcribed_text)
    print(f"DEBUG: Classified Intent: {intent}")

    # 4. Act on Intent
    if intent == "PACKAGE_DELIVERY":
        speak("Okay, I can help with a package delivery.")
        # TODO: Start package delivery workflow (e.g., ask to show label)
        # For example, you might use a general gemini chat here:
        # if gemini_chat_session:
        #     follow_up_response = gemini_chat_session.send_message("User wants to deliver a package. Ask them to show the package label to the camera.")
        #     speak(follow_up_response.text)
        # else:
        #     speak("Please show the package label to the camera.")
        print("FLOW: Package Delivery")
    elif intent == "SEND_MESSAGE":
        speak("Alright, I can help you send a message.")
        # TODO: Start send message workflow (e.g., ask who the message is for)
        print("FLOW: Send Message")
    elif intent == "UNCLEAR":
        speak("I'm sorry, I'm not sure if you want to deliver a package or send a message. Could you please say one of those?")
    elif intent == "ERROR_MODEL" or intent == "ERROR_API":
        speak("I'm having a little trouble understanding right now. Please try again in a moment.")
    else: # Should not happen
        speak("I'm a bit confused. Let's try that again later.")

if __name__ == "__main__":
    # This is where you'd have your main application loop or trigger
    # For example, triggered by a button press or person detection on the Radxa.
    # For now, let's run the interaction once for testing.
    
    # Check if essential models are loaded before proceeding
    # stt.py handles its own stt_model check within its function
    if gemini_model:
        main_neo_bell_interaction()
    else:
        print("Critical error: Gemini model not initialized. Cannot start NeoBell interaction.")