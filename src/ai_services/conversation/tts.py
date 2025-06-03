import subprocess 

def speak(text_to_say):
    """Converts text to speech and plays it."""
    print(f"NeoBell says: {text_to_say}")
    try:
        subprocess.run(["espeak-ng", text_to_say], check=True)
    except Exception as e:
        print(f"Error during TTS: {e}")
        print("Ensure espeak-ng is installed or your TTS is configured correctly.")
