import os
import time
import threading
import wave
import logging
import subprocess
from pathlib import Path

import cv2
import sounddevice as sd
import numpy as np
import ffmpeg
import pandas as pd
from deepface import DeepFace

logger = logging.getLogger(__name__)

# --- Constants for Media Processing ---
TEMP_VIDEO_ONLY = "temp_video_only.avi"
TEMP_AUDIO = "temp_audio.wav"
VIDEO_FPS = 20.0 
AUDIO_SAMPLE_RATE = 44100 
AUDIO_CHANNELS = 1       
AUDIO_DTYPE = 'int16'  

# --- Constants for Face Recognition ---
MODEL_NAME = "SFace"
DETECTOR = "opencv"
THRESHOLD = 0.55 # Distance threshold for a valid match

def save_audio_frames(audio_frames):
    if not audio_frames:
        logger.error("No audio frames were captured. Cannot save audio file.")
        return False
        
    try:
        logger.info(f"Saving {len(audio_frames)} audio frames to WAV file.")
        with wave.open(TEMP_AUDIO, 'wb') as wf:
            wf.setnchannels(AUDIO_CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(AUDIO_SAMPLE_RATE)
            wf.writeframes(b''.join(audio_frames))
        return True
    except Exception as e:
        logger.error(f"Failed to save audio file: {str(e)}", exc_info=True)
        return False

class FaceProcessing:
    """
    Handles media processing tasks, including synchronized audio/video recording
    and face recognition using DeepFace.
    """
    def __init__(self):
        # An event to signal recording threads to stop
        self.stop_recording_event = threading.Event()
        self.shared_start_time = None  # Tempo de referência compartilhado
        self.video_writer = None
        self.audio_frames = []
        self.frame_timestamps = []  # Armazena timestamps de cada frame
    # --- Video and Audio Recording Methods ---
    def _record_video_thread(self, camera_id: int, duration: int):
        """Thread de gravação de vídeo com timestamp preciso."""
        logger.info("Video recording thread started.")
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            logger.error(f"Cannot open camera with ID {camera_id}.")
            return

        frame_delay = 1.0 / VIDEO_FPS
        start_time = time.monotonic()
        
        try:
            while not self.stop_recording_event.is_set():
                frame_start = time.monotonic()
                
                # Verifica tempo total
                elapsed = frame_start - start_time
                if elapsed >= duration:
                    break
                
                ret, frame = cap.read()
                if not ret:
                    logger.error("Could not read frame from camera.")
                    break
                
                # Grava frame com timestamp
                self.video_writer.write(frame)
                self.frame_timestamps.append(time.monotonic())
                
                # Controle preciso do FPS
                processing_time = time.monotonic() - frame_start
                sleep_time = max(0, frame_delay - processing_time)
                time.sleep(sleep_time)
                
        finally:
            cap.release()
            logger.info(f"Video thread finished. Frames captured: {len(self.frame_timestamps)}")

    def _record_audio_thread(self, audio_device_id: int | None, duration: int):
        """Thread de gravação de áudio com timestamp preciso."""
        logger.info("Audio recording thread started.")
        start_time = time.monotonic()
        stream = None

        def audio_callback(indata, frames, time_info, status):
            current_time = time.monotonic()
            self.audio_frames.append((indata.copy(), current_time))
            if status:
                logger.warning(f"Audio status: {status}")

        try:
            stream = sd.InputStream(
                samplerate=AUDIO_SAMPLE_RATE,
                channels=AUDIO_CHANNELS,
                dtype=AUDIO_DTYPE,
                callback=audio_callback,
                device=audio_device_id
            )
            stream.start()
            
            while not self.stop_recording_event.is_set():
                elapsed = time.monotonic() - start_time
                if elapsed >= duration:
                    break
                time.sleep(0.05)  # Loop mais rápido para resposta rápida ao stop
                
        except Exception as e:
            logger.error(f"Audio recording error: {str(e)}", exc_info=True)
        finally:
            if stream:
                stream.stop()
                stream.close()
            logger.info(f"Audio thread finished. Samples: {len(self.audio_frames)}")

    def _calculate_sync_offset(self):
        """Calcula o offset de sincronização entre áudio e vídeo."""
        if not self.frame_timestamps or not self.audio_frames:
            return 0
        
        # Pega os primeiros timestamps válidos
        first_video_ts = self.frame_timestamps[0]
        first_audio_ts = self.audio_frames[0][1]
        
        return first_audio_ts - first_video_ts

    def _adjust_audio_sync(self, offset):
        """Ajusta o áudio com base no offset calculado."""
        if not offset:
            return b''.join([frame[0] for frame in self.audio_frames])
        
        # Calcula quantas amostras precisam ser cortadas ou adicionadas
        samples_to_trim = int(offset * AUDIO_SAMPLE_RATE)
        
        if samples_to_trim > 0:
            # Áudio começou depois - corta o início
            total_samples = sum(len(frame[0]) for frame in self.audio_frames)
            if samples_to_trim < total_samples:
                audio_data = b''.join([frame[0] for frame in self.audio_frames])
                return audio_data[samples_to_trim*2:]  # 2 bytes por sample (int16)
        else:
            # Áudio começou antes - adiciona silêncio
            silence = np.zeros((-samples_to_trim, AUDIO_CHANNELS), dtype=AUDIO_DTYPE)
            audio_data = silence.tobytes() + b''.join([frame[0] for frame in self.audio_frames])
            return audio_data
            
        return b''.join([frame[0] for frame in self.audio_frames])

    def _merge_audio_video(self, final_output_path: str):
        """Mescla áudio e vídeo com sincronização precisa usando FFmpeg."""
        logger.info("Merging with precise sync...")
        
        try:
            # Versão corrigida do comando FFmpeg
            (
                ffmpeg
                .input(TEMP_VIDEO_ONLY)
                .output(
                    ffmpeg.input(TEMP_AUDIO),
                    final_output_path,
                    vcodec='libx264',
                    acodec='aac',
                    pix_fmt='yuv420p',
                    fps_mode='vfr',  # Substitui o vsync deprecated
                    **{
                        'filter_complex': [
                            '[0:v]setpts=PTS-STARTPTS[vid]',
                            '[1:a]asetpts=PTS-STARTPTS[aud]'
                        ],
                        'map': '[vid]',
                        'map': '[aud]',
                        'shortest': None,  # Termina quando o stream mais curto acabar
                        'y': None  # Sobrescrever arquivo sem perguntar
                    }
                )
                .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
            )
            logger.info("Merge completed successfully")
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else "Unknown FFmpeg error"
            logger.error(f"FFmpeg merge failed: {error_msg}")
            
            # Debug adicional - verificar durações
            video_info = ffmpeg.probe(TEMP_VIDEO_ONLY)
            audio_info = ffmpeg.probe(TEMP_AUDIO)
            logger.debug(f"Video duration: {video_info['format']['duration']}")
            logger.debug(f"Audio duration: {audio_info['format']['duration']}")
            
            raise RuntimeError(f"Failed to merge audio/video: {error_msg}") 

    def record_video_with_audio(self, final_output_path: str, duration: int, camera_id: int, audio_device_id: int | None):
        """Gravação sincronizada com tratamento preciso de tempo."""
        # Reset de variáveis
        self.stop_recording_event.clear()
        self.audio_frames = []
        self.frame_timestamps = []
        
        # Configuração do vídeo
        cap = cv2.VideoCapture(camera_id)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        # Cria VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(TEMP_VIDEO_ONLY, fourcc, VIDEO_FPS, (frame_width, frame_height))
        
        # Inicia threads com delay mínimo entre elas
        video_thread = threading.Thread(target=self._record_video_thread, args=(camera_id, duration))
        audio_thread = threading.Thread(target=self._record_audio_thread, args=(audio_device_id, duration))
        
        # Sincroniza o início
        start_time = time.monotonic() + 0.1  # Pequeno delay para garantir readiness
        video_thread.start()
        time.sleep(0.02)  # Delay mínimo entre inícios
        audio_thread.start()
        
        # Espera exata
        while time.monotonic() - start_time < duration:
            time.sleep(0.01)
        
        # Finalização
        self.stop_recording_event.set()
        video_thread.join(timeout=2.0)
        audio_thread.join(timeout=2.0)
        self.video_writer.release()
        
        # Mescla com sincronização
        self._merge_audio_video(final_output_path)
        
        # Limpeza
        Path(TEMP_VIDEO_ONLY).unlink(missing_ok=True)
        Path(TEMP_AUDIO).unlink(missing_ok=True)
        
        return final_output_path 

    # --- Face Recognition Methods ---

    def take_picture(self, camera_id: int, filename: str):
        """Captures a single high-resolution picture and saves it to a file."""
        cam = cv2.VideoCapture(camera_id)
        try:
            cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            result, image = cam.read()
            if not result:
                raise ValueError("Failed to capture image from camera")
            cv2.imwrite(filename, image)
            logger.info(f"Picture saved to {filename}")
        finally:
            cam.release()

    def process_results(self, dfs: list) -> tuple[bool, str | None]:
        """
        Processes DeepFace results to find the best match based on distance threshold.
        Returns: A tuple containing (True, best_match_user_id) or (False, None).
        """
        results = []
        for df in dfs:
            df = df[df['distance'] < THRESHOLD]
            if not df.empty:
                # The 'person' is the user_id, extracted from the parent directory name
                df['person'] = df['identity'].apply(lambda x: Path(x).parent.name)
                results.append(df[['person', 'distance']])
        
        if not results:
            logger.warning("No matches found below the distance threshold.")
            return False, None
        
        all_results = pd.concat(results)
        best_match_idx = all_results['distance'].idxmin()
        best_match_user_id = str(all_results.loc[best_match_idx, 'person'])
        best_match_distance = float(all_results.loc[best_match_idx, 'distance'])

        logger.info(f"Best Match Found: User ID {best_match_user_id} (Distance: {best_match_distance:.3f})")
        return True, best_match_user_id

    def recognize_face(self, camera_id: int, db_path: str) -> tuple[bool, str | None]:
        """
        Captures a picture and recognizes a face against a known database.
        Returns: A tuple containing (True, user_id) on success, or (False, None).
        """
        logger.info(f"Recognizing face against database: {db_path}")
        temp_image_path = "temp_image_recognition.jpg"
        try:
            self.take_picture(camera_id, temp_image_path)
            logger.info("Analyzing face with DeepFace...")
            dfs = DeepFace.find(
                img_path=temp_image_path, 
                db_path=db_path,
                model_name=MODEL_NAME,
                detector_backend=DETECTOR,
                enforce_detection=True,
                distance_metric='cosine'
            )
            return self.process_results(dfs)
        except ValueError as e:
            logger.warning(f"No face detected in the image: {e}")
            return False, None
        except Exception as e:
            logger.error("An unexpected error occurred during face recognition.", exc_info=True)
            return False, None
        finally:
            Path(temp_image_path).unlink(missing_ok=True)


# --- Standalone Test Block ---
if __name__ == "__main__":
    
    def pre_flight_audio_check(device_id_str: str) -> bool:
        """Runs a quick 'arecord' test to check if the audio device is usable."""
        logger.info(f"--- Running pre-flight audio check on device {device_id_str} ---")
        command = [
            "arecord",
            "-D", device_id_str,
            "-f", "S16_LE",
            "-r", str(AUDIO_SAMPLE_RATE),
            "-c", str(AUDIO_CHANNELS),
            "-d", "2",
            "/dev/null"
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            logger.info(f"✅ Pre-flight audio check successful. Device '{device_id_str}' is responsive.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error("❌ Pre-flight audio check FAILED.")
            logger.error(f"Command failed: {' '.join(command)}")
            logger.error(f"Error output:\n{e.stderr}")
            return False
        except FileNotFoundError:
            logger.error("`arecord` command not found. Please ensure `alsa-utils` is installed (`sudo apt-get install alsa-utils`).")
            return False

    def test_threaded_video_recording():
        """Dedicated test function for threaded audio/video recording."""
        TEST_DURATION = 10
        OUTPUT_FILENAME = "test_video.mp4"
        CAMERA_ID = 0
        AUDIO_DEVICE_ID = 2 

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        if not pre_flight_audio_check(f"hw:{AUDIO_DEVICE_ID},0"):
            print("\nThe preliminary audio test failed. Please check 'alsamixer' settings and the errors above.")
            print("Cannot proceed with the full recording test.")
            return

        print(f"\n--- STARTING THREADED RECORDING TEST ---")
        processor = FaceProcessing()
        try:
            final_path = processor.record_video_with_audio(
                final_output_path=OUTPUT_FILENAME,
                duration=TEST_DURATION,
                camera_id=CAMERA_ID,
                audio_device_id=AUDIO_DEVICE_ID
            )
            print(f"\n✅ TEST COMPLETE! Video saved to: {os.path.abspath(final_path)}")
        except ffmpeg.Error as e:
            print(f"\n❌ FFMPEG FAILED DURING MERGE:")
            logger.error("FFmpeg error details:\n" + e.stderr.decode())
        except Exception as e:
            print(f"\n❌ AN UNEXPECTED ERROR OCCURRED:")
            logger.error("The threaded recording test failed.", exc_info=True)

    # Run the test
    test_threaded_video_recording()
