# stt_efficient_gravando_tudo.py

import json
import numpy as np
import sounddevice as sd
import logging
from vosk import Model, KaldiRecognizer
import queue
import datetime
from scipy.io import wavfile

# --- Configuração do Logger ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# --- Constantes de Áudio e STT ---
SAMPLE_RATE = 48000
CHANNELS = 1
DTYPE = 'int16'
BLOCK_SIZE = 800

# --- Parâmetros de Detecção de Silêncio ---
SILENCE_THRESHOLD = 300
SILENCE_SECONDS = 2


class STTService:
    def __init__(self, model_path: str, device_id: int | None = None):
        """
        Inicializa o serviço de Speech-to-Text.
        """
        self.model_path = model_path
        self.device_id = device_id
        self.model = self._load_model()
        self.recognizer = None
        self.audio_queue = queue.Queue()

    def _load_model(self) -> Model | None:
        """Carrega o modelo Vosk do caminho especificado."""
        try:
            model = Model(self.model_path)
            logger.info(f"Modelo Vosk '{self.model_path}' carregado com sucesso.")
            return model
        except Exception as e:
            logger.error(f"Erro ao carregar o modelo Vosk de {self.model_path}: {e}")
            return None

    def _audio_callback(self, indata, frames, time, status):
        """Este callback é chamado pelo sounddevice para cada novo bloco de áudio."""
        if status:
            logger.warning(f"Status do stream de áudio: {status}")
        self.audio_queue.put(indata.copy())

    def transcribe_audio(self, duration_seconds: int = 15) -> str | None:
        """
        Grava o áudio do dispositivo, detecta o silêncio para parar, e retorna a transcrição.
        Salva todo o áudio capturado em um arquivo .wav.
        """
        if not self.model:
            logger.error("Modelo STT não disponível. Transcrição cancelada.")
            return None
        output_filename = "audio_neobell.wav"
        self.recognizer = KaldiRecognizer(self.model, SAMPLE_RATE)
        self.recognizer.SetWords(True)

        logger.info(
            f"Iniciando escuta no dispositivo ID: {self.device_id or 'Padrão'}... "
            f"(Limite de {duration_seconds}s, silêncio após {SILENCE_SECONDS}s)"
        )

        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()

        # --- Lógica de Gravação e Detecção ---
        chunks_per_second = SAMPLE_RATE / BLOCK_SIZE
        silence_limit_chunks = int(SILENCE_SECONDS * chunks_per_second)
        max_chunks = int(duration_seconds * SAMPLE_RATE / BLOCK_SIZE)

        speech_started = False
        silence_counter = 0
        recorded_chunks_total = 0
        
        # Lista para armazenar todos os blocos de áudio.
        recorded_audio_data = []

        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                device=self.device_id,
                blocksize=BLOCK_SIZE,
                callback=self._audio_callback
            ):
                while recorded_chunks_total < max_chunks:
                    try:
                        audio_chunk = self.audio_queue.get(timeout=0.1)
                        recorded_chunks_total += 1
                    except queue.Empty:
                        continue

                    ### ALTERADO ###: Adiciona o chunk à lista de gravação incondicionalmente.
                    # Todo o áudio, desde o início, será salvo.
                    if output_filename:
                        recorded_audio_data.append(audio_chunk)

                    # Alimenta o reconhecedor Vosk
                    self.recognizer.AcceptWaveform(audio_chunk.tobytes())

                    # --- Lógica de Detecção de Silêncio (apenas para parar a gravação) ---
                    amplitude = np.sqrt(np.mean(np.square(audio_chunk, dtype=np.float64)))
                    is_speech = amplitude > SILENCE_THRESHOLD

                    if is_speech:
                        if not speech_started:
                            logger.info("Fala detectada.")
                            speech_started = True
                        silence_counter = 0
                    elif speech_started:
                        silence_counter += 1

                    # Se o limite de silêncio for atingido, para a gravação.
                    if speech_started and silence_counter > silence_limit_chunks:
                        logger.info(f"Silêncio detectado por {SILENCE_SECONDS}s. Parando.")
                        break
                else:
                    logger.info(f"Duração máxima de {duration_seconds}s atingida.")

        except Exception as e:
            logger.error(f"Erro durante a gravação ou processamento: {e}")
            return None

        # --- Lógica para Salvar o Arquivo de Áudio ---
        if output_filename and recorded_audio_data:
            try:
                logger.info(f"Concatenando {len(recorded_audio_data)} blocos de áudio...")
                full_audio = np.concatenate(recorded_audio_data, axis=0)
                wavfile.write(output_filename, SAMPLE_RATE, full_audio)
                logger.info(f"Áudio gravado com sucesso em '{output_filename}'")
            except Exception as e:
                logger.error(f"Erro ao salvar o arquivo de áudio '{output_filename}': {e}")
        
        # --- Obtenção do Resultado Final ---
        final_result_json = self.recognizer.FinalResult()
        result_dict = json.loads(final_result_json)
        transcribed_text = result_dict.get("text", "").strip()

        logger.info(f"Texto transcrito: '{transcribed_text}'")

        return transcribed_text if transcribed_text else None

# --- Bloco de Execução Principal ---
if __name__ == '__main__':
    def list_audio_devices():
        """Lista todos os dispositivos de áudio disponíveis."""
        print("Dispositivos de áudio disponíveis:")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            try:
                device_name = device['name']
            except Exception:
                device_name = "Nome indisponível"
            
            if device.get('max_input_channels', 0) > 0:
                print(f"  ID: {i}, Nome: '{device_name}' (Entrada)")

    list_audio_devices()
    print("-" * 50)

    # Configure os parâmetros aqui.
    MODEL_PATH = "vosk-model-small-pt-0.3" 
    MICROPHONE_ID = None 

    try:
        stt = STTService(model_path=MODEL_PATH, device_id=MICROPHONE_ID)
        if stt.model:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_file = f"gravacao_completa_{timestamp}.wav"
            
            print(f"\nPor favor, fale no microfone... A gravação completa será salva em '{output_file}'")
            
            transcription = stt.transcribe_audio()
            
            if transcription:
                print(f"\nResultado Final: {transcription}")
            else:
                print("\nNenhum texto foi transcrito. Ocorreu um erro ou nada foi dito.")
        else:
            print("\nNão foi possível iniciar o serviço STT. Verifique o caminho do modelo e os logs de erro.")

    except Exception as e:
        logger.error(f"Ocorreu um erro ao inicializar ou executar o serviço: {e}")
