import os
import time
import logging

from config.logging_config import setup_logging
setup_logging()

from services.stt import STTService
from services.tts import TTSService
from services.api import GAPI
from ai_services.face_processing import FaceProcessing
from communication.aws_client import AwsIotClient
from flows.visitor_flow import VisitorFlow
from flows.delivery_flow import DeliveryFlow

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    The main application class that initializes all services, handlers,
    and orchestrates the primary user interaction flow.
    """
    def __init__(self):
        """Initializes services and starts the application lifecycle."""
        try:
            logger.info("Orchestrator starting up...")
            self._load_config()
            self._init_services()

            with AwsIotClient(self.sbc_id, self.endpoint, self.port, self.cert_path, self.key_path, self.ca_path) as aws_client:
                self._init_flow_handlers(aws_client)
                self.run_interaction_loop()

        except Exception as e:
            logger.critical("A critical error occurred during Orchestrator initialization.", exc_info=True)
            if hasattr(self, 'tts_service'):
                self.tts_service.speak("A critical system error occurred. Shutting down.")

    def _load_config(self):
        """Loads all necessary configuration from environment variables."""
        logger.info("Loading configuration from environment variables...")
        self.sbc_id = os.getenv("CLIENT_ID")
        self.endpoint = os.getenv("AWS_IOT_ENDPOINT")
        self.port = os.getenv("PORT")
        self.model_path = "models/vosk-model-small-en-us-0.15"
        self.cert_path = "certifications/10da83970c7ac9793d1f4c33c48f082924dc1aaccd0e8e8fd229d13b5caa210e-certificate.pem.crt"
        self.key_path = "certifications/10da83970c7ac9793d1f4c33c48f082924dc1aaccd0e8e8fd229d13b5caa210e-private.pem.key"
        self.ca_path = "certifications/AmazonRootCA1.pem"

    def _init_services(self):
        """Initializes singleton services used across the application."""
        logger.info("Initializing core services (TTS, STT, etc.)...")
        self.gapi_service = GAPI(debug_mode=True)
        self.stt_service = STTService(model_path=self.model_path, device_id=1)
        self.tts_service = TTSService()
        self.face_processor = FaceProcessing()
        self.gpio_service = None # Placeholder for GpioService

    def _init_flow_handlers(self, aws_client):
        """Initializes the specific flow handlers, injecting dependencies."""
        logger.info("Initializing flow handlers (Visitor, Delivery)...")
        # A dictionary of common services to pass to each flow handler
        common_services = {
            "aws_client": aws_client,
            "gpio_service": self.gpio_service,
            "tts_service": self.tts_service,
            "stt_service": self.stt_service,
            "gapi_service": self.gapi_service,
            "face_processor": self.face_processor
        }
        self.visitor_handler = VisitorFlow(**common_services)
        self.delivery_handler = DeliveryFlow(**common_services)

    def run_interaction_loop(self):
        """
        Runs the main interaction loop, asking the user for their intent
        and dispatching to the correct flow handler.
        """
        logger.info("System ready. Starting main interaction loop.")
        while True:
            try:
                self.tts_service.speak("Hello. I am Neobell. Are you here to deliver a package or to leave a message?")
                text = self.stt_service.transcribe_audio(duration_seconds=7)

                if not text:
                    self.tts_service.speak("I'm sorry, I didn't hear anything. Let's try again.")
                    time.sleep(1)
                    continue

                logger.info(f"User transcription: '{text}'")
                intent = self.gapi_service.get_initial_intent(text).value
                logger.info(f"Detected intent: '{intent}'")

                if intent == "VISITOR_MESSAGE":
                    self.visitor_handler.start_interaction()
                elif intent == "PACKAGE_DELIVERY":
                    self.delivery_handler.start_delivery_process()
                else:
                    self.tts_service.speak("I'm sorry, I didn't understand. Please say 'delivery' or 'message'.")

                logger.info("Flow finished. Returning to idle state in 5 seconds...")
                time.sleep(5)

            except KeyboardInterrupt:
                logger.info("User interrupted the loop. Shutting down.")
                break
            except Exception as e:
                logger.error("An error occurred during the interaction loop.", exc_info=True)
                self.tts_service.speak("An unexpected error occurred. Restarting interaction.")
                time.sleep(2)

def main():
    Orchestrator()
    logger.info("System has shut down.")

if __name__ == "__main__":
    main()