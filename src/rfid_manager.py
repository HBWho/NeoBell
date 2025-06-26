import os
import serial
import time
import logging
from pathlib import Path
from config.logging_config import setup_logging

setup_logging()

from communication.aws_client import AwsIotClient
from hal.gpio import GpioManager 
from hal.pin_service import GpioService

logger = logging.getLogger(__name__)

# A função read_rfid() pode ser removida se não for utilizada
# def read_rfid():
#     """
#     Função principal para ler dados de uma porta serial (RFID do ESP32).
#     """
#     pass

class Orchestrator:
    """
    The main application class that initializes all services, handlers,
    and orchestrates the primary user interaction flow with resilient serial connection.
    """
    def __init__(self):
        """Initializes configuration. Services are initialized in __enter__."""
        logger.info("Orchestrator initializing...")
        self._load_config()
        self.aws_client = None
        self.gpio_manager = None
        self.gpio_service = None
        
        # Atributos para a conexão serial
        self.serial_port = '/dev/ttyACM0'
        self.baud_rate = 115200
        self.serial_connection = None # O objeto da conexão será armazenado aqui

    def __enter__(self):
        """Context manager entry: initializes and connects all services."""
        logger.info("Entering runtime context. Initializing services...")
        self._init_services()
        self.aws_client.connect()
        return self 

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit: ensures all resources are released."""
        logger.info("Exiting runtime context. Shutting down services...")
        self._disconnect_from_rfid() # Garante que a porta serial seja fechada ao sair
        if self.aws_client:
            self.aws_client.disconnect()
        if self.gpio_manager:
            self.gpio_manager.close()
        logger.info("All services shut down gracefully.")
        if exc_type:
            logger.error("Application exited with an exception.", exc_info=(exc_type, exc_val, exc_tb))

    def _load_config(self):
        """Loads all necessary configuration from environment variables."""
        logger.info("Loading configuration from environment variables...")
        self.sbc_id = os.getenv("CLIENT_ID")
        self.endpoint = os.getenv("AWS_IOT_ENDPOINT")
        self.port = os.getenv("PORT")
        self.cert_path = "certifications/10da83970c7ac9793d1f4c33c48f082924dc1aaccd0e8e8fd229d13b5caa210e-certificate.pem.crt"
        self.key_path = "certifications/10da83970c7ac9793d1f4c33c48f082924dc1aaccd0e8e8fd229d13b5caa210e-private.pem.key"
        self.ca_path = "certifications/AmazonRootCA1.pem"

    def _init_services(self):
        """Initializes singleton services used across the application."""
        logger.info("Initializing core services...")
        self.aws_client = AwsIotClient(self.sbc_id, self.endpoint, self.port, self.cert_path, self.key_path, self.ca_path)
        input_pins = []
        output_pins = [(4, 9), (4, 5), (4, 2), (4, 8), (1, 8), (1, 13), (4, 12)]
        self.gpio_manager = GpioManager(output_pins=output_pins, input_pins=input_pins)
        self.gpio_service = GpioService(gpio_manager=self.gpio_manager)

    def _connect_to_rfid(self):
        """Tries to connect to the serial port in a loop until successful."""
        while self.serial_connection is None:
            # Verifica se o dispositivo existe no sistema operacional antes de tentar conectar
            if not os.path.exists(self.serial_port):
                logger.warning(f"Device {self.serial_port} not found. Waiting for it to appear...")
                time.sleep(3)
                continue
            
            try:
                logger.info(f"Attempting to connect to RFID reader on {self.serial_port}...")
                ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
                self.serial_connection = ser
                logger.info("RFID reader connected successfully!")
                self.serial_connection.flushInput()
            except serial.SerialException as e:
                logger.error(f"Failed to connect to {self.serial_port}: {e}. Retrying in 3 seconds...")
                self.serial_connection = None # Garante que a conexão continue nula
                time.sleep(3)

    def _disconnect_from_rfid(self):
        """Safely closes the serial connection if it exists."""
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.close()
                logger.info("Serial connection closed.")
            except Exception as e:
                logger.error(f"Error while closing serial port: {e}")
        self.serial_connection = None

    def run_interaction_loop(self):
        """
        Runs the main interaction loop, with logic to handle disconnects and reconnects.
        """
        logger.info("System ready.")
        
        while True:
            # Passo 1: Se não estiver conectado, tenta conectar
            if self.serial_connection is None:
                self._connect_to_rfid()
            
            # Passo 2: Tenta ler da porta serial. Se falhar, o loop recomeça
            try:
                line = self.serial_connection.readline()

                if not line:
                    continue # Timeout, sem dados recebidos, apenas continua

                uid_string = line.decode('utf-8', errors='ignore').strip()
                if "Leitor RFID pronto" in uid_string or not uid_string:
                    continue
                
                logger.info(f"--- TAG READ: {uid_string} ---")
                formatted_uid = uid_string.lower().replace(' ', ':')
                validation_response = self.aws_client.verify_nfc_tag(formatted_uid)

                if validation_response and validation_response.get('is_valid') is True:
                    logger.info(f"Tag {formatted_uid} is VALID. Activating lock...")
                    # Este é o ponto crítico que causa a desconexão
                    self.gpio_service.set_collect_lock(True) 
                    time.sleep(5)
                    self.gpio_service.set_collect_lock(False)
                    logger.info("Door sequence complete.")
                else:
                    reason = validation_response.get('reason', 'No reason provided.') if validation_response else 'No response from server.'
                    logger.warning(f"Tag {formatted_uid} is INVALID. Reason: {reason}")
            
            except serial.SerialException as e:
                # Passo 3: A MÁGICA ACONTECE AQUI!
                logger.error(f"Connection to RFID reader lost: {e}. Cleaning up and attempting to reconnect.")
                self._disconnect_from_rfid() # Limpa a conexão antiga
                # O `continue` fará o `while True` rodar novamente.
                # Como self.serial_connection agora é None, ele cairá no `_connect_to_rfid()`
                continue
            except Exception as e:
                logger.critical(f"A non-serial error occurred: {e}", exc_info=True)
                self._disconnect_from_rfid() # Desconecta por segurança
                time.sleep(5) # Espera um pouco antes de tentar de novo

def main():
    """The main entry point of the application."""
    setup_logging()
    logger.info("Application starting up...")
    try:
        with Orchestrator() as app:
            app.run_interaction_loop()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user (Ctrl+C).")
    except Exception as e:
        logger.critical("A fatal error occurred, forcing application to exit.", exc_info=True)
    finally:
        logger.info("System has shut down.")

if __name__ == "__main__":
    main()
