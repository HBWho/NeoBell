import pyaudio
from vosk import Model, KaldiRecognizer
import json
import os
import time

class STTService:
    def __init__(self, model_path, sample_rate=16000, lang_code="en-us"): # lang_code not directly used by Vosk model path but good for context
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.lang_code = lang_code
        self.channels = 1
        self.dtype_pa = pyaudio.paInt16
        self.chunk_size = 1024 # Adjusted for potentially better partial results

        self.stt_model = None
        self.is_ready = False
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Vosk model not found at {self.model_path}")
            self.stt_model = Model(self.model_path)
            self.is_ready = True
            print(f"STTService initialized. Vosk model loaded from: {self.model_path}")
        except FileNotFoundError as e:
            print(f"ERROR STT: {e}")
        except Exception as e:
            print(f"ERROR STT: Could not load Vosk model: {e} (model path: {self.model_path})")

    def transcribe_audio(self, duration_seconds=5, device_id=None, silence_threshold=0.3, silence_duration_needed=1.5):
        if not self.is_ready:
            print("ERROR STT: Model not loaded. Cannot transcribe.")
            return None

        recognizer = KaldiRecognizer(self.stt_model, self.sample_rate)
        recognizer.SetWords(True)

        audio_interface = pyaudio.PyAudio()
        stream = None
        transcribed_text = None
        frames_for_processing = []

        print(f"STT: Listening... (Max: {duration_seconds}s, Device: {device_id if device_id is not None else 'Default'})")
        try:
            stream = audio_interface.open(
                format=self.dtype_pa,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_id,
                frames_per_buffer=self.chunk_size
            )
            
            start_time = time.time()
            last_speech_time = start_time
            
            while time.time() - start_time < duration_seconds:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                frames_for_processing.append(data) # Store for potential reprocessing if needed
                
                if recognizer.AcceptWaveform(data):
                    partial_result = json.loads(recognizer.Result())
                    if partial_result.get("text"):
                        last_speech_time = time.time() # Reset silence timer on speech
                        # print(f"STT Partial: {partial_result['text']}") # Can be noisy
                else:
                    # Check for silence only if some speech was detected recently
                    if time.time() - last_speech_time > silence_duration_needed:
                        print("STT: Silence detected, stopping early.")
                        break
                
                # Check for keyboard interrupt to stop listening (for testing)
                # In a real app, this would be handled by the main loop
                # if msvcrt.kbhit() and msvcrt.getch() == b'\x1b': # ESC key (Windows example)
                #     print("STT: Stop requested.")
                #     break
            
            final_result_json = recognizer.FinalResult()
            result_dict = json.loads(final_result_json)
            transcribed_text = result_dict.get("text", "").strip()

            if transcribed_text:
                print(f"STT Transcription: \"{transcribed_text}\"")
            else:
                print("STT: No clear speech detected or transcribed.")
                
        except Exception as e:
            print(f"ERROR STT: During recording/transcription: {e}")
            return None
        finally:
            if stream:
                stream.stop_stream()
                stream.close()
            if audio_interface:
                audio_interface.terminate()
        
        return transcribed_text