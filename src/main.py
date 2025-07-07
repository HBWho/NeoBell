import os
import time
import logging
import sounddevice as sd
from pathlib import Path
from phrases import MAIN_LOOP
from config.logging_config import setup_logging

setup_logging()

from services.stt import STTService
from services.tts import TTSService
from services.api import GAPI
from services.user_manager import UserManager
from services.servo_service import ServoService
from services.rfid_service import RfidListenerService
from services.interaction_manager import InteractionManager
from services.camera_manager import CameraManager
from ai_services.face_processing import FaceProcessing
from ai_services.ocr_processing import OCRProcessing
from communication.aws_client import AwsIotClient
from hal.gpio import GpioManager
from hal.pin_service import GpioService
from flows.visitor_flow import VisitorFlow
from flows.delivery_flow import DeliveryFlow

BUTTON_PIN = (1, 12)  # Physical Pin 33

STT_HEAVY_MODE = (
    False  # Set to True if using a heavy STT model like vosk-model-en-us-0.22
)

MICROPHONE_NAME = "USB PnP Sound Device"

logger = logging.getLogger(__name__)


def find_stt_device_id(device_name_substring: str) -> int | None:
    """
    Finds the device index for an audio input device that contains a specific substring.

    This makes device selection robust against changes in device order.

    Args:
        device_name_substring: A unique part of the desired device's name.

    Returns:
        The integer index of the found device, or None if not found.
    """
    try:
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            # We are looking for an INPUT device that contains our target name
            is_input = device.get("max_input_channels", 0) > 0
            name_matches = (
                device_name_substring.lower() in device.get("name", "").lower()
            )

            if is_input and name_matches:
                logger.info(
                    f"Found matching STT device: '{device['name']}' with index {i}."
                )
                return i
    except Exception as e:
        logger.error("Could not query audio devices.", exc_info=True)
        return None

    logger.warning(
        f"Could not find an input device matching '{device_name_substring}'. STT might not work."
    )
    logger.warning(f"Available devices: {devices}")
    return None


class Orchestrator:
    """
    The main application class that initializes all services, handlers,
    and orchestrates the primary user interaction flow.
    """

    def __init__(self):
        """Initializes configuration. Services are initialized in __enter__."""
        logger.info("Orchestrator initializing...")
        self._load_config()
        self.aws_client = None
        self.gpio_manager = None
        self.gpio_service = None
        self.user_manager = None
        self.gapi_service = None
        self.stt_service = None
        self.tts_service = None
        self.camera_manager = None
        self.face_processor = None
        self.ocr_service = None
        self.servo_service = None
        self.rfid_listener = None

    def __enter__(self):
        """Context manager entry: initializes and connects all services."""
        logger.info("Entering runtime context. Initializing services...")
        self._init_services()
        self.aws_client.connect()
        self.rfid_listener.start()
        self._init_flow_handlers(self.aws_client)
        return self  # Return the instance to be used in the 'with' block

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit: ensures all resources are released."""
        logger.info("Exiting runtime context. Shutting down services...")

        if self.rfid_listener:
            self.rfid_listener.stop()
        if self.aws_client:
            self.aws_client.disconnect()
        if self.gpio_manager:
            self.gpio_manager.close()
        logger.info("All services shut down gracefully.")
        # If an exception occurred, it can be logged here
        if exc_type:
            logger.error(
                "Application exited with an exception.",
                exc_info=(exc_type, exc_val, exc_tb),
            )

    def _load_config(self):
        """Loads all necessary configuration from environment variables."""
        logger.info("Loading configuration from environment variables...")
        self.sbc_id = os.getenv("CLIENT_ID")
        self.endpoint = os.getenv("AWS_IOT_ENDPOINT")
        self.port = os.getenv("PORT")

        # self.model_path = "models/vosk-model-small-en-us-0.15"
        self.model_path = (
            "base"
            if STT_HEAVY_MODE
            else "tiny"
        )
        self.cert_path = "certifications/10da83970c7ac9793d1f4c33c48f082924dc1aaccd0e8e8fd229d13b5caa210e-certificate.pem.crt"
        self.key_path = "certifications/10da83970c7ac9793d1f4c33c48f082924dc1aaccd0e8e8fd229d13b5caa210e-private.pem.key"
        self.ca_path = "certifications/AmazonRootCA1.pem"

    def _init_services(self):
        """Initializes singleton services used across the application."""
        logger.info("Initializing core services (TTS, STT, etc.)...")
        user_db_file = Path.cwd() / "data" / "users.json"
        self.aws_client = AwsIotClient(
            self.sbc_id,
            self.endpoint,
            self.port,
            self.cert_path,
            self.key_path,
            self.ca_path,
        )
        self.user_manager = UserManager(db_path=user_db_file)
        self.gapi_service = GAPI(debug_mode=True)
        self.tts_service = TTSService()
        self.camera_manager = CameraManager()
        self.face_processor = FaceProcessing(self.camera_manager)
        self.ocr_service = OCRProcessing()
        self.servo_service = ServoService(pwm_chip=1, pwm_channel=0)

        stt_device_id = find_stt_device_id(MICROPHONE_NAME)
        if stt_device_id is None:
            logger.critical(
                "Could not find a suitable STT audio device. STT will be disabled."
            )
            self.stt_service = None
        else:
            self.stt_service = STTService(
                model_name=self.model_path, device_id=stt_device_id
            )

        input_pins = [BUTTON_PIN]
        output_pins = [
            (4, 9),
            (4, 5),
            (4, 2),
            (4, 8),  # LEDs
            (1, 8),
            (1, 13),
            (4, 12),  # Locks
        ]
        self.gpio_manager = GpioManager(output_pins=output_pins, input_pins=input_pins)
        self.gpio_service = GpioService(gpio_manager=self.gpio_manager)

        self.rfid_listener = RfidListenerService(
            aws_client=self.aws_client, gpio_service=self.gpio_service
        )

        self.interaction_manager = InteractionManager(
            tts_service=self.tts_service, stt_service=self.stt_service
        )

    def _init_flow_handlers(self, aws_client):
        """Initializes the specific flow handlers, injecting dependencies."""
        logger.info("Initializing flow handlers (Visitor, Delivery)...")
        common_services = {
            "aws_client": aws_client,
            "user_manager": self.user_manager,
            "gpio_service": self.gpio_service,
            "tts_service": self.tts_service,
            "stt_service": self.stt_service,
            "gapi_service": self.gapi_service,
            "face_processor": self.face_processor,
            "ocr_processing": self.ocr_service,
            "camera_manager": self.camera_manager,
            "servo_service": self.servo_service,
            "interaction_manager": self.interaction_manager,
        }

        self.visitor_handler = VisitorFlow(**common_services)
        self.delivery_handler = DeliveryFlow(**common_services)

    def run_interaction_loop(self):
        """
        Runs the main interaction loop, asking the user for their intent
        and dispatching to the correct flow handler.
        """
        logger.info("System ready.")
        self.aws_client.submit_log(
            event_type="device_status_change",
            summary="Boot Notification",
            details={"Status": "System ready"},
        )

        while True:
            try:
                self.gpio_service.set_external_red_led(True)
                # self.gpio_service.set_camera_led(False)
                # self.gpio_service.set_internal_led(True)
                logger.info("Waiting for button press to start interaction...")

                # self.delivery_handler.start_delivery_flow() # TODO
                # continue # TODO
                # Wait for the button to be pressed
                while self.gpio_service.manager.get_pin_value(BUTTON_PIN):
                    time.sleep(0.1)

                logger.info("Button pressed! Starting main conversation flow.")
                # self.aws_client.submit_log(
                #     event_type="doorbell_pressed",
                #     summary="Doorbell pressed",
                #     details={
                #         "Button": "Pressed",
                #         "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                #     },
                # )
                time.sleep(0.5)

                # Intent detection loop (allows retry on unclear intent)
                max_intent_attempts = 1
                attempt = 0
                text = None
                intent = None
                while attempt < max_intent_attempts:
                    if attempt == 0:
                        # First attempt: use greeting
                        text = self.interaction_manager.ask_question(
                            MAIN_LOOP["greeting"],
                            max_listen_duration=7,
                            max_attempts=1,
                        )
                    else:
                        # Retry: just prompt for delivery/message
                        text = self.interaction_manager.ask_question(
                            MAIN_LOOP["unclear_intent"],
                            max_listen_duration=7,
                            max_attempts=1,
                        )
                    if not text:
                        attempt += 1
                        continue
                    
                    # intent = self.gapi_service.get_initial_intent(text).value
                    # intent = "VISITOR_MESSAGE"
                    intent = "PACKAGE_DELIVERY"
                    logger.info(f"Detected intent: '{intent}'")
                    if intent in ("VISITOR_MESSAGE", "PACKAGE_DELIVERY"):
                        break
                    attempt += 1

                if not text or intent not in ("VISITOR_MESSAGE", "PACKAGE_DELIVERY"):
                    self.aws_client.submit_log(
                        event_type="intent_failed",
                        summary="Intent Detection Failed",
                        details={"Attempts": attempt, "LastText": text or "(no input)"},
                    )
                    time.sleep(2)
                    continue

                if intent == "VISITOR_MESSAGE":
                    self.aws_client.submit_log(
                        event_type="visitor_flow_started",
                        summary="Visitor Flow Started",
                        details={"IntentText": text},
                    )
                    self.visitor_handler.start_interaction()
                elif intent == "PACKAGE_DELIVERY":
                    self.aws_client.submit_log(
                        event_type="delivery_flow_started",
                        summary="Delivery Flow Started",
                        details={"IntentText": text},
                    )
                    self.delivery_handler.start_delivery_flow()

                logger.info("Flow finished. Returning to idle state in 5 seconds...")
                time.sleep(5)

            except KeyboardInterrupt:
                logger.info("User interrupted the loop. Shutting down.")
                break
            except Exception as e:
                logger.error(
                    "An error occurred during the interaction loop.", exc_info=True
                )
                self.aws_client.submit_log(
                    event_type="error_occurred",
                    summary="Error occurred",
                    details={"Exception": str(e)},
                )
                self.tts_service.speak(MAIN_LOOP["error"])
                time.sleep(2)


def main():
    """The main entry point of the application."""
    setup_logging()
    logger.info("Application starting up...")
    try:
        with Orchestrator() as app:
            app.run_interaction_loop()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user (Ctrl+C).")
    except Exception:
        logger.critical(
            "A fatal error occurred, forcing application to exit.", exc_info=True
        )
    finally:
        logger.info("System has shut down.")


if __name__ == "__main__":
    main()
