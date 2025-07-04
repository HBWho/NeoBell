import os
import hashlib
import logging
import threading
import queue
from typing import Optional, Union
from gtts import gTTS
from playsound import playsound

# --- Basic configuration ---
logger = logging.getLogger(__name__)
CACHE_DIR = os.path.join("data", "audios")

# Define a type for items in the queue for clarity
QueueItem = Union[str, tuple[str, threading.Event]]

class TTSService:
    """
    A service that uses gTTS with a local cache to provide high-quality speech.
    It uses a thread-safe queue to manage speech requests sequentially
    and features an override mechanism for high-priority messages.
    """
    def __init__(self, lang="en"):
        """
        Initializes the TTS service and starts a background worker thread.
        """
        self.lang = lang
        self._speech_queue = queue.Queue()
        self._lock = threading.Lock()
        
        # This flag will be used to signal the worker to stop playing.
        self._interrupt_event = threading.Event()

        # The worker thread processes items from the queue.
        self._worker_thread = threading.Thread(target=self._tts_worker)
        self._worker_thread.daemon = True
        self._worker_thread.start()
        
        # Ensure the cache directory exists
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        logger.info(f"TTSService initialized with gTTS. Language: {self.lang}")

    def _tts_worker(self):
        """
        The worker function that runs in a background thread. It gets text
        from the queue, generates audio using the caching mechanism, and plays it.
        """
        while True:
            item: QueueItem = self._speech_queue.get()
            
            # Reset the interrupt flag for the new item
            self._interrupt_event.clear()
            
            started_event: Optional[threading.Event] = None
            done_event: Optional[threading.Event] = None
            if isinstance(item, tuple):
                # Suporte para (texto, done_event) ou (texto, started_event, done_event)
                if len(item) == 2:
                    text, done_event = item
                elif len(item) == 3:
                    text, started_event, done_event = item
            else:
                text = item

            # --- Caching and Playback Logic ---
            text_hash = hashlib.md5(text.encode()).hexdigest()
            filepath = os.path.join(CACHE_DIR, f"{text_hash}.mp3")

            # Check if the file is already in our cache
            if not os.path.exists(filepath):
                logger.info(f"CACHE MISS: Generating new audio for '{text}'.")
                try:
                    tts = gTTS(text=text, lang=self.lang, slow=False)
                    tts.save(filepath)
                except Exception as e:
                    logger.error(f"Failed to call gTTS API: {e}")
                    if done_event:
                        done_event.set()
                    self._speech_queue.task_done()
                    continue # Skip to the next item
            else:
                logger.info(f"CACHE HIT: Playing '{text}' from file.")

            # Play the audio file.
            # NOTE: playsound is blocking, so the queue will wait here.
            # The override functionality works by clearing the queue of upcoming
            # items, but it cannot interrupt a sound that has already started.
            try:
                # Sinaliza o início da fala (caso seja async com started_event)
                if started_event:
                    started_event.set()
                # We check the interrupt event before playing.
                if not self._interrupt_event.is_set():
                    playsound(filepath)
            except Exception as e:
                logger.error(f"Error playing sound file {filepath}: {e}")
            finally:
                # If this was a synchronous call, signal its completion
                if done_event:
                    done_event.set()
                self._speech_queue.task_done()

    def _clear_speech_queue(self):
        """Clears all upcoming speech requests from the queue."""
        with self._lock:
            while not self._speech_queue.empty():
                try:
                    item = self._speech_queue.get_nowait()
                    # If the discarded item was a synchronous call, unblock it
                    if isinstance(item, tuple):
                        item[1].set()
                except queue.Empty:
                    break
        
        # Set the interrupt flag to prevent the current item from playing if it hasn't started.
        self._interrupt_event.set()
        logger.warning("Speech queue cleared.")


    def speak(self, text_to_say: str, override: bool = False):
        """
        Speaks the given text and blocks until the speech is complete.
        This method is synchronous.
        """
        if not text_to_say:
            return

        if override:
            self._clear_speech_queue()

        # Create an event that will signal when this specific phrase is done
        done_event = threading.Event()
        self._speech_queue.put((text_to_say, done_event))
        
        # Wait here until the worker thread signals that this text is finished
        done_event.wait()

    def speak_async(self, text_to_say: str, override: bool = False):
        """
        Adds text to the speech queue and returns after the speech starts playing.
        This method is asynchronous, but waits until its audio starts.
        """
        if not text_to_say:
            return

        logger.info(f"Queueing async TTS: '{text_to_say}' (Override: {override})")
        
        if override:
            self._clear_speech_queue()
        
        # Cria um evento para sinalizar o início da fala
        started_event = threading.Event()
        # Adiciona na fila uma tupla (texto, started_event, None)
        self._speech_queue.put((text_to_say, started_event, None))
        # Aguarda até que o worker sinalize o início da fala
        started_event.wait()

    def wait_for_completion(self):
        """Blocks until all queued speech tasks are completed."""
        logger.info("Waiting for TTS queue to complete...")
        self._speech_queue.join()
        logger.info("TTS queue is empty.")
