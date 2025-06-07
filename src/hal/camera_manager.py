import cv2
import time
import os

class CameraManager:
    def __init__(self, camera_id=0, default_width=640, default_height=480, default_fps=15):
        self.camera_id = camera_id
        self.default_width = default_width
        self.default_height = default_height
        self.default_fps = default_fps
        self.video_writer = None
        self.is_recording = False
        self.output_path = None
        self.tts_service = None # To be injected for prompts
        print(f"CameraManager initialized for camera_id: {self.camera_id}")

    def set_tts_service(self, tts_service):
        self.tts_service = tts_service

    def _speak(self, text):
        if self.tts_service:
            self.tts_service.speak(text)
        else:
            print(f"CAM TTS (fallback): {text}")

    def capture_still_frame(self):
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            print(f"ERROR CAM: Could not open camera {self.camera_id}")
            return None
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.default_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.default_height)
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            print("CAM: Frame captured successfully.")
            return frame
        else:
            print("ERROR CAM: Failed to capture frame.")
            return None

    def start_video_recording(self, output_dir, filename_prefix="visitor_message", duration_seconds=10, 
                              silence_timeout_seconds=3, stt_service_for_silence=None):
        self._speak(f"Recording will start in 3 seconds and last for up to {duration_seconds} seconds.")
        for i in range(3, 0, -1):
            self._speak(str(i))
            time.sleep(1)
        self._speak("Recording now.")

        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            self._speak("I couldn't access the camera to record.")
            print(f"ERROR CAM: Could not open camera {self.camera_id} for recording.")
            return None

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.default_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.default_height)
        actual_fps = cap.get(cv2.CAP_PROP_FPS)
        if actual_fps == 0: # If camera doesn't report FPS, use default
            actual_fps = self.default_fps
        
        fourcc = cv2.VideoWriter_fourcc(*'XVID') # Or 'MP4V' for .mp4, ensure codecs are available
        self.output_path = os.path.join(output_dir, f"{filename_prefix}_{int(time.time())}.avi")
        
        self.video_writer = cv2.VideoWriter(
            self.output_path, fourcc, actual_fps,
            (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        )

        if not self.video_writer.isOpened():
            self._speak("Sorry, I encountered an error starting the video recorder.")
            print(f"ERROR CAM: Could not open VideoWriter for {self.output_path}")
            cap.release()
            return None

        print(f"CAM: Recording video to {self.output_path} (FPS: {actual_fps:.2f})")
        self.is_recording = True
        start_time = time.time()
        last_sound_time = start_time # For silence detection

        # Basic silence detection needs audio input, which is complex to integrate here directly
        # For now, we'll rely on max duration.
        # A more advanced version would run STT in a separate thread on audio chunks from the mic
        # while video is being recorded.

        while self.is_recording and (time.time() - start_time < duration_seconds):
            ret, frame = cap.read()
            if not ret:
                print("ERROR CAM: Lost video stream during recording.")
                break
            self.video_writer.write(frame)
            
            # Placeholder for silence detection logic (would require STT integration here)
            # if stt_service_for_silence:
            #     # ... get audio chunk, process with STT ...
            #     if sound_detected: last_sound_time = time.time()
            #     if time.time() - last_sound_time > silence_timeout_seconds:
            #         self._speak("Stopping recording due to silence.")
            #         break
            
            # Allow stopping with 'q' during testing if a window is shown elsewhere
            # key = cv2.waitKey(1) & 0xFF 
            # if key == ord('q'):
            #     break
            time.sleep(1/actual_fps) # Try to match camera FPS for sleep

        self.stop_video_recording(cap) # Pass cap to release it
        return self.output_path

    def stop_video_recording(self, camera_capture_instance=None):
        if self.is_recording:
            print(f"CAM: Stopping video recording. Finalizing {self.output_path}")
            self.is_recording = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        if camera_capture_instance and camera_capture_instance.isOpened():
            camera_capture_instance.release()
        
        if self.output_path and os.path.exists(self.output_path):
            return self.output_path
        return None
