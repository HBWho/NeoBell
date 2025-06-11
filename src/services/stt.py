from vosk import Model, KaldiRecognizer
import json
import os
import time
import sounddevice as sd
import numpy as np

class STTService:
    def __init__(self, model_path, sample_rate=16000, lang_code="en-us"):
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.lang_code = lang_code
        self.channels = 1
        self.dtype_sd = 'int16'  # sounddevice equivalent of paInt16
        self.chunk_size = 1024

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

    @staticmethod
    def list_audio_devices():
        """List all available audio input devices"""
        devices = sd.query_devices()
        print("\nAvailable Audio Devices:")
        for i, device in enumerate(devices):
            print(f"{i}: {device['name']} (Input Channels: {device['max_input_channels']})")
        return devices

    def transcribe_audio(self, duration_seconds=5, device_id=None, silence_threshold=0.3, silence_duration_needed=1.5):
        if not self.is_ready:
            print("ERROR STT: Model not loaded. Cannot transcribe.")
            return None

        recognizer = KaldiRecognizer(self.stt_model, self.sample_rate)
        recognizer.SetWords(True)

        print(f"STT: Listening... (Max: {duration_seconds}s, Device: {device_id if device_id is not None else 'Default'})")

        try:
            # Record audio with sounddevice
            recording = sd.rec(
                int(duration_seconds * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype_sd,
                device=device_id
            )
            
            print("Recording started...")
            sd.wait()  # Wait until recording is finished

            # Process the audio through Vosk
            recognizer.AcceptWaveform(recording.tobytes())

            final_result_json = recognizer.FinalResult()
            result_dict = json.loads(final_result_json)
            transcribed_text = result_dict.get("text", "").strip()

            if transcribed_text:
                print(f"STT Transcription: \"{transcribed_text}\"")
            else:
                print("STT: No clear speech detected or transcribed.")

            return transcribed_text

        except Exception as e:
            print(f"ERROR STT: During recording/transcription: {e}")
            return None

if __name__ == "__main__":
    # Example usage
    model_path = "../models/vosk-model-en-us-0.22"
    stt_service = STTService(model_path, sample_rate=16000)
    
    if stt_service.is_ready:
        # List available devices
        STTService.list_audio_devices()
        
        # Example with default device
        print("\n--- Testing with default device ---")
        result = stt_service.transcribe_audio(duration_seconds=5)
        print(f"Result: {result}")
        
        # Example with specific device (change the ID as needed)
        # print("\n--- Testing with device ID 2 ---")
        # result = stt_service.transcribe_audio(duration_seconds=5, device_id=2)
        # print(f"Result: {result}")
