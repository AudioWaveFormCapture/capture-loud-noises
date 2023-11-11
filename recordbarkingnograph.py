import sounddevice as sd
import numpy as np
import datetime
import os
import wavio

# Define parameters
sample_rate = 44100
duration = 1
threshold = 0.05
blocksize = 1024
pre_noise_duration = 0
post_noise_duration = 0.5
min_clip_duration = 1

# Create a directory to store audio clips
os.makedirs("audio_clips", exist_ok=True)

# Function to create a filename for audio clips
def create_audio_clip_filename():
    now = datetime.datetime.now()
    return f"audio_clips/test_{now.strftime('%Y-%m-%d_%H-%M-%S')}.wav"

# Function to save an audio clip
def save_audio_clip(recording, buffer_audio):
    audio_clip_filename = create_audio_clip_filename()
    if buffer_audio is not None:
        recording = np.concatenate([buffer_audio, recording])
    wavio.write(audio_clip_filename, recording, sample_rate, sampwidth=3)
    print(f"Saved audio clip as {audio_clip_filename}")

# Variables to track the audio buffer and clip duration
audio_buffer = []
clip_duration = 0
recording_started = False

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

# Create an input audio stream with a larger block size
input_stream = sd.InputStream(callback=audio_callback, blocksize=blocksize, samplerate=sample_rate, channels=1)
input_stream.start()

try:
    print("Listening to the microphone. Press Ctrl+C to stop.")
    while True:
        pass
except KeyboardInterrupt:
    pass
finally:
    input_stream.stop()
    input_stream.close()
