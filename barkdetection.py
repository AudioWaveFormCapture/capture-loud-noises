import librosa
import librosa.display
import numpy as np
import pyaudio
import tensorflow as tf
import datetime

# Load a pre-trained dog bark detection model (you would need to train one)
model = tf.keras.models.load_model('dog_bark_model.h5')

# Function to preprocess audio data for prediction
def preprocess_audio(y):
    # Extract relevant audio features (e.g., MFCCs)
    mfccs = librosa.feature.mfcc(y=y, sr=44100, n_mfcc=13, hop_length=512)

    # Pad or truncate the features to a fixed length (if necessary)
    max_len = 100  # Adjust as needed based on your model's input size
    if mfccs.shape[1] < max_len:
        mfccs = np.pad(mfccs, ((0, 0), (0, max_len - mfccs.shape[1])), mode='constant')
    else:
        mfccs = mfccs[:, :max_len]

    return mfccs

# Function to predict if a given audio snippet contains a dog bark
def detect_dog_bark(audio_data):
    mfccs = preprocess_audio(audio_data)
    mfccs = np.expand_dims(mfccs, axis=0)  # Add a batch dimension

    # Make a prediction using the pre-trained model
    prediction = model.predict(mfccs)

    # Interpret the prediction
    if prediction[0][0] >= 0.5:
        return "Dog bark detected"
    else:
        return "No dog bark detected"

# Initialize PyAudio to capture audio from the microphone
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)

print("Listening for dog barks...")

# Create and open a log file for writing
log_filename = f"bark_log_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
with open(log_filename, 'w') as log_file:
    while True:
        try:
            audio_data = np.frombuffer(stream.read(1024), dtype=np.int16)
            result = detect_dog_bark(audio_data)
            if result == "Dog bark detected":
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                log_line = f"{timestamp}: {result}\n"
                print(log_line)
                log_file.write(log_line)
        except KeyboardInterrupt:
            print("Stopped listening.")
            break

# Cleanup
stream.stop_stream()
stream.close()
p.terminate()