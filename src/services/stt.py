import logging
import datetime
import whisper
import speech_recognition as sr  # Novo: Importa speech_recognition


# --- Configuração do Logger ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger("speech_recognition").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

# --- Constantes de Áudio e STT ---
SAMPLE_RATE = 48000
# SAMPLE_RATE = 96000

# --- Parâmetros de Detecção de Silêncio ---
PAUSE_THRESHOLD = 1.2
SILENCE_THRESHOLD = 100  # Limiar de energia para detecção de silêncio


class STTService:
    def __init__(self, model_name: str = "base", device_id: int | None = None):
        """
        Inicializa o serviço de Speech-to-Text usando speech_recognition + Whisper.
        """
        self.model_name = model_name
        self.device_id = device_id
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = (
            SILENCE_THRESHOLD  # Define o limiar de energia para detecção de silêncio
        )
        self.recorder.pause_threshold = PAUSE_THRESHOLD
        self.recorder.dynamic_energy_threshold = False
        self.audio_model = whisper.load_model(
            model_name
        )  # Carrega o modelo Whisper corretamente
        logger.info(
            f"STTService inicializado com modelo '{model_name}' e dispositivo ID '{device_id}'"
        )

    def transcribe_audio(self, duration_seconds: int = 15) -> str | None:
        """
        Grava o áudio do microfone usando speech_recognition, detecta silêncio automaticamente e retorna a transcrição usando Whisper.
        Salva o áudio capturado em um arquivo .wav.
        """
        output_filename = "audio_neobell.wav"
        try:
            with sr.Microphone(device_index=self.device_id, sample_rate=SAMPLE_RATE, chunk_size=512) as source:
                logger.info("Ajustando para o ruído ambiente...")
                # self.recorder.adjust_for_ambient_noise(source, duration=1) #* Check if this line is needed
                logger.info(f"Gravando... (máx {duration_seconds}s ou até silêncio)")
                audio = self.recorder.listen(
                    source, timeout=duration_seconds, phrase_time_limit=duration_seconds
                )
            # Salva o áudio capturado
            with open(output_filename, "wb") as f:
                f.write(audio.get_wav_data(convert_rate=SAMPLE_RATE))
            logger.info(f"Áudio gravado com sucesso em '{output_filename}'")
        except Exception as e:
            logger.error(f"Erro ao capturar áudio do microfone: {e}")
            return None
        # --- Transcrição com Whisper ---
        try:
            logger.info("Transcrevendo áudio com Whisper...")
            result = self.audio_model.transcribe(output_filename, language="en")
            transcribed_text = result["text"].strip()
            logger.info(f"Texto transcrito: '{transcribed_text}'")
            return transcribed_text if transcribed_text else None
        except Exception as e:
            logger.error(f"Erro ao transcrever áudio com Whisper: {e}")
            return None


# --- Bloco de Execução Principal ---
if __name__ == "__main__":

    def list_audio_devices():
        print("Dispositivos de áudio disponíveis:")
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            print(
                'Microphone with name "{1}" found for `Microphone(device_index={0})`'.format(
                    index, name
                )
            )

    list_audio_devices()
    print("-" * 50)

    # Configure os parâmetros aqui.
    MODEL_NAME = "tiny"  # Whisper model: tiny, base, small, medium, large
    MICROPHONE_ID = 0

    try:
        stt = STTService(model_name=MODEL_NAME, device_id=MICROPHONE_ID)
        if stt.audio_model:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_file = f"gravacao_completa_{timestamp}.wav"
            print(
                f"\nPor favor, fale no microfone... A gravação completa será salva em '{output_file}'"
            )
            transcription = stt.transcribe_audio()
            if transcription:
                print(f"\nResultado Final: {transcription}")
            else:
                print(
                    "\nNenhum texto foi transcrito. Ocorreu um erro ou nada foi dito."
                )
        else:
            print(
                "\nNão foi possível iniciar o serviço STT. Verifique o modelo e os logs de erro."
            )
    except Exception as e:
        logger.error(f"Ocorreu um erro ao inicializar ou executar o serviço: {e}")

