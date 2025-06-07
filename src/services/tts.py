import subprocess
import os

class TTSService:
    def __init__(self, engine_path=None, lang="en"):
        self.engine_path = engine_path
        self.lang_code = lang # For espeak-ng -v option
        if not engine_path:
            if os.name == 'nt':
                possible_paths = [r"C:\Program Files\eSpeak NG\espeak-ng.exe", r"C:\Program Files (x86)\eSpeak NG\espeak-ng.exe"]
                for p in possible_paths:
                    if os.path.exists(p):
                        self.engine_path = p
                        break
        self.executable = self.engine_path if self.engine_path else "espeak-ng"
        print(f"TTSService initialized. Engine: {self.executable}, Lang: {self.lang_code}")

    def speak(self, text_to_say):
        print(f"NeoBell TTS: \"{text_to_say}\"")
        command = [self.executable, f"-v{self.lang_code}", text_to_say]
        try:
            # Using DEVNULL for stdout/stderr to keep console clean unless error
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            print(f"ERROR TTS: Command '{command[0]}' not found. Ensure eSpeak NG is installed and in PATH, or engine_path is set.")
        except subprocess.CalledProcessError as e:
            # In case of error, we might want to see stderr
            # For now, just a generic message. To debug, remove DEVNULL for stderr.
            print(f"ERROR TTS: eSpeak NG failed. Return code: {e.returncode}")
        except Exception as e:
            print(f"ERROR TTS: An unexpected error occurred: {e}")
