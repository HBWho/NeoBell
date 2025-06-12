import time
from services.stt import *
from services.tts import *
from services.api import *
from communication.aws import *
from hal.gpio import *
from hal.servo import *
from hal.pin import *
from ai_services.ocr_processing import *
from ai_services.face_processing import *

# model_path = "models/vosk-model-en-us-0.22"
model_path = "models/vosk-model-small-en-us-0.15"

gapi = GAPI(debug_mode=True) 
stt = STTService(model_path=model_path, device_id=1)
tts = TTSService()
ocrp = OCRProcessing()
facereg = FaceProcessing()
servo = ServoClass()

print("Loading model...")
stt.load_model()
print("Model loaded!")

try:
    PINService = PINService()
    PINService.activate_red()

    PINService.activate_collect_lock()
    time.sleep(5)
    PINService.deactivate_collect_lock()
    raise Exception("")
    
    # PINService.deactivate_internal_lock()
    # PINService.deactivate_external_lock()

    tts.speak("Hello. I am Neobell, are you here to deliver a package or leave a message for the resident?")
    text = stt.transcribe_audio(duration_seconds=5)
    print(f"text: {text}")
    intent = gapi.get_initial_intent(text).value
    print(f"intent: {intent:}")
    
    if intent == "VISITOR_MESSAGE":
        tts.speak("Ok. Please, keep your face close to the camera in a visible way. Photo will be taken in 3, 2, 1.")
        valid, name = facereg.recognize_face(0, "data/known_faces_db")
        if valid:
            tts.speak(f"Hello {name}. Stand in front of the camera. Your video will be recorded in 3, 2, 1.")
            facereg.record_video(0)
            # record video
            
            visitor_face_tag = "634eaa37-5728-451a-8df4-7008bb14a3a9"
            testar_envio_mensagem_video("temp_video.avi", face_id_visitante=visitor_face_tag)
            tts.speak(f"Your video was registered and sent for the resident. Thank you and have a nice day!")

    elif intent == "PACKAGE_DELIVERY":
        tts.speak("Ok. Show the QR Code of the package in front of this camera. Please, center the QR Code in the camera. Photo will be taken in 3, 2, 1. Photo taken.")
        ocrp.take_picture(0) # 0 for external camera
        # codes = ocrp.process_codes("temp_image.jpg")
        # if codes:
        time.sleep(4)
        tts.speak("Packaged verified. Please, deliver the package inside the compartment with the QR code facing up.")
        PINService.deactivate_red()
        time.sleep(1)
        PINService.activate_green()
        time.sleep(1)
        PINService.activate_external_lock() 
        time.sleep(1)
        PINService.activate_internal_led()
        time.sleep(6)
        tts.speak("The package will be verified soon.")
        PINService.deactivate_external_lock()
        # verificacao de pacote
        ocrp.take_picture(2) # 0 for external camera
        # codes = ocrp.process_codes("")
        time.sleep(6)
        servo.servopadrao()
        time.sleep(2)
        tts.speak("Package validated! Thank you and have a nice day")
        
        # time.sleep(3)
        # print("Passa a Tag em:")
        # print("3")
        # print("2")
        # print("1")
        # PINService.activate_collect_lock()

    else:
        tts.speak("I didnt catch it. Are you here to deliver a package or leave a message?")

    # ocrp.take_picture(2) # 2 for internal camera
    # ocrp.process_codes("temp_image.jpg")
finally:
    # PINService.deactivate_red()
    PINService.deactivate_green()
    PINService.deactivate_external_lock() 
    PINService.deactivate_internal_lock()
    PINService.deactivate_collect_lock()
    # deactivate_pin(4, 2)
