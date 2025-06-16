import time
import os
import logging

logger = logging.getLogger(__name__)

class VisitorFlow:
    """
    Handles all logic related to visitor interactions, from recognition
    and registration to leaving video messages.
    """
    def __init__(self, aws_client, gpio_service, tts_service, stt_service, face_processor, gapi_service):
        """
        Initializes the flow with all its required service dependencies.
        """
        self.aws = aws_client
        self.gpio = gpio_service
        self.tts = tts_service
        self.stt = stt_service
        self.face_proc = face_processor
        self.gapi = gapi_service
        self.stt.load_model()
        logger.info("Visitor Flow handler initialized.")

    def start_interaction(self):
        """
        Main entry point for the visitor interaction flow.
        """
        logger.info("Starting visitor interaction flow...")
        self.tts.speak("Hello! To begin, I need to recognize you. Please look at the camera.")
        time.sleep(1)

        recognized, name, tag = self._handle_recognition()

        if not recognized:
            self._handle_new_visitor_registration()
        else:
            self._handle_known_visitor(name, tag)

    def _handle_recognition(self):
        """Handles the face recognition process and returns the result."""
        self.tts.speak("I will take a picture in... 5, 4, 3, 2, 1.")

        return self.face_proc.recognize_face(0, "data/known_faces_db")

    def _handle_known_visitor(self, name, tag):
        """Handles the flow for a visitor who was successfully recognized."""
        logger.info(f"Recognized '{name}' with tag '{tag}'. Checking permissions...")
        self.tts.speak(f"Hi, {name}. Let me check your permissions.")

        response = self.aws.check_permissions(tag)
        permission_level = response.get("permission_level") if response else None

        if permission_level == "Allowed":
            logger.info(f"Visitor '{name}' is allowed.")
            self.tts.speak("You are allowed to leave a message.")
            self._record_and_send_message(name, tag)
        else: # Covers "Denied" and other cases
            logger.warning(f"Visitor '{name}' has permission '{permission_level}'. Access denied.")
            self.tts.speak(f"Sorry, {name}. It seems you don't have permission to leave a message. Have a nice day.")

    def _handle_new_visitor_registration(self):
        """Handles the entire flow for registering a new, unknown visitor."""
        logger.info("New visitor detected.")
        self.tts.speak("It seems I don't know you. Would you like to register?")
        text = self.stt.transcribe_audio(duration_seconds=5)
        intent = self.gapi.get_initial_intent(text).value

        if intent == "No":
            logger.info("New visitor didn't choice to register yourself.")
            self.tts.speak("Ok, no problem. Have a nice day!")
            return

        logger.info("New visitor decided to register youself.")
        self.tts.speak("Great! Let's get you registered. First, could you please tell me your name?")
        name = self.stt.transcribe_audio(duration_seconds=5)
        logger.info(f"New visitor calls by {name}")
        
        self.tts.speak(f"Nice to meet you, {name}. Now, I'll take a few pictures for registration. Please stay still. Starting in 5, 4, 3, 2, 1.")
        
        image_path = "data/new_visitor_image.jpg"
        self.face_proc.take_picture(0, image_path) 

        new_face_tag = self.aws.register_visitor(image_path, name, "Allowed") 

        if new_face_tag:
            self.tts.speak(f"Thank you, {name}. Your registration is complete.")
            self._record_and_send_message(name, new_face_tag)
            logger.info(f"New visitor {name} was registered successfully.")
        else:
            self.tts.speak("I'm sorry, there was an error during registration. Please try again later.")
            logger.error(f"It occurred an error during the registration of a new visitor ({name})")

    def _record_and_send_message(self, name, tag):
        """Handles the process of recording and sending a video message."""
        self.tts.speak(f"The recording will start after the countdown and will last for 20 seconds. Starting in 5, 4, 3, 2, 1.")
        
        video_path = "data/temp_visitor_video.mp4"
        self.face_proc.record_video(0, video_path, duration=20)
        
        self.tts.speak("Recording finished. Now sending your message...")
        success = self.aws.send_video_message(video_path, tag)

        if success:
            self.tts.speak(f"Your message was successfully sent, {name}. Thank you and have a nice day!")
        else:
            self.tts.speak("I'm sorry, there was a problem sending your message. Please try again later.")