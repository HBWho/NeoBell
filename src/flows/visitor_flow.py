import time
import os
import logging
from pathlib import Path
from src.phrases import VISITOR

logger = logging.getLogger(__name__)


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
        self.aws = services.get(
            "aws_client"
        )  # AWS IoT client for logging and permission checks
        self.user_manager = services.get("user_manager")  # Local user DB manager
        self.gpio = services.get("gpio_service")  # GPIO hardware abstraction
        self.tts = services.get("tts_service")  # Text-to-Speech service
        self.stt = services.get("stt_service")  # Speech-to-Text service
        self.face_proc = services.get("face_processor")  # Face recognition/recording
        self.interaction_manager = services.get(
            "interaction_manager"
        )  # Centralized interaction logic
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

        # Step 1: Greet and prompt user to look at the camera
        self.tts.speak(VISITOR["start"])
        time.sleep(1)

        # Step 2: Attempt face recognition
        is_recognized, recognized_user_id = self._handle_recognition()

        # Step 3: If recognized, check permissions; else, start registration
        if is_recognized:
            user_data = self.user_manager.get_user_by_id(recognized_user_id)
            if user_data:
                user_name = user_data.get("name", "Unknown")
                self._handle_known_visitor(user_name, recognized_user_id)
            else:
                # Local DB inconsistency: face found but no user record
                logger.error(
                    f"Inconsistency: Face for user_id '{recognized_user_id}' recognized, but user not in users.json."
                )
                self.tts.speak("I'm sorry, a system error occurred with your profile.")
        else:
            self._handle_new_visitor_registration()

    def _handle_recognition(self):
        """
        Activates camera LED, prompts user, and attempts face recognition.
        Returns (is_recognized: bool, user_id_or_name: str).
        """
        self.gpio.set_camera_led(True)
        self.tts.speak(VISITOR["face_recognition"])
        known_faces_db_path = str(Path.cwd() / "data" / "known_faces_db")
        is_recognized, name = self.face_proc.recognize_face(0, known_faces_db_path)
        self.gpio.set_camera_led(False)
        return is_recognized, name

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
        Handles the registration flow for a new (unrecognized) visitor:
        - Asks if the user wants to register (up to 3 attempts)
        - If yes, asks for name (up to 3 attempts)
        - Creates user and face folder, takes photos
        - Registers user in AWS and local DB
        - Confirms before recording a message
        - Handles all errors and logs events
        """
        logger.info("New visitor detected.")
        self.aws.submit_log(
            event_type="visitor_detected",
            summary="Unknown visitor detected",
            details={},
        )

        # Step 1: Ask if the user wants to register (up to 3 attempts)
        register = self.interaction_manager.ask_yes_no(
            VISITOR["unknown"], override=True
        )
        if not register:
            logger.info("New visitor didn't choose to register.")
            self.tts.speak(VISITOR["register_no"])
            return

        logger.info("New visitor decided to register.")
        # Step 2: Ask for the user's name, confirm, and allow retries until accepted or user gives up
        for attempt in range(3):
            name_from_stt = self.interaction_manager.ask_question(
                VISITOR["register_yes"],
                override=True,
                max_listen_duration=7,
                max_attempts=3,
            )
            logger.info(f"New Visitor name from STT: {name_from_stt}")
            if not name_from_stt:
                self.tts.speak(VISITOR["register_no"])
                return
            # Confirm the name with the user
            confirm_text = (
                f"I understood your name as {name_from_stt}. Is that correct?"
            )
            if self.interaction_manager.ask_yes_no(confirm_text, override=True):
                break
            elif attempt == 2:
                # User didn't confirm after 3 attempts
                logger.warning("User failed to confirm their name after 3 attempts.")
                self.tts.speak(VISITOR["register_name_fail"])
                return
            self.tts.speak("Let's try again. Please say your name clearly.")

        # Step 3: Create user in local DB
        new_user_id, _ = self.user_manager.create_user(name_from_stt)
        if not new_user_id:
            self.tts.speak(VISITOR["register_profile_fail"])
            return

        # Step 4: Create face folder and take registration photos
        user_face_dir = Path.cwd() / "data" / "known_faces_db" / new_user_id
        os.makedirs(user_face_dir, exist_ok=True)
        self.tts.speak(VISITOR["register_photo"].format(name=name_from_stt))

        try:
            self.gpio.set_camera_led(True)
            for i in range(3):
                self.tts.speak(str(3 - i))
                time.sleep(1)
                image_path = user_face_dir / f"image_{i}.jpg"
                self.face_proc.take_picture(0, str(image_path))

            self.gpio.set_camera_led(False)
            self.tts.speak_async(VISITOR["register_photo_complete"])
            main_image_path_for_aws = str(user_face_dir / "image_0.jpg")
            # Register user in AWS
            self.aws.register_visitor(
                image_path=main_image_path_for_aws,
                visitor_name=name_from_stt,
                user_id=new_user_id,
                permission_level="Allowed",
            )
            logger.info(f"New visitor {name_from_stt} was registered successfully.")
            self.aws.submit_log(
                event_type="user_access_granted",
                summary="New visitor registered",
                details={},
            )
            self.tts.speak(VISITOR["register_complete"])
            # Step 5: Confirm before recording a message
            if self.interaction_manager.ask_yes_no(VISITOR["ask_message"]):
                self._record_and_send_message(name_from_stt, new_user_id)
            else:
                self.tts.speak(VISITOR["register_no"])

        except Exception:
            # Any error during registration
            self.tts.speak(VISITOR["register_error"])
            logger.error(
                f"It occurred an error during the registration of a new visitor ({new_user_id})"
            )
        finally:
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
                camera_id=0,
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
