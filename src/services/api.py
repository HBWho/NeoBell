import google.generativeai as genai
from dotenv import load_dotenv
import os
from enum import Enum
from typing import Optional

class Intent(Enum):
    PACKAGE = "PACKAGE_DELIVERY"
    VISITOR = "VISITOR_MESSAGE"
    UNCLEAR = "UNCLEAR"
    ERROR_MODEL = "ERROR_MODEL"
    ERROR_API = "ERROR_API"

class GAPI:
    DEFAULT_SYSTEM_PROMPT = (
        "You are NeoBell, an AI assistant for a smart doorbell. "
        "Your primary task is to understand if a person at the door wants to 'deliver a package' "
        "or if they are a 'visitor' (which implies they might want to leave a message). "
        "Respond ONLY with 'PACKAGE_DELIVERY', 'VISITOR_MESSAGE', or 'UNCLEAR'."
    )

    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.gemini_model = self._initialize_gemini()

    def _initialize_gemini(self) -> Optional[genai.GenerativeModel]:
        try:
            load_dotenv()
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not set in .env")
            genai.configure(api_key=api_key)
            return genai.GenerativeModel(
                model_name="gemini-1.5-flash-latest",
                system_instruction=self.DEFAULT_SYSTEM_PROMPT
            )
        except Exception as e:
            print(f"Gemini initialization failed: {e}")
            return None

    def get_initial_intent(self, user_reply_text: str) -> Intent:
        if not self.gemini_model:
            return Intent.ERROR_MODEL
        if not isinstance(user_reply_text, str) or not user_reply_text.strip():
            return Intent.UNCLEAR

        prompt = f"""
        NeoBell asked: "How can I help you today?"
        User replied: "{user_reply_text}"
        Classify the intent.
        """
        try:
            response = self.gemini_model.generate_content(prompt)
            intent = response.text.strip().upper()
            return Intent(intent) if intent in Intent._value2member_map_ else Intent.UNCLEAR
        except Exception as e:
            if self.debug_mode:
                print(f"API Error: {e}")
            return Intent.ERROR_API
