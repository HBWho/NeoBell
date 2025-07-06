import time
import os
import logging
from pathlib import Path
# from src.phrases import VISITOR
from phrases import VISITOR

logger = logging.getLogger(__name__)

CAMERA_ID = 2

class VisitorFlow:
    """
    VisitorFlow orchestrates the entire visitor interaction process for NeoBell.
    It manages face recognition, permission checks, new visitor registration,
    and the recording/sending of video messages. All user-facing messages are
    centralized and context-aware, and error handling is robust with retries
    and clear feedback.
    """

    """
    Handles all logic related to visitor interactions, from recognition
    and registration to leaving video messages.
    """

    def __init__(self, **services):
        """
        Initializes VisitorFlow with all required service dependencies.
        Args:
            services: Dictionary of service instances (AWS, user manager, GPIO, TTS, STT, face processor, interaction manager).
        """
        """
        Initializes the flow with all its required service dependencies.
        """
        self.aws = services.get("aws_client")  # AWS IoT client for logging and permission checks
        self.user_manager = services.get("user_manager")  # Local user DB manager
        self.gpio = services.get("gpio_service")  # GPIO hardware abstraction
        self.tts = services.get("tts_service")  # Text-to-Speech service
        self.stt = services.get("stt_service")  # Speech-to-Text service
        self.face_proc = services.get("face_processor")  # Face recognition/recording
        self.interaction_manager = services.get("interaction_manager")  # Centralized interaction logic
        logger.info("Visitor Flow handler initialized.")

    def start_interaction(self):
        """
        Entry point for the visitor flow. Guides the user through recognition,
        permission check, and registration if needed. Handles all error cases
        gracefully and logs key events.
        """
        """
        Main entry point for the visitor interaction flow.
        """
        logger.info("Starting visitor interaction flow...")

        self.tts.speak(VISITOR["start"])
        time.sleep(1)

        # Step 1: Analyze the live stream to determine the situation
        status, recognized_user_id = self._handle_recognition()

        # Step 2: Handle the result based on the status from the stream analysis
        if status == "KNOWN_PERSON":
            logger.info(f"Known person detected: {recognized_user_id}. Checking permissions.")
            user_data = self.user_manager.get_user_by_id(recognized_user_id)
            
            # Handle case where user is in face DB but not user DB (data inconsistency)
            if not user_data:
                logger.error(f"Inconsistency: Face for user_id '{recognized_user_id}' recognized, but user not in users.json.")
                self.tts.speak("I'm sorry, a system error occurred with your profile.")
                return

            user_name = user_data.get("name", "a known visitor")
            self._handle_known_visitor(user_name, recognized_user_id)

        elif status == "UNKNOWN_PERSON":
            logger.info("Unknown person detected. Starting registration flow.")
            self._handle_new_visitor_registration()

        elif status == "NO_FACE": # TODO
            logger.warning("Could not recognize anyone in the given time.")
            self.tts.speak("I'm sorry, I couldn't see anyone clearly. Please press the button to try again.")
            # The flow ends here, waiting for another button press.

    def _handle_recognition(self) -> tuple[str, str | None]:
        """
        Analyzes the live stream and returns the status of who was seen.
        This is now the single point of contact for face analysis in this flow.
        """
        self.gpio.set_camera_led(True)
        self.tts.speak(VISITOR["face_recognition"])
        db_path = str(Path.cwd() / "data" / "known_faces_db")
        
        # The core of the new logic: call the stream analyzer
        status, user_id = self.face_proc.analyze_live_stream(
            camera_id=CAMERA_ID,
            db_path=db_path,
            timeout_seconds=5 # This is the timeout period you wanted
        )
        
        self.gpio.set_camera_led(False)
        return status, user_id
        

    def _handle_known_visitor(self, name: str, user_id: str):
        """
        Handles the flow for a recognized visitor:
        - Checks permissions with AWS
        - Handles local/cloud DB inconsistencies
        - If allowed, confirms and records a message
        - If denied, informs the user
        - Logs all relevant events
        """
        logger.info(
            f"Handling known visitor '{name}' with ID '{user_id}'. Checking backend permissions..."
        )

        # Query AWS for permissions
        response = self.aws.check_permissions(user_id)

        if not response:
            # AWS did not respond (timeout or error)
            logger.error(
                f"No response from AWS for permission check on user {user_id}."
            )
            self.aws.submit_log(
                event_type="visitor_permission_check",
                summary="Permission check failed",
                details={"user_id": user_id, "error": "No response from AWS"},
            )
            self.tts.speak(VISITOR["perm_later"])
            return

        if response.get("permission_exists") is False:
            # Local face found but not in cloud: treat as new visitor
            logger.warning(
                f"Data inconsistency found: Face ID '{user_id}' exists locally but has no permissions entry in the backend."
            )
            self.tts.speak(VISITOR["profile_issue"])
            faces_db_path = Path.cwd() / "data" / "known_faces_db"
            self.user_manager.delete_user(user_id, faces_db_path)
            self._handle_new_visitor_registration()
        else:
            # Permission exists in cloud
            # Log the detection event
            permission_level = response.get("permission_level")
            visitor_name_from_db = response.get("visitor_name", name)
            self.aws.submit_log(
                event_type="visitor_detected",
                summary="Known visitor detected",
                details={
                    "user_id": user_id,
                    "visitor_name": visitor_name_from_db,
                    "permission_level": permission_level,
                },
            )
            self.tts.speak(
                VISITOR["known_hello"].format(visitor_name=visitor_name_from_db)
            )
            if permission_level == "Allowed":
                # User is allowed to leave a message
                logger.info(
                    f"Permission for '{visitor_name_from_db}' is 'Allowed'. Proceeding to record message."
                )
                self.tts.speak(VISITOR["allowed"])
                # Confirm before recording
                if self.interaction_manager.ask_yes_no(VISITOR["ask_message"]):
                    self._record_and_send_message(visitor_name_from_db, user_id)
                else:
                    self.tts.speak(VISITOR["register_no"])
            elif permission_level == "Denied":
                # User is denied access
                logger.warning(f"Permission for '{visitor_name_from_db}' is 'Denied'.")
                self.tts.speak(
                    VISITOR["denied"].format(visitor_name=visitor_name_from_db)
                )
            else:
                # Unexpected permission state
                logger.error(
                    f"Inconsistent permission data for user '{visitor_name_from_db}' (ID: {user_id}). Level: '{permission_level}'."
                )
                self.tts.speak(VISITOR["perm_error"])

    def _handle_new_visitor_registration(self):
        """
        Handles registration for a new visitor using the simplified photo capture flow.
        """
        logger.info("New visitor detected, starting registration process.")
        self.aws.submit_log(event_type="visitor_detected", summary="Unknown visitor detected", details={})

        # Ask if the user wants to register
        if not self.interaction_manager.ask_yes_no(VISITOR["unknown"], override=True):
            logger.info("New visitor declined to register.")
            self.tts.speak(VISITOR["register_no"])
            return

        # Get the user's name
        name_from_stt = None
        for attempt in range(3):
            raw_name = self.interaction_manager.ask_question(
                VISITOR["register_yes"] if attempt == 0 else "Let's try again. Please say your name clearly.",
                override=True, max_listen_duration=7
            )
            if raw_name:
                confirm_text = f"I understood your name as {raw_name}. Is that correct?"
                if self.interaction_manager.ask_yes_no(confirm_text, override=True):
                    name_from_stt = raw_name
                    break
        
        if not name_from_stt:
            logger.warning("User failed to confirm their name after multiple attempts.")
            self.tts.speak(VISITOR["register_name_fail"])
            return
        
        # Create user record
        new_user_id, _ = self.user_manager.create_user(name_from_stt)
        if not new_user_id:
            self.tts.speak(VISITOR["register_profile_fail"])
            return

        # --- Simplified Face Registration Step ---
        user_face_dir = Path.cwd() / "data" / "known_faces_db" / new_user_id
        self.tts.speak(VISITOR["register_photo"].format(name=name_from_stt))
        
        try:
            self.gpio.set_camera_led(True)
            # A single, clean call to the simple registration method
            registration_success = self.face_proc.register_face_simple(
                camera_id=CAMERA_ID,
                user_folder=user_face_dir,
                num_photos=3  # Captures 3 quality photos
            )
            self.gpio.set_camera_led(False)

            if not registration_success:
                self.tts.speak(VISITOR["register_error"])
                self.user_manager.delete_user(new_user_id, user_face_dir.parent)
                return

            # --- Registration successful, proceed to AWS and messaging ---
            self.tts.speak_async(VISITOR["register_photo_complete"])
            main_image_path_for_aws = str(user_face_dir / "image_0.jpg")
            self.aws.register_visitor(
                image_path=main_image_path_for_aws,
                visitor_name=name_from_stt,
                user_id=new_user_id,
                permission_level="Allowed",
            )
            logger.info(f"New visitor '{name_from_stt}' was registered successfully.")
            self.tts.speak(VISITOR["register_complete"])

            if self.interaction_manager.ask_yes_no(VISITOR["ask_message"]):
                self._record_and_send_message(name_from_stt, new_user_id)
            else:
                self.tts.speak(VISITOR["register_no"])

        except Exception as e:
            logger.error(f"A critical error occurred during visitor registration: {e}", exc_info=True)
            self.tts.speak(VISITOR["register_error"])
            self.user_manager.delete_user(new_user_id, user_face_dir.parent)
            self.gpio.set_camera_led(False)

    def _record_and_send_message(self, name, user_id):
        """
        Handles the process of recording and sending a video message:
        - Activates camera LED and records a 10s video
        - Sends the video to AWS
        - Provides user feedback on success/failure
        - Logs all relevant events
        """
        self.tts.speak(VISITOR["recording"])
        final_video_path = f"data/visitor_message_{user_id}.mp4"
        try:
            # Step 1: Record video with audio
            self.gpio.set_camera_led(True)
            self.face_proc.record_video_with_audio(
                camera_id=CAMERA_ID,
                output_file=final_video_path,
                duration=10,
            )
            self.gpio.set_camera_led(False)
            self.tts.speak(VISITOR["done"])

            # Step 2: Send video to AWS
            success = self.aws.send_video_message(final_video_path, user_id, 10)

            # Step 3: Provide feedback to user
            if success:
                self.aws.submit_log(
                    event_type="video_message_recorded",
                    summary="Video Message Recorded",
                    details={},
                )
                self.tts.speak(VISITOR["sent"].format(visitor_name=name))
            else:
                self.tts.speak(VISITOR["not_send"])
        except Exception:
            # Any error during recording or sending
            logger.error("Failed to record or send video message.", exc_info=True)
            self.tts.speak(VISITOR["system_error"])
        finally:
            self.gpio.set_camera_led(False)
