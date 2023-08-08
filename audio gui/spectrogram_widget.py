from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import librosa
import matplotlib.pyplot as plt

WAVEFORM_HEIGHT_PERCENTAGE = 0.4

class SpectrogramWidget(QWidget):
    def __init__(self, file_name, parent=None):
        super().__init__(parent)
        
        self.file_name = file_name
        self.audio_data = None
        self.sample_rate = None

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

       # Create a Matplotlib figure and canvas
        self.figure = Figure(figsize=(self.width() / 100, self.height() / 100), dpi=100)  # Adjust the figsize to fit the widget size
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Set size policy to expand the widget's height based on WAVEFORM_HEIGHT_PERCENTAGE
        height = int(self.parent().height() * WAVEFORM_HEIGHT_PERCENTAGE * 2)
        self.setMinimumHeight(height)
        self.setMaximumHeight(height)


        layout.addWidget(self.canvas)

    def loadAudioData(self):
        try:
            # Load the audio data using librosa
            self.audio_data, self.sample_rate = librosa.load(self.file_name, sr=None, mono=True, dtype=float)
            self.plotSpectrogram()
        except Exception as e:
            print(f"Error loading audio data: {str(e)}")
            self.audio_data = None

    def plotSpectrogram(self):
        if self.audio_data is not None:
            self.figure.clear()  # Clear the existing spectrogram

            # Get the actual width and height of the widget
            width = self.canvas.width()
            height = self.canvas.height()

            # Update the figsize of the figure to match the widget's dimensions
            self.figure.set_size_inches(width, height)

            # Compute the spectrogram using librosa
            spectrogram = librosa.amplitude_to_db(np.abs(librosa.stft(self.audio_data)), ref=np.max)

            # Plot the spectrogram
            ax = self.figure.add_subplot(111)
            librosa.display.specshow(spectrogram, sr=self.sample_rate, x_axis='time', y_axis='log', ax=ax)
            plt.colorbar(format='%+2.0f dB')

            ax.set_xlabel("")  # Remove x-axis label completely
            ax.set_ylabel("")  # Remove y-axis label completely
            ax.tick_params(axis='x', direction='in', pad=-15)
            ax.tick_params(axis='y', direction='in', pad=-30)

            # Convert x-axis ticks from sample indices to seconds
            sample_rate = self.sample_rate
            num_samples = len(self.audio_data)
            num_seconds = num_samples / sample_rate
            ax.set_xticks(np.linspace(0, num_samples, num=11))
            ax.set_xticklabels([f"{i:.1f}" for i in np.linspace(0, num_seconds, num=11)])

            self.canvas.draw()
