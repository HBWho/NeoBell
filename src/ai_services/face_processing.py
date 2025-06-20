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
# AUDIO_SAMPLE_RATE = 44100 # old mic
AUDIO_SAMPLE_RATE = 48000 # new mic
AUDIO_CHANNELS = 1       
AUDIO_DTYPE = 'int16'  

# --- Constants for Face Recognition ---
MODEL_NAME = "SFace"
DETECTOR = "opencv"
THRESHOLD = 0.55 # Distance threshold for a valid match

class FaceProcessing:
    def __init__(self):
        self.recording = False
        self.video_frames = []
        self.audio_frames = []
        self.recording_thread = None
        self.audio_thread = None

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

    def record_video_with_audio(self, camera_id: int, output_file: str, duration: float = 5.0):
        """
        Grava vídeo com áudio usando FFmpeg com configurações mais compatíveis.
        
        Args:
            camera_id: ID da câmera (0 para padrão)
            output_file: Nome do arquivo de saída (use .mp4)
            duration: Duração em segundos
        """
        logger.info(f"Iniciando gravação por {duration} segundos...")
        
        try:
            # Configurações de dispositivo (ajuste conforme necessário)
            video_device = f"/dev/video{camera_id}"  # Linux
            audio_device = "default"  # Linux
            
            # Comando FFmpeg otimizado para compatibilidade
            cmd = [
                'ffmpeg',
                '-y',
                '-f', 'v4l2',
                '-framerate', str(VIDEO_FPS),
                '-video_size', '640x480',
                '-i', video_device,
                '-f', 'alsa',
                '-i', audio_device,
                '-t', str(duration),
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-crf', '23',
                '-pix_fmt', 'yuv420p',  # Essencial para compatibilidade
                '-c:a', 'aac',
                '-b:a', '128k',
                '-ar', '44100',
                '-movflags', '+faststart',  # Para streaming online
                output_file
            ]
            
            # Executa o comando
            process = subprocess.run(cmd, 
                                   stderr=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   timeout=duration + 10)
            
            if process.returncode != 0:
                logger.error(f"Erro FFmpeg: {process.stderr.decode()}")
                return False
                
            logger.info(f"Vídeo criado em {output_file}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout na gravação")
            return False
        except Exception as e:
            logger.error(f"Falha na gravação: {str(e)}")
            return False

def main():
    face_processor = FaceProcessing()
    print("Inicio do video...")
    sucesso = face_processor.record_video_with_audio(
        camera_id=0, 
        output_file="video_sync.mp4", 
        duration=10.0  # grava por 10 segundos
    )
    if sucesso:
        print("Vídeo gravado com sucesso!")
    else:
        print("Falha ao gravar vídeo.")

if __name__ == "__main__":
    main()

