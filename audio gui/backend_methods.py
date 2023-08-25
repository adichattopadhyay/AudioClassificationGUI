import keras
import librosa
import numpy as np
from pydub import AudioSegment
from pydub.utils import make_chunks
import time as t


def build_timestamp(start_timestamp):
    length_of_timestamp = 5
    hours, minutes, seconds = int(start_timestamp[0:2]), int(start_timestamp[3:5]), int(start_timestamp[6:])
    total_seconds = hours * 3600 + minutes * 60 + seconds + length_of_timestamp
    time = t.gmtime(total_seconds)
    final_timestamp = t.strftime('%H:%M:%S', time)
    return final_timestamp


def runBackendProcessing(path):
    model = keras.models.load_model("classification_model.keras")

    # cut file into pieces
    full_audio_file = AudioSegment.from_file(path, "wav")
    chunk_length_ms = 5000
    chunks = make_chunks(full_audio_file, chunk_length_ms)

    # Export all the individual chunks, load, classify, put into array as [timestamp_s, timestamp_e, label]
    processed_data = [[0] * 3 for i in range(len(chunks))]
    start_timestamp = "00:00:00"
    for i, chunk in enumerate(chunks):
        processed_data[i][0] = start_timestamp
        chunk_name = "chunk{0}.wav".format(i)
        chunk.export(chunk_name, format="wav")
        signal, rate = librosa.load(chunk_name, duration=5)
        for m in range(3):
            n = np.random.randint(0, len(signal) - (rate * 2))
            sig_ = signal[n: int(n + (rate * 2))]
            mfcc = librosa.feature.mfcc(y=sig_, sr=rate, n_mfcc=13)
            mfcc = np.array(mfcc)
            X_new = mfcc.reshape(1, 13, 87, 1)
        prediction = np.argmax(model.predict(X_new), axis=-1)
        class_dict = {0: 'dog', 1: 'chainsaw', 2: 'crackling_fire', 3: 'helicopter', 4: 'rain', 5: 'crying_baby',
                          6: 'clock_tick', 7: 'sneezing', 8: 'rooster', 9: 'sea_waves'}
        processed_data[i][2] = (class_dict[prediction[0]])
        end_timestamp = build_timestamp(start_timestamp)
        processed_data[i][1] = end_timestamp
        start_timestamp = end_timestamp
    return processed_data

print(runBackendProcessing("Rooster.wav"))