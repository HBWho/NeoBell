import json
import numpy as np
import sounddevice as sd
import logging
from vosk import Model, KaldiRecognizer

logger = logging.getLogger(__name__)

# --- Vosk Model Setup ---
RATE = 44100
STT_CHANNELS = 1
SD_FORMAT = 'int16'  # sounddevice equivalent of paInt16
SD_CHUNK_SIZE = 1024

class STTService:
    def __init__(self, model_path, device_id):
        self.stt_model = None
        self.model_path = model_path
        self.device_id = device_id

    def load_model(self):
        try:
            self.stt_model = Model(self.model_path)
            logger.info("Vosk STT model loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading Vosk STT model from {self.model_path}: {e}")
            self.stt_model = None

    def transcribe_audio(self, duration_seconds=7):
        if not self.stt_model:
            logger.error("STT model not available.")
            return None

        recognizer = KaldiRecognizer(self.stt_model, RATE)
        recognizer.SetWords(True)

        logger.info(f"Attempting to listen for {duration_seconds} seconds on device ID: {self.device_id} using sounddevice...")

        try:
            # Record audio with sounddevice
            recording = sd.rec(
                int(duration_seconds * RATE),
                samplerate=RATE,
                channels=STT_CHANNELS,
                dtype=SD_FORMAT,
                device=self.device_id
            )
            
            logger.info(f"Recording started on device {self.device_id}. Listening...")
            sd.wait()  # Wait until recording is finished

            # Process the audio through Vosk
            recognizer.AcceptWaveform(recording.tobytes())

        except Exception as e:
            logger.error(f"Error during sounddevice recording or processing on device {self.device_id}: {e}")
            return f"SOUNDDEVICE_ERROR_ON_DEVICE_{self.device_id}"

        final_result_json = recognizer.FinalResult()
        result_dict = json.loads(final_result_json)
        transcribed_text = result_dict.get("text", "").strip()

        if transcribed_text:
            return transcribed_text
        else:
            return None
