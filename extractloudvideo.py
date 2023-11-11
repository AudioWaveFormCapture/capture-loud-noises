import sounddevice as sd
import numpy as np
import datetime

# Set the parameters for audio recording
sample_rate = 44100  # Sample rate in Hz
duration = 5  # Duration of each audio clip in seconds
threshold = 0.1  # Adjust this threshold as needed

# Initialize variables
recording = False

def audio_callback(indata, frames, time, status):
    global recording

    # Calculate the root mean square (RMS) of the audio data
    rms = np.sqrt(np.mean(indata**2))

    # Check if the RMS exceeds the threshold to start recording
    if rms > threshold and not recording:
        recording = True
        print("Recording started at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        # You can add code here to save the test audio clip with a unique name

    # Check if the RMS falls below the threshold to stop recording
    if rms <= threshold and recording:
        recording = False
        print("Recording stopped at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        # You can add code here to save the recorded audio clip with a unique name

# Start streaming audio from the microphone
with sd.InputStream(callback=audio_callback, channels=1, samplerate=sample_rate):
    print("Listening to microphone. Press Ctrl+C to stop.")
    sd.sleep(duration)  # Sleep for the desired duration

# Code continues running here after Ctrl+C
