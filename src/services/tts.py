import subprocess
import os
import logging

logger = logging.getLogger(__name__)

class TTSService:
    """
    A service wrapper for the eSpeak NG text-to-speech engine,
    allowing for easy customization of voice, speed, and pitch.
    """
    def __init__(self, lang="pt-br", variant="m3", speed=160, pitch=50):
        """
        Initializes the TTS service.

        Args:
            lang (str): The language code (e.g., 'pt-br', 'en-us').
            variant (str): The voice variant (e.g., 'm1'-'m7' for male, 'f1'-'f5' for female).
            speed (int): Speaking speed in words per minute (default is ~160).
            pitch (int): The pitch of the voice (0-99, default is 50).
        """
        self.executable = self._find_espeak_executable()
        
        # Combines language and variant for the -v flag (e.g., "pt-br+m3")
        self.voice = f"{lang}+{variant}" if variant else lang
        self.speed = str(speed)
        self.pitch = str(pitch)
        
        logger.info(f"TTSService initialized. Voice: {self.voice}, Speed: {self.speed}, Pitch: {self.pitch}")

    def _find_espeak_executable(self) -> str:
        """Finds the espeak-ng executable or defaults to the command name."""
        if os.name == 'nt': # If on Windows
            possible_paths = [
                r"C:\Program Files\eSpeak NG\espeak-ng.exe",
                r"C:\Program Files (x86)\eSpeak NG\espeak-ng.exe"
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    return p
        # For Linux, macOS, or if not found in default Windows paths,
        # assume it's in the system's PATH.
        return "espeak-ng"

    def speak(self, text_to_say: str):
        """
        Speaks the given text using the configured voice, speed, and pitch.
        """
        if not self.executable:
            logger.error("eSpeak NG executable not found. Cannot speak.")
            return

        logger.info(f"NeoBell TTS: \"{text_to_say}\"")
        
        # Command with additional flags for better control
        command = [
            self.executable,
            "-v", self.voice,
            "-s", self.speed,  # Sets the speed
            "-p", self.pitch,  # Sets the pitch
            text_to_say
        ]
        
        try:
            # Using DEVNULL to prevent espeak-ng from printing to console on success
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            logger.error(f"ERROR TTS: Command '{self.executable}' not found. Ensure eSpeak NG is installed and in your system's PATH.")
        except subprocess.CalledProcessError as e:
            logger.error(f"ERROR TTS: eSpeak NG failed with return code {e.returncode}. Command: {' '.join(command)}")
        except Exception as e:
            logger.error(f"ERROR TTS: An unexpected error occurred: {e}")
