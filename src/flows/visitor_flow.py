import time
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class VisitorFlow:
    """
    Handles all logic related to visitor interactions, from recognition
    and registration to leaving video messages.
    """
    def __init__(self, aws_client, user_manager, gpio_service, tts_service, stt_service, face_processor, gapi_service):
        """
        Initializes the flow with all its required service dependencies.
        """
        self.aws = aws_client
        self.user_manager = user_manager
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

        is_recognized, recognized_user_id = self._handle_recognition()

        if is_recognized:
            user_data = self.user_manager.get_user_by_id(recognized_user_id)
            if user_data:
                user_name = user_data.get("name", "Unknown")
                self._handle_known_visitor(user_name, recognized_user_id)
            else:
                logger.error(f"Inconsistency: Face for user_id '{recognized_user_id}' recognized, but user not in users.json.")
                self.tts.speak("I'm sorry, a system error occurred with your profile.")
        else:
            self._handle_new_visitor_registration()

    def _handle_recognition(self):
        """Handles the face recognition process and returns the result."""
        self.tts.speak("I will take a picture in... 5, 4, 3, 2, 1.")
        known_faces_db_path = str(Path.cwd() / "data" / "known_faces_db")
        is_recognized, name = self.face_proc.recognize_face(0, known_faces_db_path)

        return is_recognized, name

    def _handle_known_visitor(self, name: str, user_id: str):
        """Handles the flow for a known visitor using their unique ID."""
        logger.info(f"Handling known visitor '{name}' with ID '{user_id}'.")
        response = self.aws.check_permissions(user_id)
        user_exists = response.get("permission_exists") if response else False

        if not user_exists:
            faces_db_path = Path.cwd() / "data" / "known_faces_db"
            self.user_manager.delete_user(user_id, faces_db_path)
            self._handle_new_visitor_registration()
        else:
            permission_level = response.get("permission_level") if response else None
            self.tts.speak(f"Hi, {name}. Let me check your permissions.")
            if permission_level == "Allowed":
                logger.info(f"Visitor '{name}' is allowed.")
                self.tts.speak("You are allowed to leave a message.")
                self._record_and_send_message(name, user_id)
            else: # Covers "Denied" and other cases
                logger.warning(f"Visitor '{name}' has permission '{permission_level}'. Access denied.")
                self.tts.speak(f"Sorry, {name}. It seems you don't have permission to leave a message. Have a nice day.")

    def _handle_new_visitor_registration(self):
        """Handles registering a new visitor, creating a unique ID, and saving face data."""
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
        name_from_stt = self.stt.transcribe_audio(duration_seconds=5)
        if not name_from_stt:
            self.tts.speak("I'm sorry, I couldn't understand your name. Please try again later.")
            return

        new_user_id, _ = self.user_manager.create_user(name_from_stt)
        if not new_user_id:
            self.tts.speak("I'm sorry, there was an error creating your profile.")
            return

        user_face_dir = Path.cwd() / "data" / "known_faces_db" / new_user_id
        os.makedirs(user_face_dir, exist_ok=True)
        
        self.tts.speak(f"Nice to meet you, {name_from_stt}. Now, I will take a few pictures for registration. Please stay still. Starting in 5, 4, 3, 2, 1.")

        try:
            for i in range(3):
                self.tts.speak(str(3 - i))
                time.sleep(1)
                image_path = user_face_dir / f"image_{i}.jpg"
                self.face_proc.take_picture(0, str(image_path))

            self.tts.speak("Registration pictures taken successfully.")
            # Use the first image for AWS user registration
            main_image_path_for_aws = str(user_face_dir / "image_0.jpg")
            
            self.aws.register_visitor(
                image_path=main_image_path_for_aws,
                visitor_name=name_from_stt,
                user_id=new_user_id,
                permission_level="Allowed"
            )
            self.tts.speak(f"Thank you, {name_from_stt}. Your registration is complete.")
            logger.info(f"New visitor {name_from_stt} was registered successfully.")
            self._record_and_send_message(name_from_stt, new_user_id)

        except Exception as e:
            self.tts.speak("I'm sorry, there was an error during registration.")
            logger.error(f"It occurred an error during the registration of a new visitor ({new_user_id})")

    def _record_and_send_message(self, name, user_id):
        """Handles the process of recording and sending a video message."""
        self.tts.speak(f"The recording will start after the countdown and will last for 10 seconds. Starting in 5, 4, 3, 2, 1.")
        
        final_video_path = f"data/visitor_message_{user_id}.mp4"
        
        try:
            self.face_proc.record_video_with_audio(
                camera_id=0,
                output_file=final_video_path,
                duration=10,
            )
            
            self.tts.speak("Recording finished. Now sending your message...")
            success = self.aws.send_video_message(final_video_path, user_id, 10)

            if success:
                self.tts.speak(f"Your message was successfully sent, {name}. Thank you and have a nice day!")
            else:
                self.tts.speak("I'm sorry, there was a problem sending your message.")

        except Exception as e:
            logger.error("Failed to record or send video message.", exc_info=True)
            self.tts.speak("I'm sorry, an error occurred during recording. Please try again later.")
