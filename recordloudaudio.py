import sounddevice as sd
import numpy as np
import datetime
import os
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import wavio

# Define parameters
sample_rate = 44100
duration = 1 # set the duration for the output graph
threshold = 0.02
blocksize = 1024
pre_noise_duration = 0  # Duration to record before noise threshold crossing (in seconds)
post_noise_duration = 0.5  # Duration to record after noise threshold crossing (in seconds)
min_clip_duration = 1  # Minimum duration of the recorded clip (in seconds)

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

# Function to update the audio level plot
def update_audio_level(frame):
    line.set_ydata(y_data)
    return line,

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
recording_started = False  # Flag to indicate when to start recording

# Function to handle audio data
def audio_callback(indata, frames, time, status):
    global audio_buffer, clip_duration, recording_started
    if status:
        print(f"Audio callback status: {status}")
    if any(indata > threshold):
        if not recording_started:
            print("Audio level exceeded the threshold. Starting recording...")
            recording_started = True
            audio_buffer.extend(indata.flatten())
            clip_duration += frames / sample_rate
        else:
            audio_buffer.extend(indata.flatten())
            clip_duration += frames / sample_rate
    elif recording_started:
        audio_buffer.extend(indata.flatten())
        clip_duration += frames / sample_rate
        if clip_duration >= pre_noise_duration + min_clip_duration:
            save_audio_clip(np.array(audio_buffer), audio_buffer[:int(pre_noise_duration * sample_rate)])
            audio_buffer = []
            clip_duration = 0
            recording_started = False
    y_data[:-frames] = y_data[frames:]
    y_data[-frames:] = indata.flatten()

# Create an input audio stream with a larger block size
input_stream = sd.InputStream(callback=audio_callback, blocksize=blocksize, samplerate=sample_rate, channels=1)
input_stream.start()

# Create a real-time audio level plot
ani = FuncAnimation(fig, update_audio_level, interval=0)

try:
    print("Listening to microphone. Press Ctrl+C to stop.")
    plt.show()  # Start the Matplotlib event loop
except KeyboardInterrupt:
    pass
finally:
    input_stream.stop()
    input_stream.close()