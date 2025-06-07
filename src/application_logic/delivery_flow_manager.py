import time
import os
import sys

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_CURRENT_DIR) 
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from services.tts import TTSService


tts = TTSService(
    engine_path=app_config.ESPEAK_NG_PATH,
    lang=app_config.TTS_LANG
)


greeting = "Hello, I am NeoBell. Are you here to deliver a package, or are you a visitor?"
tts.speak(greeting)

tts.speak("Okay, you're here to deliver a package.")
tts.speak("Please show the package label clearly to the external camera.")
time.sleep(5)
tts.speak("Thank you. I am verifying the details.")
time.sleep(5)
tts.speak("Compartment one is unlocked. Please place the package inside with the receipt or label facing upwards towards the internal camera.")
