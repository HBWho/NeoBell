import time
import os
import logging

logger = logging.getLogger(__name__)

# Constants for camera IDs
EXTERNAL_CAMERA = 0
INTERNAL_CAMERA = 2

class DeliveryFlow:
    """Handles the entire package delivery workflow."""
    def __init__(self, **services):
        """Initializes the flow with all its required service dependencies."""
        self.aws = services.get("aws_client")
        self.gpio = services.get("gpio_service")
        self.tts = services.get("tts_service")
        self.ocr = services.get("ocr_processing")
        self.servo = services.get("servo_service")
        self.face_proc = services.get("face_processor")
        logger.info("Delivery Flow handler initialized.")

    def start_delivery_flow(self):
        """Main entry point for the delivery interaction flow with a retry loop."""
        logger.info("Starting delivery flow...")
        self.gpio.set_external_red_led(True)
        self.gpio.set_external_green_led(False)
        
        MAX_ATTEMPTS = 5 # Allow for 2 total attempts
        validated_codes = None

        try:
            for attempt in range(MAX_ATTEMPTS):
                logger.info(f"Starting package scan, attempt {attempt + 1}/{MAX_ATTEMPTS}...")
                validated_codes = self._scan_and_validate_external_package()
                
                if validated_codes:
                    logger.info("Valid package code found. Proceeding with delivery.")
                    break # Exit the retry loop on success
                
                logger.warning("External scan and validation failed.")
                if attempt < MAX_ATTEMPTS - 1:
                    self.tts.speak("I could not validate this package. Please try again, positioning the code in front of the camera.")
                else:
                    self.tts.speak("I could not validate a delivery code after several attempts. Aborting.")
            
            if not validated_codes:
                return # End the entire flow if all attempts fail

            # If we get here, it means the external scan was successful.
            # The rest of the flow continues as before.
            self._handle_deposit()
            is_same_package = self._scan_internal_package(validated_codes)
            
            if is_same_package:
                self._finalize_delivery()
            else:
                self._reject_package()

        except Exception as e:
            logger.error("An unexpected error occurred during the delivery flow.", exc_info=True)
            self.tts.speak("An unexpected error occurred. Please try again.")
        finally:
            # Final hardware safety cleanup
            logger.info("Ensuring all hardware is in a safe final state.")
            self.gpio.set_internal_led(False)
            self.gpio.set_external_green_led(False)
            self.gpio.set_external_red_led(True)

    def _scan_and_validate_external_package(self) -> list[str] | None:
        """
        Asks for and scans the package's codes, validates each one with AWS,
        and returns a list of all valid codes.
        """
        self.gpio.set_camera_led(True)
        self.tts.speak("Please show the package's QR code to the camera. I am going to take 5 photos. The photos will be taken in 3, 2, 1.")

        max_photos = 2
        valid = False
        for i in range(max_photos):
            logger.info(f"Taking internal photo attempt {i + 1}/{max_photos}...")

            if not self.ocr.take_picture(EXTERNAL_CAMERA):
                logger.error("Failed to take picture with external camera.")
                time.sleep(0.5)
                continue

            all_found_codes = self.ocr.process_codes()
            if not all_found_codes:
                logger.warning("No scannable codes found on the package.")
                continue

            logger.info(f"External scan attempt {i + 1} found codes: {all_found_codes}")
            validated_codes = []
            for code in all_found_codes:
                response = self.aws.request_package_info("tracking_number", code)

                # Check 1: Did we get a response?
                # Check 2: Is 'package_found' True?
                # Check 3: Is the nested 'status' equal to 'pending'?
                if response and response.get('package_found') is True:
                    details = response.get('details', {})
                    if details.get('status') == 'pending':
                        logger.info(f"Code '{code}' is VALID and package status is 'pending'.")
                        validated_codes.append(code)
                        valid = True
                    else:
                        status = details.get('status', 'unknown')
                        logger.warning(f"Package for code '{code}' was found, but its status is '{status}', not 'pending'.")
                        self.tts.speak(f"This package cannot be delivered, its status is {status}.")
                else:
                    logger.warning(f"Package for code '{code}' was not found in the system.")
            
            if not validated_codes:
                logger.error("No valid packages with 'pending' status were found after checking all codes.")
                continue
            else:
                break
        
        self.gpio.set_camera_led(False)
        self.tts.speak("Process finished!")
        if valid == True:
            return validated_codes

        return None

    def _scan_internal_package(self, original_valid_codes: list[str]) -> bool:
        """
        Scans the package inside the compartment using a burst of photos
        to increase reliability.
        """
        self.tts.speak("Thank you. I will now verify the package inside.")
        logger.info("Performing internal package scan...")

        # Give the camera sensor time to adjust to the light
        time.sleep(1)

        max_photos = 5
        for i in range(max_photos):
            logger.info(f"Taking internal photo attempt {i + 1}/{max_photos}...")
            if not self.ocr.take_picture(INTERNAL_CAMERA):
                logger.error("Failed to take picture with internal camera.")
                time.sleep(0.5) # Wait a bit before retrying
                continue
            
            internal_codes = self.ocr.process_codes() # Processes the default temp image
            if not internal_codes:
                logger.warning("No codes found in this photo.")
                continue

            logger.info(f"Internal scan attempt {i + 1} found codes: {internal_codes}")
            
            # Use sets for an efficient check for any common element
            if set(original_valid_codes) & set(internal_codes):
                logger.info("Internal package verification successful. A matching code was found.")
                # self.aws.update_package_status(internal_codes, "delivered")
                return True
        
        logger.error(f"Internal scan failed after {max_photos} attempts. No match found.")
        return False

    def _handle_deposit(self):
        """Opens the compartment and instructs the user."""
        self.tts.speak("Delivery code accepted. Please place the package inside the compartment, with the label facing up.")
        self.gpio.set_external_red_led(False)
        self.gpio.set_external_green_led(True)
        self.gpio.set_internal_led(True)
        self.gpio.set_external_lock(True) # Unlock the compartment
        time.sleep(7) # Give the user time to place the package
        self.gpio.set_external_lock(False) # Lock the compartment
        self.gpio.set_external_green_led(False)
        self.gpio.set_external_red_led(True)

    def _finalize_delivery(self):
        """Handles the successful delivery confirmation and secures the package."""
        self.tts.speak("Package validated. Thank you for your delivery.")
        self.aws.submit_log(
            event_type="package_detected", 
            summary="Package delivered", 
            details={}
        )
        self.gpio.set_internal_led(True)
        self.gpio.set_external_green_led(False)
        self.gpio.set_external_red_led(True)

        video_filename = f"delivery_capture_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
        video_filepath = os.path.join("data", "captures", video_filename)
        os.makedirs(os.path.dirname(video_filepath), exist_ok=True)

        try:
            # 1. Start recording in the background using the internal camera
            self.face_proc.start_background_recording(INTERNAL_CAMERA, video_filepath)
            
            # Give it a brief moment to initialize the camera
            time.sleep(1)

            # 2. Execute the blocking action: closing the hatch
            self.servo.openHatch() # Open the hatch
            time.sleep(5)
            self.servo.closeHatch() # Close the hatch
            
        except Exception as e:
            logger.error("An error occurred during the finalization sequence.", exc_info=True)
        finally:
            # 3. No matter what, stop the recording
            self.face_proc.stop_background_recording()
            
            # Turn off the internal light after recording is done
            self.gpio.set_internal_led(False)

        logger.info(f"Delivery finalized and package secured. Capture saved to {video_filepath}")

    def _reject_package(self):
        """Handles a failed internal verification."""
        self.tts.speak("The package inside does not seem to match the one scanned outside. Please remove the package and close the door.")
        # Wait for user to remove package. You might add a sensor check here in the future.
        self.gpio.set_external_green_led(True)
        self.gpio.set_external_red_led(False)
        self.gpio.set_external_lock(True) # Unlock the compartment
        time.sleep(7)
        self.gpio.set_external_lock(False) # Lock the compartment
        self.gpio.set_external_green_led(False)
        self.gpio.set_external_red_led(True)
        logger.warning("Package rejected due to mismatch.")
