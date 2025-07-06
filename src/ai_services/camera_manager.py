import cv2
import threading
import time
import logging
import subprocess

VIDEO_FPS = 20.0
logger = logging.getLogger(__name__)

class CameraManager:
    def __init__(self):
        self.stop_recording_event = threading.Event()
        self.recording_thread = None
        self.cams = {}  # camera_id: VideoCapture
        self.cam_refcounts = {}  # camera_id: refcount
        self.lock = threading.Lock()  # para garantir thread safety

    def open_camera(self, camera_id: int, width: int = 1920, height: int = 1080):
        """Opens and returns a cv2.VideoCapture object for the given camera ID. Increments refcount."""
        with self.lock:
            if camera_id in self.cams:
                # Já aberta, só aumenta o contador
                self.cam_refcounts[camera_id] += 1
                return self.cams[camera_id]
            # Abrir nova câmera
            cam = cv2.VideoCapture(camera_id)
            if not cam.isOpened():
                logger.error(f"Cannot open camera with ID {camera_id}.")
                raise RuntimeError(f"Camera {camera_id} could not be opened.")
            cam.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cams[camera_id] = cam
            self.cam_refcounts[camera_id] = 1
            return cam

    def release_camera(self, camera_id: int):
        """Decrements refcount and releases the camera object if no one else is using it."""
        with self.lock:
            if camera_id not in self.cams:
                return
            self.cam_refcounts[camera_id] -= 1
            if self.cam_refcounts[camera_id] <= 0:
                self.cams[camera_id].release()
                del self.cams[camera_id]
                del self.cam_refcounts[camera_id]

    def take_picture(self, camera_id: int, filename: str):
        """Captures a single high-resolution picture and saves it to a file."""
        cam = None
        try:
            cam = self.open_camera(camera_id)
            for i in range(10):
                result, image = cam.read()
                if not result:
                    logger.warning(f"Failed to read a warmup frame (attempt {i + 1}).")
                    break

            logger.info("Capturing final image...")
            result, image = cam.read()
            if not result:
                logger.error("Failed to capture the final image from the camera.")
                return False

            cv2.imwrite(filename, image)
            logger.info("Image successfully saved")
            return True
        finally:
            if cam is not None:
                self.release_camera(camera_id)

    def _record_video_thread(self, camera_id: int, output_file: str):
        """Thread worker for recording video frames. It runs until the stop event is set."""
        logger.info("Background video recording thread started.")
        cap = self.open_camera(camera_id)
        if not cap:
            cap = self.open_camera(camera_id)

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video_writer = cv2.VideoWriter(
            output_file, fourcc, VIDEO_FPS, (frame_width, frame_height)
        )

        frame_delay = 1.0 / VIDEO_FPS
        try:
            while not self.stop_recording_event.is_set():
                loop_start_time = time.monotonic()
                ret, frame = cap.read()
                if not ret:
                    break
                if video_writer:
                    video_writer.write(frame)

                elapsed = time.monotonic() - loop_start_time
                sleep_time = frame_delay - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
        finally:
            self.release_camera(camera_id)
            video_writer.release()
            logger.info("Background video recording thread finished.")

    def start_background_recording(self, camera_id: int, output_file: str):
        """Starts a video recording in a background thread."""
        if self.recording_thread and self.recording_thread.is_alive():
            logger.warning("A recording is already in progress.")
            return

        logger.info(
            f"Starting background recording for camera {camera_id}. Output will be saved to {output_file}."
        )
        self.stop_recording_event.clear()

        # Create and start the daemon thread
        self.recording_thread = threading.Thread(
            target=self._record_video_thread, args=(camera_id, output_file), daemon=True
        )
        self.recording_thread.start()

    def stop_background_recording(self):
        """Signals the background recording thread to stop and waits for it to finish."""
        if not self.recording_thread or not self.recording_thread.is_alive():
            logger.info("No active recording to stop.")
            return

        logger.info("Stopping background recording...")
        self.stop_recording_event.set()
        self.recording_thread.join(timeout=5)  # Wait up to 5s for the thread to finish

        if self.recording_thread.is_alive():
            logger.error("Recording thread did not stop in time.")

        logger.info("Background recording stopped and file saved.")

    def record_video_with_audio(
        self, camera_id: int, output_file: str, duration: float = 5.0
    ):
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
            audio_device = "plughw:CARD=Device,DEV=0"  # Linux

            # Comando FFmpeg otimizado para compatibilidade
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "v4l2",
                "-framerate",
                str(VIDEO_FPS),
                "-video_size",
                "640x480",
                "-i",
                video_device,
                "-f",
                "alsa",
                "-i",
                audio_device,
                "-t",
                str(duration),
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-crf",
                "23",
                "-pix_fmt",
                "yuv420p",  # Essencial para compatibilidade
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-ar",
                "44100",
                "-movflags",
                "+faststart",  # Para streaming online
                output_file,
            ]

            # Executa o comando
            process = subprocess.run(
                cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                timeout=duration + 10,
            )

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
    print("Inicio do video...")
    camera_manager = CameraManager()
    sucesso = camera_manager.record_video_with_audio(
        camera_id=0,
        output_file="video_sync.mp4",
        duration=10.0,  # grava por 10 segundos
    )
    if sucesso:
        print("Vídeo gravado com sucesso!")
    else:
        print("Falha ao gravar vídeo.")


if __name__ == "__main__":
    main()
