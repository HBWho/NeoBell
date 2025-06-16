class DeliveryFlow:
    def __init__(self):
        pass

"""
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
    else:
        tts.speak("I didnt catch it. Are you here to deliver a package or leave a message?")
"""