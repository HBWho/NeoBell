import sounddevice as sd
import numpy as np

duration = 5  # seconds
samplerate = 44100  # CD quality
device_index = 2  # Device index of your webcam mic

print(sd.query_devices())

print(f"Recording from device {device_index}...")

# Record audio with 1 channel (mono)
audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, device=device_index)
sd.wait()

# Print a slice of audio data
print(f"Audio data (first 20 samples): {audio[:20]}")

# If there's no audio (all zeros), we can try troubleshooting further
if np.all(audio == 0):
    print("No audio captured! Check the microphone input.")
else:
    print("Recording complete. Playing back...")

    # Play back the recorded audio
    sd.play(audio, samplerate)
    sd.wait()

    # Optionally save to file
    import soundfile as sf
    sf.write('test_recording.wav', audio, samplerate)
    print("Audio saved as 'test_recording.wav'")

