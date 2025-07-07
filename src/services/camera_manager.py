import cv2
import threading
import time
import logging
import subprocess
import sounddevice as sd

VIDEO_FPS = 20.0
MICROPHONE_NAME = "USB PnP Sound Device"
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
            logger.info(f"Camera resource allocated")
            return cam

    def release_camera(self, camera_id: int):
        """Decrements refcount and releases the camera object if no one else is using it."""
        with self.lock:
            if camera_id not in self.cams:
                return
            self.cam_refcounts[camera_id] -= 1
            if self.cam_refcounts[camera_id] <= 0:
                logger.info(f"Camera resource released")
                self.cams[camera_id].release()
                del self.cams[camera_id]
                del self.cam_refcounts[camera_id]

    def take_picture(self, camera_id: int, filename: str):
        """Captures a single high-resolution picture and saves it to a file."""
        cam = None # Initialize to None
        try:
            cam = self.open_camera(camera_id)

            for i in range(10):
                result, _ = cam.read()
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
        Grava vídeo com áudio usando FFmpeg, selecionando o microfone dinamicamente.
        """
        logger.info(f"Iniciando gravação por {duration} segundos...")

        try:
            # --- SELEÇÃO DINÂMICA DO MICROFONE ---
            audio_device = self._get_ffmpeg_alsa_device_name(MICROPHONE_NAME)
            if not audio_device:
                logger.error("Microfone alvo não encontrado. Verifique o nome e se está conectado. Abortando gravação.")
                return False
            
            # Dispositivo de vídeo (pode precisar de ajuste se não for /dev/video{X})
            video_device = f"/dev/video{camera_id}"

            # Comando FFmpeg usando o nome do dispositivo de áudio encontrado
            cmd = [
                "ffmpeg",
                "-y",
                "-f", "v4l2",
                "-input_format", "mjpeg",
                "-framerate", str(VIDEO_FPS), # Supondo que VIDEO_FPS é uma constante definida
                "-video_size", "1920x1080",
                "-i", video_device,
                "-thread_queue_size", "1024",
                "-f", "alsa",
                "-i", audio_device,
                "-t", str(duration),
                "-c:v", "libx264",
                "-af", "afftdn",
                "-preset", "ultrafast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "128k",
                "-ar", "48000",
                "-movflags", "+faststart",
                output_file,
            ]

            # Executa o comando
            process = subprocess.run(
                cmd,
                capture_output=True, # capture_output é mais simples que definir stdout/stderr separadamente
                text=True,           # Decodifica stdout/stderr automaticamente
                timeout=duration + 10,
            )

            if process.returncode != 0:
                logger.error(f"Erro FFmpeg:\nSTDOUT:\n{process.stdout}\nSTDERR:\n{process.stderr}")
                return False

            logger.info(f"Vídeo criado em {output_file}")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Timeout na gravação")
            return False
        except Exception as e:
            logger.error(f"Falha na gravação: {str(e)}")
            return False
        
    def _get_ffmpeg_alsa_device_name(self, device_name_substring: str) -> str | None:
        """
        Encontra um dispositivo de áudio de entrada e retorna seu nome no formato ALSA
        para ser usado com o FFmpeg (ex: 'plughw:1,0').

        Args:
            device_name_substring: Parte do nome do dispositivo desejado (ex: "Webcam").

        Returns:
            O nome do dispositivo no formato ALSA ou None se não for encontrado.
        """
        try:
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                # Procura por um dispositivo de ENTRADA que contenha o nome
                is_input = device.get("max_input_channels", 0) > 0
                name_matches = (
                    device_name_substring.lower() in device.get("name", "").lower()
                )

                if is_input and name_matches:
                    alsa_name = f"plughw:{i},0"
                    logger.info(
                        f"Dispositivo encontrado: '{device['name']}' (índice {i}). Usando nome ALSA: '{alsa_name}'"
                    )
                    return alsa_name

        except Exception:
            logger.error("Não foi possível consultar os dispositivos de áudio.", exc_info=True)
            return None

        logger.warning(f"Não foi possível encontrar um dispositivo de entrada com o nome '{device_name_substring}'.")
        return None


def main():
    print("Inicio do video...")
    camera_manager = CameraManager()
    sucesso = camera_manager.record_video_with_audio(
        camera_id=2,
        output_file="video_sync.mp4",
        duration=10.0,  # grava por 10 segundos
    )
    if sucesso:
        print("Vídeo gravado com sucesso!")
    else:
        print("Falha ao gravar vídeo.")
    # sucesso = camera_manager.take_picture(
    #         camera_id=2,
    #         filename="test.jpeg"
    #         )
    # if sucesso:
    #     print("Foto tirada com sucesso!")
    # else:
    #     print("Falha ao tirar a foto.")

if __name__ == "__main__":
    main()
