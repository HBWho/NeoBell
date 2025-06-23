import time
import logging

logger = logging.getLogger(__name__)

# Constants for camera IDs
EXTERNAL_CAMERA = 0
INTERNAL_CAMERA = 1 

class DeliveryFlow:
    """Handles the entire package delivery workflow."""
    def __init__(self, **services):
        """Initializes the flow with all its required service dependencies."""
        self.aws = services.get("aws_client")
        self.gpio = services.get("gpio_service")
        self.tts = services.get("tts_service")
        self.ocr = services.get("ocr_processing")
        self.servo = services.get("servo_service")
        # Add other services if needed, e.g., STT, GAPI
        logger.info("Delivery Flow handler initialized.")

    def start_delivery_flow(self):
        """Main entry point for the delivery interaction flow."""
        logger.info("Starting delivery flow...")
        self.gpio.set_external_red_led(True)
        self.gpio.set_external_green_led(False)
        
        try:
            # Step 1: Scan external package QR code
            delivery_code = self._scan_external_package()
            if not delivery_code:
                self.tts.speak("I could not read the package code. Please try again later.")
                return # End flow

            # Step 2: Validate with AWS
            is_valid = self.aws.request_package_info(id_type="tracking_number", id_value=delivery_code)
            if not is_valid:
                self.tts.speak("This delivery code is not valid. Please check the package.")
                return # End flow

            # Step 3: Open compartment and guide user
            self._handle_deposit()

            # Step 4: Internal verification scan
            is_same_package = self._scan_internal_package(delivery_code)
            
            # Step 5: Final actions based on verification
            if is_same_package:
                self._finalize_delivery()
            else:
                self._reject_package()

        except Exception as e:
            logger.error("An unexpected error occurred during the delivery flow.", exc_info=True)
            self.tts.speak("An unexpected error occurred. Please try again.")
        finally:
            # Ensure hardware is in a safe, locked state
            logger.info("Ensuring all hardware is in a safe final state.")
            self.gpio.set_internal_led(False)
            # self.gpio.set_collect_lock(True)
            self.gpio.set_external_green_led(False)
            self.gpio.set_external_red_led(True)


    def _scan_external_package(self) -> str | None:
        """Asks for and scans the package's QR code from the external camera."""
        self.tts.speak("Please show the package's QR code to the camera. The photo will be taken in 5, 4, 3, 2, 1.")
        if not self.ocr.take_picture(EXTERNAL_CAMERA):
            logger.error("Failed to take picture with external camera.")
            return None
        
        codes = self.ocr.process_codes() # Processes the default temp image
        if codes:
            logger.info(f"Found delivery code: {codes[0]}")
            return codes[0] # Return the first code found
        
        logger.warning("No scannable codes found on the package.")
        return None

    def _handle_deposit(self):
        """Opens the compartment and instructs the user."""
        self.tts.speak("Delivery code accepted. Please place the package inside the compartment, with the label facing up.")
        self.gpio.set_external_red_led(False)
        self.gpio.set_external_green_led(True)
        self.gpio.set_internal_led(True)
        self.gpio.set_collect_lock(False) # Unlock the compartment
        time.sleep(7) # Give the user time to place the package
        self.gpio.set_collect_lock(True) # Lock the compartment

    def _scan_internal_package(self, original_code: str) -> bool:
        """Scans the package inside the compartment for verification."""
        self.tts.speak("Thank you. I will now verify the package inside.")
        # Here you might want to close a main door before the final hatch action
        # For now, we just scan
        
        if not self.ocr.take_picture(INTERNAL_CAMERA):
            logger.error("Failed to take picture with internal camera.")
            return False
            
        codes = self.ocr.process_codes()
        if codes and original_code in codes:
            logger.info("Internal package verification successful.")
            return True
        
        logger.warning(f"Internal scan failed. Original code '{original_code}' not found in internal scan codes: {codes}")
        return False

    def _finalize_delivery(self):
        """Handles the successful delivery confirmation and secures the package."""
        self.tts.speak("Package validated. Thank you for your delivery. The compartment will now close.")
        # self.gpio.set_collect_lock(True) # Lock the compartment
        self.gpio.set_internal_led(False)
        self.gpio.set_external_green_led(False)
        self.gpio.set_external_red_led(True)
        
        # This is the final "trapdoor" action to secure the package internally
        self.servo.open_hatch() # Open the hatch
        time.sleep(5)
        self.servo.close_hatch() # Close the hatch
        logger.info("Delivery finalized and package secured.")

    def _reject_package(self):
        """Handles a failed internal verification."""
        self.tts.speak("The package inside does not seem to match the one scanned outside. Please remove the package and close the door.")
        # Wait for user to remove package. You might add a sensor check here in the future.
        self.gpio.set_collect_lock(False) # Unlock the compartment
        time.sleep(7)
        self.gpio.set_collect_lock(True) # Lock the compartment
        logger.warning("Package rejected due to mismatch.")