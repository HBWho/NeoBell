import google.generativeai as genai
from dotenv import load_dotenv
import os 

load_dotenv()

try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    print("Please ensure you have set the GOOGLE_API_KEY environment variable.")

# --- Initialize the Generative Model ---
# Choose a Gemini model. "gemini-1.5-flash-latest" is good for speed and cost-effectiveness.
# "gemini-1.5-pro-latest" is more powerful.
try:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest", # Or "gemini-1.5-pro-latest"
        system_instruction="You are a helpful assistant for residents in a building. Your role is to help with package deliveries and sending messages to residents. Keep your responses concise and clear."
    )
except Exception as e:
    print(f"Error initializing Gemini model: {e}")

# --- Conversation History (managed by you) ---
# Gemini API can support conversational context by sending previous messages.
# The `start_chat` method is good for this.
chat_session = None
if 'model' in locals(): # Only start chat if model initialized successfully
    chat_session = model.start_chat(history=[])

# Function to get response from Gemini
def get_gemini_response(user_text, relevant_data=None):
    global chat_session
    if not chat_session:
        return "Sorry, the AI model is not available at the moment."

    # Construct the prompt for Gemini
    prompt = f"User said: '{user_text}'."
    if relevant_data:
        prompt += f"\nAdditional context: {relevant_data}"
        # Example: relevant_data = {"task_type": "package_delivery", "user_has_provided_recipient_name": False}

    print(f"DEBUG: Sending to Gemini: {prompt}") # For your debugging

    try:
        # Send the message and get the response
        # The chat_session object automatically manages history if you keep using it.
        response = chat_session.send_message(prompt)
        assistant_response = response.text # Accessing the text part of the response
        return assistant_response
    except Exception as e:
        print(f"Error communicating with Gemini API: {e}")
        # Fallback or error handling (e.g., try re-initializing chat_session)
        # For instance, some errors might require starting a new chat session.
        # chat_session = model.start_chat(history=[]) # Reset chat on some errors
        return "I encountered an issue trying to understand that. Could you try again?"

transcribed_text = "I need to deliver a package for Mr. Smith."
relevant_data_for_gemini = {"task_type": "package_delivery", "recipient_hint": "Mr. Smith"}

if transcribed_text and 'model' in locals() and chat_session:
    gemini_reply = get_gemini_response(transcribed_text, relevant_data_for_gemini)
    print(f"Gemini says: {gemini_reply}")
    # Then, speak(gemini_reply) using your TTS function
