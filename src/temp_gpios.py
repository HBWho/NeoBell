import time
import os
import sys
import config as app_config
from gpio import activate_pin, deactivate_pin

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_CURRENT_DIR) 
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from services.tts import TTSService


tts = TTSService(
    engine_path=app_config.ESPEAK_NG_PATH,
    lang=app_config.TTS_LANG
)

# LED status V PIN 38 c4, 5
# LED status G PIN 40 c4, 9

# LED interno PIN 36 c4, 2
# Solenoide da porta de entrega PIN 18 c1, 8
# Solenoide do alcapao PIN 22 c1, 13
# Pino da ESP PIN 5 c1, 30 -- mesmo pino do servo

deactivate_pin(1, 30)
# Ativa LED no Vermelho
activate_pin(4, 5)
# LED interna sempre ligada
activate_pin(4, 2)
tts.speak("Hello, I am NeoBell. Are you here to deliver a package, or are you a visitor?")
time.sleep(5)
tts.speak("Okay, you're here to deliver a package.")
tts.speak("Please show the package label clearly to the external camera.")
time.sleep(5)
tts.speak("Thank you. I am verifying the details.")
time.sleep(5)
tts.speak("Compartment one is unlocked. Please place the package inside with the receipt or label facing upwards towards the internal camera.")
# Ativa Solenoide para abertura
activate_pin(1, 8)
# Muda LED para Verde
deactivate_pin(4, 5)
activate_pin(4, 9)
time.sleep(3)
# Desativa Solenoide 
deactivate_pin(1, 8)
time.sleep(5)
tts.speak("Thank you. Package detected. Closing compartment and starting internal scan.")
time.sleep(10)
tts.speak("Packaged authorized!")
# Ativa Solenoide alcapao
activate_pin(1, 13)
time.sleep(2)
# Manda sinal pra ESP 
activate_pin(1, 30)
time.sleep(2)
tts.speak("Thank you for your delivery! The package is now secure.")


