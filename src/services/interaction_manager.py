import logging
from src.phrases import YESNO

# Import the service classes for type hinting
# from tts_service import TTSService
# from stt_service import STTService

logger = logging.getLogger(__name__)

# Keyword Definitions for Interpretation
AFFIRMATIVE_WORDS = {"yes", "yeah", "yep", "sure", "correct", "right", "affirmative"}
NEGATIVE_WORDS = {"no", "nope", "negative", "wrong", "incorrect"}


class InteractionManager:
    def ask_question(
        self,
        question: str,
        override: bool = True,
        max_listen_duration: int = 5,
        max_attempts: int = 3,
    ) -> str | None:
        """
        Asks a generic question via TTS and returns the user's transcribed response (STT).
        Repeats up to max_attempts if no response is detected.
        Returns the formatted (lowercase, stripped) response or None if not understood.
        """
        if not question:
            logger.error("ask_question called with an empty question.")
            return None

        for attempt in range(max_attempts):
            self.tts.speak(question, override)
            logger.info(
                f"Waiting for user response for {max_listen_duration} seconds..."
            )
            transcribed_text = self.stt.transcribe_audio(
                duration_seconds=max_listen_duration
            )
            if not transcribed_text:
                logger.warning("No text was transcribed from the user's response.")
                self.tts.speak(YESNO["not_understood"])
                continue
            processed_response = transcribed_text.lower().strip()
            logger.info(f"User response transcribed as: '{processed_response}'")
            return processed_response
        logger.warning(
            "Could not get a valid response from user after multiple attempts."
        )
        self.tts.speak(YESNO["max_attempts"])
        return None

    """
    A centralized manager for handling common user interaction flows,
    like asking questions and interpreting responses. This class requires
    TTS and STT services to be injected upon initialization.
    """

    def __init__(self, tts_service, stt_service):
        """
        Initializes the InteractionManager with necessary services.

        Args:
            tts_service (TTSService): An initialized instance of the TTS service.
            stt_service (STTService): An initialized instance of the STT service.
        """
        self.tts = tts_service
        self.stt = stt_service
        logger.info("InteractionManager initialized.")

    def ask_yes_no(
        self, question: str, override: bool = True, listen_duration_seconds: int = 5
    ) -> bool | None:
        """
        Asks a user a yes/no question and interprets the answer.
        Tries up to 3 times to get a valid yes/no response (not just any response).
        All feedback is centralized in phrases.py (YESNO).
        Returns True for affirmative, False for negative or after 3 failed attempts.
        """
        for attempt in range(3):
            response = self.ask_question(
                question if attempt == 0 else YESNO["clarify"],
                override=override,
                max_listen_duration=listen_duration_seconds,
                max_attempts=2,
            )
            if not response:
                break
            response_words = set(response.split())
            is_affirmative = not response_words.isdisjoint(AFFIRMATIVE_WORDS)
            is_negative = not response_words.isdisjoint(NEGATIVE_WORDS)
            if is_affirmative and is_negative:
                logger.warning(
                    f"ask_yes_no: Conflicting responses detected: '{response}'"
                )
                self.tts.speak(YESNO["conflict"])
                continue
            if is_affirmative:
                logger.info("Affirmative answer detected.")
                self.tts.speak(YESNO["affirmative"])
                return True
            if is_negative:
                logger.info("Negative answer detected.")
                self.tts.speak(YESNO["negative"])
                return False
            logger.warning(
                f"ask_yes_no: Could not determine intent from response: '{response}'"
            )
            self.tts.speak(YESNO["not_understood"])
        logger.warning("ask_yes_no: No valid yes/no response after retries.")
        self.tts.speak(YESNO["max_attempts"])
        return None  # No response at all, treat as negative
