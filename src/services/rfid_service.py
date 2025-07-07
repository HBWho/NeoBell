import serial
import time
import logging
import threading

logger = logging.getLogger(__name__)

class RfidListenerService:
    """
    A background service that listens for RFID tags from a serial port (e.g., ESP32),
    validates them, and triggers actions like opening a lock.
    """
    def __init__(self, aws_client, gpio_service, port='/dev/ttyACM0', baud_rate=115200):
        """
        Initializes the RFID listener service.

        Args:
            aws_client: The client for validating tags with AWS.
            gpio_service: The service for controlling hardware pins (locks).
            port (str): The serial port name.
            baud_rate (int): The serial communication speed.
        """
        self.aws_client = aws_client
        self.gpio_service = gpio_service
        self.serial_port = port
        self.baud_rate = baud_rate
        
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run_listener_loop, daemon=True)
        logger.info(f"RfidListenerService initialized for port {self.serial_port}")

    def start(self):
        """Starts the background listening thread."""
        if not self._thread.is_alive():
            logger.info("Starting RFID listener thread...")
            self._thread.start()

    def stop(self):
        """Stops the background listening thread gracefully."""
        logger.info("Stopping RFID listener thread...")
        self._stop_event.set()
        # Wait for the thread to finish, with a timeout
        self._thread.join(timeout=2)
        if self._thread.is_alive():
            logger.warning("RFID listener thread did not stop in time.")

    def _run_listener_loop(self):
        """The main loop that runs in the background thread."""
        while not self._stop_event.is_set():
            try:
                logger.info(f"Attempting to connect to serial port {self.serial_port}...")
                with serial.Serial(self.serial_port, self.baud_rate, timeout=1) as ser:
                    logger.info("Toggling DTR to reset ESP32...")
                    ser.dtr = False
                    time.sleep(0.1)
                    ser.dtr = True
                    time.sleep(0.5)

                    logger.info("Serial connection successful! Waiting for RFID tags...")
                    ser.reset_input_buffer()
                    
                    while not self._stop_event.is_set():
                        if ser.in_waiting > 0:
                            line = ser.readline()
                            if line:
                                self._process_rfid_tag(line, ser)
                        
                        time.sleep(0.1)

            except serial.SerialException as e:
                logger.warning(f"Serial port error: {e}. Retrying in 5 seconds...")
                time.sleep(5)
            except Exception as e:
                logger.error("An unexpected error occurred in the RFID listener loop.", exc_info=True)
                time.sleep(5)
        
        logger.info("RFID listener loop has finished.")

    def _process_rfid_tag(self, line: bytes, serial_connection: serial.Serial):
        """
        Decodes a raw tag, formats it to a standard format (lowercase, colon-separated),
        validates it, and acts upon the result.
        """
        try:
            # Decode the raw bytes from serial into a string and strip whitespace
            raw_uid = line.decode('utf-8', errors='ignore').strip()
            
            # Ignore empty lines or initial messages from the ESP32
            if not raw_uid or "Leitor RFID pronto" in raw_uid:
                return

            # --- NEW FORMATTING LOGIC IS HERE ---
            # 1. Convert the entire string to lowercase (e.g., "CD 01..." -> "cd 01...")
            # 2. Replace all space characters with colons (e.g., "cd 01..." -> "cd:01:39:03")
            formatted_uid = raw_uid.lower().replace(' ', ':')
            # --- END OF FORMATTING LOGIC ---

            logger.info(f"--- RFID TAG READ: '{raw_uid}' -> Formatted to: '{formatted_uid}' ---")
            
            logger.info(f"Validating tag '{formatted_uid}' with backend...")
            # Use the newly formatted UID for all subsequent operations
            validation_response = self.aws_client.verify_nfc_tag(formatted_uid)
            
            if validation_response and validation_response.get('is_valid') is True:
                user_id = validation_response.get("user_id_associated")
                logger.info(f"Tag {formatted_uid} is VALID for user_id {user_id}. Opening collection door for 5 seconds.")
                
                # The action sequence
                self.gpio_service.set_collect_lock(True) # Unlock
                time.sleep(5)
                self.gpio_service.set_collect_lock(False) # Lock

                logger.info("Clearing serial buffer and pausing for 2 seconds to prevent duplicate reads...")
                # 1. Limpa qualquer leitura que tenha chegado durante o processamento
                serial_connection.reset_input_buffer()
                # 2. Pausa para criar um período de "cooldown"
                time.sleep(2)
                
                logger.info("Collection door sequence complete.")
            else:
                reason = validation_response.get('reason', 'unknown') if validation_response else 'timeout'
                logger.warning(f"Tag {formatted_uid} is INVALID or validation failed. Reason: {reason}")

        except Exception as e:
            logger.error("Failed to process RFID tag.", exc_info=True) 
