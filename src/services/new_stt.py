import json
import numpy as np
import sounddevice as sd
import logging
from vosk import Model, KaldiRecognizer
import hashlib # NEW: Import for hashing
import os      # NEW: Import for creating directories
from scipy.io.wavfile import write as write_wav # NEW: Import for saving WAV files

logger = logging.getLogger(__name__)

# --- Vosk Model Setup ---
RATE = 48000
STT_CHANNELS = 1
SD_FORMAT = 'int16'
SD_CHUNK_SIZE = 1024

SILENCE_THRESHOLD = 400
SILENCE_SECONDS = 2

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

    # NEW: Added output_dir parameter
    def transcribe_audio(self, duration_seconds=7, output_dir="recordings"):
        if not self.stt_model:
            logger.error("STT model not available.")
            return None, None # NEW: Return a tuple

        recognizer = KaldiRecognizer(self.stt_model, RATE)
        recognizer.SetWords(True)

        logger.info(f"Attempting to listen with dynamic silence detection (max {duration_seconds}s) on device ID: {self.device_id}...")

        chunks_per_second = RATE / SD_CHUNK_SIZE
        silence_limit_chunks = int(SILENCE_SECONDS * chunks_per_second)
        max_chunks = int(duration_seconds * RATE / SD_CHUNK_SIZE)

        speech_started = False
        silence_counter = 0
        
        # NEW: 1. List to store all recorded audio chunks
        recorded_chunks = []

        try:
            with sd.InputStream(
                samplerate=RATE,
                channels=STT_CHANNELS,
                dtype=SD_FORMAT,
                device=self.device_id,
                blocksize=SD_CHUNK_SIZE
            ) as stream:
                
                logger.info(f"Recording started on device {self.device_id}. Listening...")
                
                for _ in range(max_chunks):
                    audio_chunk, overflowed = stream.read(SD_CHUNK_SIZE)
                    if overflowed:
                        logger.warning("Input audio stream overflowed")
                    
                    # NEW: 2. Append each chunk to our list
                    recorded_chunks.append(audio_chunk)
                    
                    if recognizer.AcceptWaveform(audio_chunk.tobytes()):
                        pass

                    amplitude = np.sqrt(np.mean(np.square(audio_chunk, dtype=np.float64)))

                    if amplitude > SILENCE_THRESHOLD:
                        if not speech_started:
                            logger.info("Speech detected.")
                            speech_started = True
                        silence_counter = 0
                    elif speech_started:
                        silence_counter += 1

                    if speech_started and silence_counter > silence_limit_chunks:
                        logger.info(f"Silence detected for {SILENCE_SECONDS} seconds. Stopping.")
                        break
                else:
                    logger.info(f"Max duration of {duration_seconds} seconds reached.")

        except Exception as e:
            logger.error(f"Error during sounddevice recording or processing on device {self.device_id}: {e}")
            return f"SOUNDDEVICE_ERROR_ON_DEVICE_{self.device_id}", None # NEW: Return a tuple

        # --- NEW: After the loop, save the recorded audio ---
        audio_hash = None
        if recorded_chunks:
            # 3. Combine all chunks into a single NumPy array
            full_audio_data = np.concatenate(recorded_chunks, axis=0)
            
            # 4. Calculate the SHA256 hash of the raw audio bytes
            hasher = hashlib.sha256()
            hasher.update(full_audio_data.tobytes())
            audio_hash = hasher.hexdigest()
            
            # 5. Save the combined audio to a .wav file
            try:
                # Ensure the output directory exists
                os.makedirs(output_dir, exist_ok=True)
                file_path = os.path.join(output_dir, f"{audio_hash}.wav")
                
                # Use scipy to write the numpy array to a wav file
                write_wav(file_path, RATE, full_audio_data)
                logger.info(f"Audio saved successfully to: {file_path}")
            except Exception as e:
                logger.error(f"Failed to save audio file: {e}")
                audio_hash = None # Reset hash if saving failed
        
        # Get the final transcription result from Vosk
        final_result_json = recognizer.FinalResult()
        result_dict = json.loads(final_result_json)
        transcribed_text = result_dict.get("text", "").strip()

        # NEW: 6. Return both the text and the hash of the audio file
        if transcribed_text:
            return transcribed_text, audio_hash
        else:
            return None, audio_hash
