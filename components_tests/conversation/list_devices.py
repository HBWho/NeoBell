
from vosk import Model, KaldiRecognizer
import json
import numpy as np
import sounddevice as sd

# --- Vosk Model Setup ---
VOSK_MODEL_PATH = "models/vosk-model-small-en-us-0.15" 
# VOSK_MODEL_PATH = "models/vosk-model-en-us-0.22" 
RATE = 44100
STT_CHANNELS = 1
SD_FORMAT = 'int16'  # sounddevice equivalent of paInt16
SD_CHUNK_SIZE = 1024

# --- List Available Audio Devices ---
def list_audio_devices():
    devices = sd.query_devices()
    print("\nAvailable Audio Devices:")
    for i, device in enumerate(devices):
        print(f"{i}: {device['name']} (Input Channels: {device['max_input_channels']})")
    return devices

stt_model = None
try:
    stt_model = Model(VOSK_MODEL_PATH)
    print("Vosk STT model loaded successfully.")
except Exception as e:
    print(f"Error loading Vosk STT model from {VOSK_MODEL_PATH}: {e}")
    stt_model = None

def record_with_sounddevice_and_transcribe(duration_seconds=7, device_id_to_test=None):
    if not stt_model:
        print("STT model not available.")
        return None

    recognizer = KaldiRecognizer(stt_model, RATE)
    recognizer.SetWords(True)

    print(f"Attempting to listen for {duration_seconds} seconds on device ID: {device_id_to_test} using sounddevice...")

    try:
        # Record audio with sounddevice
        recording = sd.rec(
            int(duration_seconds * RATE),
            samplerate=RATE,
            channels=STT_CHANNELS,
            dtype=SD_FORMAT,
            device=device_id_to_test
        )
        
        print(f"Recording started on device {device_id_to_test}. Listening...")
        sd.wait()  # Wait until recording is finished

        # Process the audio through Vosk
        recognizer.AcceptWaveform(recording.tobytes())

    except Exception as e:
        print(f"Error during sounddevice recording or processing on device {device_id_to_test}: {e}")
        return f"SOUNDDEVICE_ERROR_ON_DEVICE_{device_id_to_test}"

    final_result_json = recognizer.FinalResult()
    result_dict = json.loads(final_result_json)
    transcribed_text = result_dict.get("text", "").strip()

    if transcribed_text:
        return transcribed_text
    else:
        return None

if __name__ == "__main__":
    # List available devices and let user choose
    devices = list_audio_devices()
