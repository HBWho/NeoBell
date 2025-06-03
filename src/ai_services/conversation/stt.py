import pyaudio
from vosk import Model, KaldiRecognizer
import json
import wave # Only if you want to save the file too

# --- Vosk Model Setup ---
VOSK_MODEL_PATH = "models/vosk-model-small-en-us-0.15" # Ensure this path is correct
STT_SAMPLE_RATE = 16000
STT_CHANNELS = 1
# PyAudio format mapping
PYAUDIO_FORMAT = pyaudio.paInt16 # For 'int16'
PYAUDIO_CHUNK_SIZE = 1024 # A common chunk size

stt_model = None
try:
    stt_model = Model(VOSK_MODEL_PATH)
    print("Vosk STT model loaded successfully.")
except Exception as e:
    print(f"Error loading Vosk STT model from {VOSK_MODEL_PATH}: {e}")
    stt_model = None

def record_with_pyaudio_and_transcribe(duration_seconds=7, device_id_to_test=None):
    if not stt_model:
        print("STT model not available.")
        return None

    recognizer = KaldiRecognizer(stt_model, STT_SAMPLE_RATE)
    recognizer.SetWords(True)

    audio = pyaudio.PyAudio()
    stream = None

    print(f"Attempting to listen for {duration_seconds} seconds on device ID: {device_id_to_test} using PyAudio...")

    try:
        stream = audio.open(format=PYAUDIO_FORMAT,
                            channels=STT_CHANNELS,
                            rate=STT_SAMPLE_RATE,
                            input=True,
                            input_device_index=device_id_to_test,
                            frames_per_buffer=PYAUDIO_CHUNK_SIZE)
        
        print(f"PyAudio stream opened successfully on device {device_id_to_test}. Listening...")
        
        for i in range(0, int(STT_SAMPLE_RATE / PYAUDIO_CHUNK_SIZE * duration_seconds)):
            data = stream.read(PYAUDIO_CHUNK_SIZE)
            recognizer.AcceptWaveform(data)

            partial = recognizer.PartialResult()
            print(f"Partial: {json.loads(partial).get('partial', '')}")

    except Exception as e:
        print(f"Error during PyAudio recording or processing on device {device_id_to_test}: {e}")
        return f"PYAUDIO_ERROR_ON_DEVICE_{device_id_to_test}"

    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        if audio:
            audio.terminate()

    final_result_json = recognizer.FinalResult()
    result_dict = json.loads(final_result_json)
    transcribed_text = result_dict.get("text", "").strip()

    if transcribed_text:
        return transcribed_text
    else:
        return None

if __name__ == "__main__":
    TARGET_DEVICE_ID_PYAUDIO = 1

    if not stt_model:
        print("STT Model not loaded, cannot run PyAudio with Vosk test.")
    else:
        print(f"\n--- Testing PyAudio with Vosk: HyperX DirectSound (Device ID: {TARGET_DEVICE_ID_PYAUDIO}) ---")
        result = record_with_pyaudio_and_transcribe(duration_seconds=5, device_id_to_test=TARGET_DEVICE_ID_PYAUDIO)
        print(f"Text: {result}")
        print("-" * 30)
