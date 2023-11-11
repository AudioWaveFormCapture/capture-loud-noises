import sounddevice as sd
import numpy as np
import datetime
import os
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import wavio

# Define parameters
sample_rate = 44100
duration = 5
threshold = 0.02
blocksize = 1024
pre_noise_duration = 1
post_noise_duration = 0.5
min_clip_duration = 1
stop_duration = 1  # Duration to stop recording after audio level drops below threshold (in seconds)

# Create a directory to store audio clips
os.makedirs("audio_clips", exist_ok=True)

# Initialize variables for audio level plot
x_data = np.arange(0, duration, 1 / sample_rate)
y_data = np.zeros(len(x_data))
fig, ax = plt.subplots()
line, = ax.plot(x_data, y_data)
ax.set_ylim(0, 1)
ax.axhline(y=threshold, color='r', linestyle='--')

# Function to create a filename for audio clips
def create_audio_clip_filename():
    now = datetime.datetime.now()
    return f"audio_clips/test_{now.strftime('%Y-%m-%d_%H-%M-%S')}.wav"

# Function to save an audio clip
def save_audio_clip(recording, buffer_audio):
    audio_clip_filename = create_audio_clip_filename()
    if buffer_audio is not None:
        recording = np.concatenate([buffer_audio, recording])
    wavio.write(audio_clip_filename, recording, sample_rate, sampwidth=3)  # Use wavio to write WAV files
    print(f"Saved audio clip as {audio_clip_filename}")

# Variables to track the audio buffer and clip duration
audio_buffer = []
clip_duration = 0
recording_started = False
low_noise_duration = 0

# Function to handle audio data
def audio_callback(indata, frames, time, status):
    global audio_buffer, clip_duration, recording_started, low_noise_duration
    if status:
        print(f"Audio callback status: {status}")
    if any(indata > threshold):
        if not recording_started:
            print("Audio level exceeded the threshold. Starting recording...")
            recording_started = True
            audio_buffer.extend(indata.flatten())
            clip_duration += frames / sample_rate
            low_noise_duration = 0  # Reset low noise duration
            line.set_color('r')  # Change the color to red when the threshold is reached
        else:
            audio_buffer.extend(indata.flatten())
            clip_duration += frames / sample_rate
            low_noise_duration = 0  # Reset low noise duration
    elif recording_started:
        audio_buffer.extend(indata.flatten())
        clip_duration += frames / sample_rate
        low_noise_duration += frames / sample_rate  # Increase low noise duration
        if low_noise_duration >= stop_duration:
            stop_recording()

    # Rectify audio data (convert negative values to positive)
    indata = np.abs(indata)

    y_data[:-frames] = y_data[frames:]
    y_data[-frames:] = indata.flatten()
    line.set_ydata(y_data)

# Function to stop recording and save the audio clip
def stop_recording():
    global audio_buffer, clip_duration, recording_started
    if clip_duration >= pre_noise_duration + min_clip_duration:
        # Save the current clip and start a new one
        save_audio_clip(np.array(audio_buffer), audio_buffer[:int(pre_noise_duration * sample_rate)])
    audio_buffer = []
    clip_duration = 0
    recording_started = False
    line.set_color('b')  # Change the color back to blue

# Create an input audio stream with a larger block size
input_stream = sd.InputStream(callback=audio_callback, blocksize=blocksize, samplerate=sample_rate, channels=1)
input_stream.start()

# Create a real-time audio level plot
ani = FuncAnimation(fig, lambda x: None, interval=0)  # Empty animation function, we update the plot in audio_callback

try:
    print("Listening to microphone. Press Ctrl+C to stop.")
    plt.show()  # Start the Matplotlib event loop
except KeyboardInterrupt:
    pass
finally:
    input_stream.stop()
    input_stream.close()
