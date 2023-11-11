import sounddevice as sd
import numpy as np
import datetime
import os
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from pyqtgraph.Qt import QtCore

# Define parameters
sample_rate = 44100
duration = 5
threshold = 0.02
blocksize = 1024
pre_noise_duration = 0
post_noise_duration = 0.5
min_clip_duration = 1

# Create a directory to store audio clips
os.makedirs("audio_clips", exist_ok=True)

# Initialize variables for audio level plot
x_data = np.arange(0, duration, 1 / sample_rate)
y_data = np.zeros(len(x_data))

# Create an application
app = QApplication([])

# Create a main window
main_window = QMainWindow()
main_window.setWindowTitle("Real-time Audio Level Plot")

# Create a central widget
central_widget = QWidget()
main_window.setCentralWidget(central_widget)

# Create a layout for the central widget
layout = QVBoxLayout()
central_widget.setLayout(layout)

# Create a PyQtGraph plot widget
plot_widget = pg.PlotWidget()
layout.addWidget(plot_widget)

# Add a curve to the plot widget
curve = plot_widget.plot(pen='r')

# Function to create a filename for audio clips
def create_audio_clip_filename():
    now = datetime.datetime.now()
    return f"audio_clips/test_{now.strftime('%Y-%m-%d_%H-%M-%S')}.wav"

# Function to save an audio clip
def save_audio_clip(recording, buffer_audio):
    audio_clip_filename = create_audio_clip_filename()
    if buffer_audio is not None:
        recording = np.concatenate([buffer_audio, recording])
    sd.write(audio_clip_filename, recording, sample_rate, format='wav')  # Use sounddevice to write WAV files
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
    y_data[:-frames] = y_data[frames:]
    y_data[-frames:] = indata.flatten()
    curve.setData(x_data, y_data)

# Create an input audio stream with a larger block size
input_stream = sd.InputStream(callback=audio_callback, blocksize=blocksize, samplerate=sample_rate, channels=1)
input_stream.start()

# Create a real-time audio level plot
timer = QtCore.QTimer()
timer.timeout.connect(app.processEvents)
timer.start(0)

# Show the main window
main_window.show()

try:
    print("Listening to microphone. Press Ctrl+C to stop.")
    app.exec_()  # Start the PyQtGraph event loop
except KeyboardInterrupt:
    pass
finally:
    timer.stop()
    input_stream.stop()
    input_stream.close()
