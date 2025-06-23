import time
import logging

logger = logging.getLogger(__name__)

# Constants for camera IDs
EXTERNAL_CAMERA = 0
INTERNAL_CAMERA = 0

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
            # Step 1 & 2: Scan external package and validate all codes found
            validated_codes = self._scan_and_validate_external_package()
            if not validated_codes:
                self.tts.speak("I could not find a valid delivery code on this package. Please try again later.")
                return

            # Step 3: Open compartment
            self._handle_deposit()

            # Step 4: Internal verification scan
            is_same_package = self._scan_internal_package(validated_codes)
            
            # Step 5: Final actions
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

    def _scan_and_validate_external_package(self) -> list[str] | None:
        """
        Asks for and scans the package's codes, validates each one with AWS,
        and returns a list of all valid codes.
        """
        self.tts.speak("Please show the package's QR code to the camera. The photo will be taken in 3, 2, 1.")
        if not self.ocr.take_picture(EXTERNAL_CAMERA):
            logger.error("Failed to take picture with external camera.")
            return None
        
        all_found_codes = self.ocr.process_codes()
        if not all_found_codes:
            logger.warning("No scannable codes found on the package.")
            return None

        logger.info(f"Found {len(all_found_codes)} codes: {all_found_codes}. Validating with backend...")
        
        validated_codes = []
        for code in all_found_codes:
            if self.aws.request_package_info(identifier_type="tracking_number", identifier_value=code):
                logger.info(f"Code '{code}' is VALID.")
                validated_codes.append(code)
            else:
                logger.info(f"Code '{code}' is invalid.")

        if not validated_codes:
            logger.warning("None of the found codes were valid.")
            return None
            
        return validated_codes

    def _scan_internal_package(self, original_valid_codes: list[str]) -> bool:
        """
        Scans the package inside the compartment and checks if any of the new codes
        match any of the original valid codes.
        """
        self.tts.speak("Thank you. I will now verify the package inside.")
        
        if not self.ocr.take_picture(INTERNAL_CAMERA):
            logger.error("Failed to take picture with internal camera.")
            return False
            
        internal_codes = self.ocr.process_codes()
        if not internal_codes:
            logger.warning("Could not find any codes in the internal scan.")
            return False

        logger.info(f"Internal scan found codes: {internal_codes}")
        
        # Use sets for an efficient check for any common element
        if set(original_valid_codes) & set(internal_codes):
            logger.info("Internal package verification successful. A matching code was found.")
            return True
        
        logger.warning(f"Internal scan failed. No match between original codes {original_valid_codes} and internal codes {internal_codes}.")
        return False

    def _handle_deposit(self):
        """Opens the compartment and instructs the user."""
        self.tts.speak("Delivery code accepted. Please place the package inside the compartment, with the label facing up.")
        self.gpio.set_external_red_led(False)
        self.gpio.set_external_green_led(True)
        self.gpio.set_internal_led(True)
        self.gpio.set_collect_lock(False) # Unlock the compartment
        time.sleep(7) # Give the user time to place the package
        self.gpio.set_collect_lock(True) # Lock the compartment

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
