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
        self.camera_manager = services.get("camera_manager")
        self.interaction_manager = services.get("interaction_manager")  # Centralized interaction logic
        logger.info("Visitor Flow handler initialized.")

    def start_interaction(self):
        """
        Main entry point for the visitor interaction flow, using centralized phrases.
        """
        logger.info("Starting visitor interaction flow...")
        self.tts.speak(VISITOR["start"])
        time.sleep(1)

        max_retries = 3
        for attempt in range(max_retries):
            logger.info(f"Recognition attempt #{attempt + 1}")
            
            status, recognized_user_id = self._handle_recognition()

            # --- Success Cases ---
            if status == "KNOWN_PERSON":
                logger.info(f"Known person detected: {recognized_user_id}.")
                user_data = self.user_manager.get_user_by_id(recognized_user_id)
                if not user_data:
                    logger.error(f"Inconsistency: Face for '{recognized_user_id}' found, but user not in users.json.")
                    self.tts.speak(VISITOR["system_error"])
                    break 
                
                user_name = user_data.get("name", "a known visitor")
                self._handle_known_visitor(user_name, recognized_user_id)
                break 

            elif status == "UNKNOWN_PERSON":
                logger.info("Unknown person detected. Starting registration flow.")
                self._handle_new_visitor_registration()
                break 

            # --- NO_FACE Retry Logic with New Phrases ---
            elif status == "NO_FACE":
                logger.warning(f"Could not recognize anyone on attempt {attempt + 1}.")
                self.tts.speak(VISITOR["recognition_fail"])
                
                if attempt == max_retries - 1:
                    self.tts.speak(VISITOR["max_retries_fail"])
                    break
                
                # Ask the user to retry using the new phrase
                if self.interaction_manager.ask_yes_no(VISITOR["ask_retry"]):
                    self.tts.speak(VISITOR["confirm_retry"])
                else:
                    # Reuse the standard goodbye phrase
                    self.tts.speak(VISITOR["register_no"]) 
                    break

        logger.info("Visitor interaction flow finished.")

    def _handle_recognition(self, timeout_seconds: int = 7) -> tuple[str, str | None]:
        """
        Analyzes the camera feed frame-by-frame for a set duration.

        It controls the loop and calls the simplified analyze_person
        method from the FaceProcessing class for each frame.
        """
        self.tts.speak(VISITOR["face_recognition"])
        start_time = time.time()
        temp_image_path = "data/temp_live_frame.jpg"

        while time.time() - start_time < timeout_seconds:
            # 1. Take a single picture
            if not self.camera_manager.take_picture(CAMERA_ID, temp_image_path):
                time.sleep(0.5)
                continue # Try again if picture fails

            # 2. Analyze that single picture using your new reliable method
            status, user_id = self.face_proc.analyze_person(temp_image_path)

            # 3. Act on the result
            if status in ["KNOWN_PERSON", "UNKNOWN_PERSON"]:
                # If we get a clear result (known or unknown), we're done.
                return status, user_id
            
            # If result is "NO_FACE" or "BAD_QUALITY", the loop continues to try again.
            time.sleep(0.5) # Small delay before next attempt

        # If the loop finishes without a clear result
        logger.info("Recognition timeout. No clear face was identified.")
        return "NO_FACE", None

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

        try:
            # A single call to the new batch registration method.
            # We pass the gpio and tts services so it can handle LED and announcements.
            registration_success = self.face_proc.register_face(
                camera_id=CAMERA_ID,
                user_folder=user_face_dir,
                gpio=self.gpio,
                tts=self.tts
            )

            if not registration_success:
                self.tts.speak(VISITOR["register_error"])
                # The batch function handles its own cleanup, we just need to delete the user record
                self.user_manager.delete_user(new_user_id) 
                return

            # --- Registration successful, proceed to AWS and messaging ---
            # The "processing" message is handled inside the batch function,
            # so we can go straight to completion.
            self.tts.speak(VISITOR["register_complete"])

            # Register with AWS and ask to leave a message...
            main_image_path_for_aws = str(user_face_dir / "image_0.jpg")
            self.aws.register_visitor(
                image_path=main_image_path_for_aws,
                visitor_name=name_from_stt,
                user_id=new_user_id,
                permission_level="Allowed",
            )

            if self.interaction_manager.ask_yes_no(VISITOR["ask_message"]):
                self._record_and_send_message(name_from_stt, new_user_id)
            else:
                self.tts.speak(VISITOR["register_no"])

        except Exception as e:
            logger.error(f"A critical error occurred during visitor registration: {e}", exc_info=True)
            self.tts.speak(VISITOR["system_error"])
            self.user_manager.delete_user(new_user_id)
        

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
            self.camera_manager.record_video_with_audio(
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
