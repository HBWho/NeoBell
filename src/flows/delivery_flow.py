import time
import os
import logging
from src.phrases import DELIVERY

logger = logging.getLogger(__name__)

# Constants for camera IDs
EXTERNAL_CAMERA = 0
INTERNAL_CAMERA = 2


class DeliveryFlow:
    """Handles the entire package delivery workflow using refactored services."""

    def __init__(self, **services):
        """Initializes the flow with all its required service dependencies."""
        self.aws = services.get("aws_client")
        self.gpio = services.get("gpio_service")
        self.tts = services.get("tts_service")
        self.ocr = services.get("ocr_processing")
        self.servo = services.get("servo_service")
        self.face_proc = services.get("face_processor")
        self.interaction_manager = services.get("interaction_manager")
        logger.info("Delivery Flow handler initialized.")

    def start_delivery_flow(self):
        """
        Main entry point for the delivery interaction flow.
        Guides the user through package scanning, validation, compartment handling,
        and final confirmation. All messages are centralized and user-friendly.
        """
        logger.info("Starting delivery flow...")
        self.gpio.set_external_red_led(True)
        self.gpio.set_external_green_led(False)

        try:
            validated_code = self._scan_and_validate_external_package()
            if validated_code:
                logger.info(
                    f"Valid package code '{validated_code}' found. Proceeding with delivery."
                )
                self._handle_compartment_door(DELIVERY["compartment"])
                is_same_package = self._scan_internal_package(validated_code)
                if is_same_package:
                    self._finalize_delivery()
                else:
                    logger.info("Package rejected due to mismatch.")
                    self._handle_compartment_door(DELIVERY["cancel_inside"])
            else:
                self.tts.speak_async(DELIVERY["cancel"])

        except Exception:
            logger.error(
                "An unexpected error occurred during the delivery flow.", exc_info=True
            )
            self.tts.speak(DELIVERY["error"])

        finally:
            logger.info("Ensuring all hardware is in a safe final state.")
            self.gpio.set_internal_led(False)
            self.gpio.set_external_green_led(False)
            self.gpio.set_external_red_led(True)

    def _scan_and_validate_external_package(self) -> str | None:
        """
        Scans for a package, validates it with AWS, and handles user feedback.
        Retries up to 3 times if validation fails.
        """
        self.gpio.set_camera_led(True)

        # Announce the initial action to the user without blocking the scan
        self.tts.speak_async(DELIVERY["start"])

        def aws_checker_callback(code):
            return self.aws.request_package_info("tracking_number", code)

        def on_timeout():
            self.tts.speak_async(
                "Move it closer to the camera and move it gently to help with scanning."
            )

        scan_timeout = 10.0
        max_scan_attempts = 3

        logger.info("External package scan attempt")

        result = self.ocr.find_validated_code(
            camera_id=EXTERNAL_CAMERA,
            fast_mode=True,
            code_verification_callback=aws_checker_callback,
            timeout_sec=scan_timeout,
            retries=max_scan_attempts,
            on_timeout=on_timeout,
        )

        if result["status"] == "success":
            self.gpio.set_camera_led(False)
            return result["code"]
        elif result["status"] == "not_accepted":
            logger.warning(
                f"External package scan failed. Response: {result['response']}"
            )
            if self.interaction_manager.ask_yes_no(DELIVERY["not_accepted"]):
                return self._scan_and_validate_external_package()
        else:
            if self.interaction_manager.ask_yes_no(DELIVERY["timeout"]):
                logger.info("User chose to retry the external package scan.")
                return self._scan_and_validate_external_package()
            else:
                logger.info("User chose not to retry the external package scan.")

        self.gpio.set_camera_led(False)
        return None

    def _scan_internal_package(self, original_valid_codes: str) -> bool:
        """
        Scans the package inside the compartment and checks if the code matches the original.
        All user messages are centralized and clear.
        """
        self.tts.speak_async(DELIVERY["checking"])
        logger.info(
            f"Performing internal package scan, looking for: {original_valid_codes}"
        )
        self.gpio.set_internal_led(True)

        def local_checker_callback(code_to_check):
            return {
                "package_same": True if code_to_check in original_valid_codes else False
            }

        def on_timeout():
            self._handle_compartment_door(DELIVERY["internal_fail"])

        scan_timeout = 6.0
        max_scan_attempts = 3

        logger.info("Internal package scan attempt")

        result = self.ocr.find_validated_code(
            camera_id=INTERNAL_CAMERA,
            fast_mode=False,
            code_verification_callback=local_checker_callback,
            timeout_sec=scan_timeout,
            retries=max_scan_attempts,
            on_timeout=on_timeout,
        )

        if result["status"] == "success":
            logger.info(
                "Internal package verification successful. A matching code was found."
            )
            self.gpio.set_internal_led(False)
            return True

        logger.error(
            f"Internal scan failed after all attempts. No match found for {original_valid_codes}."
        )
        if self.interaction_manager.ask_yes_no(DELIVERY["internal_fail"]):
            logger.info("User chose to retry the internal package scan.")
            self._handle_compartment_door(DELIVERY["internal_adjust"])
            return self._scan_internal_package(original_valid_codes)
        else:
            logger.info("User chose not to retry the internal package scan.")

        self.gpio.set_internal_led(False)
        return False

    def _handle_compartment_door(self, tts_text: str):
        """
        Opens the compartment and instructs the user with a clear, centralized message.
        """
        self.tts.speak_async(tts_text, override=True)
        self.gpio.set_external_red_led(False)
        self.gpio.set_external_green_led(True)
        self.gpio.set_external_lock(True)
        time.sleep(14)
        self.gpio.set_external_lock(False)
        self.gpio.set_external_green_led(False)
        self.gpio.set_external_red_led(True)

    def _finalize_delivery(self):
        """
        Handles the successful delivery confirmation and secures the package.
        All user feedback is centralized and friendly.
        """
        self.tts.speak_async(DELIVERY["finalize"], override=True)
        self.aws.submit_log(
            event_type="package_detected", summary="Package delivered", details={}
        )
        logger.info("Finalizing delivery...")

        self.gpio.set_internal_led(True)
        self.gpio.set_external_green_led(False)
        self.gpio.set_external_red_led(True)

        video_filename = f"delivery_capture_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
        video_filepath = os.path.join("data", "captures", video_filename)
        os.makedirs(os.path.dirname(video_filepath), exist_ok=True)

        try:
            self.face_proc.start_background_recording(INTERNAL_CAMERA, video_filepath)
            time.sleep(1)
            self.servo.openHatch()
            time.sleep(5)
            self.servo.closeHatch()
        except Exception:
            logger.error(
                "An error occurred during the finalization sequence.", exc_info=True
            )
        finally:
            self.face_proc.stop_background_recording()
            self.gpio.set_internal_led(False)

        logger.info(
            f"Delivery finalized and package secured. Capture saved to {video_filepath}"
        )
