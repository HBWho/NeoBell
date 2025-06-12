from services.stt import *
from services.tts import *
from services.api import *

# model_path = "models/vosk-model-en-us-0.22"
model_path = "models/vosk-model-small-en-us-0.15"

gapi = GAPI(debug_mode=True) 
stt = STTService(model_path=model_path, device_id=2)
tts = TTSService()

TARGET_DEVICE_ID = 2
print("Loading model...")
stt.load_model()
print("Model loaded!")

tts.speak("Hello. I am Neobell, are you here to deliver a package or leave a message for the resident?")
text = stt.transcribe_audio(duration_seconds=5)
print(f"text: {text}")
intent = gapi.get_initial_intent(text).value

if intent == "VISITOR_MESSAGE":
    tts.speak("Ok. Please, keep your face close to the camera in a visible way.")

elif intent == "PACKAGE_DELIVERY":
    tts.speak("Ok. Show the QR Code of the package in front of this camera. Please, center the QR Code in the camera.")
else:
    tts.speak("I didnt catch it. Are you here to deliver a package or leave a message?")

