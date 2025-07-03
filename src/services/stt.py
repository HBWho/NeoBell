import json
import numpy as np
import sounddevice as sd
import logging
from vosk import Model, KaldiRecognizer

logger = logging.getLogger(__name__)

# --- Vosk Model Setup ---
# RATE = 44100 # old mic
RATE = 48000 # new mic
STT_CHANNELS = 1
SD_FORMAT = 'int16'      # sounddevice equivalent of paInt16
SD_CHUNK_SIZE = 1024

# THRESHOLD: Lower values make it more sensitive to speech, higher values make it less sensitive. Good range: 100 - 300
SILENCE_THRESHOLD = 250
SILENCE_SECONDS = 2      # How many seconds of silence to wait for before stopping

class STTService:
    def __init__(self, model_path, device_id):
        self.stt_model = None
        self.model_path = model_path
        self.device_id = device_id
        self.load_model()

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

        logger.info(f"Attempting to listen with dynamic silence detection (max {duration_seconds}s) on device ID: {self.device_id}...")

        # --- Calculate constants for the recording loop ---
        chunks_per_second = RATE / SD_CHUNK_SIZE
        silence_limit_chunks = int(SILENCE_SECONDS * chunks_per_second)
        max_chunks = int(duration_seconds * RATE / SD_CHUNK_SIZE)

        speech_started = False
        silence_counter = 0

        try:
            # Use an InputStream to process audio in real-time chunks
            with sd.InputStream(
                samplerate=RATE,
                channels=STT_CHANNELS,
                dtype=SD_FORMAT,
                device=self.device_id,
                blocksize=SD_CHUNK_SIZE
            ) as stream:
                
                logger.info(f"Recording started on device {self.device_id}. Listening...")
                
                # Loop for a maximum duration
                for _ in range(max_chunks):
                    audio_chunk, overflowed = stream.read(SD_CHUNK_SIZE)
                    if overflowed:
                        logger.warning("Input audio stream overflowed")
                    
                    # Feed the audio chunk to the Vosk recognizer
                    if recognizer.AcceptWaveform(audio_chunk.tobytes()):
                        pass
                        # partial_result = json.loads(recognizer.PartialResult())
                        # logger.debug(f"Partial text: {partial_result.get('partial', '')}")

                    # --- Silence detection logic ---
                    # Calculate the volume (Root Mean Square) of the chunk
                    amplitude = np.sqrt(np.mean(np.square(audio_chunk, dtype=np.float64)))

                    if amplitude > SILENCE_THRESHOLD:
                        if not speech_started:
                            logger.info("Speech detected.")
                            speech_started = True
                        silence_counter = 0
                    elif speech_started:
                        # Increment silence counter only if speech has already started
                        silence_counter += 1

                    # If silence limit is reached after speech, stop recording
                    if speech_started and silence_counter > silence_limit_chunks:
                        logger.info(f"Silence detected for {SILENCE_SECONDS} seconds. Stopping.")
                        break
                else:
                    # This block runs if the loop completes without breaking (max time reached)
                    logger.info(f"Max duration of {duration_seconds} seconds reached.")

        except Exception as e:
            logger.error(f"Error during sounddevice recording or processing on device {self.device_id}: {e}")
            return f"SOUNDDEVICE_ERROR_ON_DEVICE_{self.device_id}"

        # Get the final transcription result from Vosk
        final_result_json = recognizer.FinalResult()
        result_dict = json.loads(final_result_json)
        transcribed_text = result_dict.get("text", "").strip()

        if transcribed_text:
            return transcribed_text
        else:
            return None