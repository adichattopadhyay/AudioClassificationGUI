from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patheffects as path_effects
import matplotlib.colorbar as cbr
import numpy as np
import librosa
import matplotlib.pyplot as plt

WAVEFORM_HEIGHT_PERCENTAGE = 0.42

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

        layout.addWidget(self.canvas, stretch=1)

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

            # Create a grid of subplots with 2 rows and 1 column
            gs = self.figure.add_gridspec(2, 1, height_ratios=[0.1, 0.9])

            # Plot the spectrogram in the bottom subplot
            ax = self.figure.add_subplot(gs[1])
            ax.set_xlabel("")  # Remove x-axis label completely
            ax.set_ylabel("")  # Remove y-axis label completely
            ax.xaxis.tick_top()

            # Convert x-axis ticks from sample indices to seconds
            sample_rate = self.sample_rate
            num_samples = len(self.audio_data)
            num_seconds = num_samples / sample_rate
            ax.set_xticks(np.linspace(0, num_samples, num=11))
            ax.set_xticklabels([f"{i:.1f}" for i in np.linspace(0, num_seconds, num=11)])

            # Customize tick parameters for the spectrogram
            ax.tick_params(axis='x', direction='in', pad=-15, width=2, color='white', labelcolor='white')
            ax.tick_params(axis='y', direction='in', pad=-30, width=2, color='white', labelcolor='white')

            im = librosa.display.specshow(spectrogram, sr=self.sample_rate, x_axis='time', y_axis='log', ax=ax)

            # Create a new axis for the color bar in the top subplot
            cax = self.figure.add_subplot(gs[0])
            cbar = cbr.ColorbarBase(cax, im, orientation='horizontal', format='%+2.0f dB')
            cbar.ax.xaxis.set_ticks_position("top")
            cbar.ax.tick_params(axis='x', direction='in', pad=-15, color='white', labelcolor='white')
            
            # Adjust the position of the x tick labels for the color bar
            x_tick_labels = cbar.ax.get_xticklabels()
            x_tick_positions = cbar.ax.get_xticks()
            x_tick_positions[0] += 2  # Move the leftmost tick 2 units to the right
            x_tick_positions[-1] -= 2  # Move the rightmost tick 2 units to the left
            cbar.ax.set_xticks(x_tick_positions)
            cbar.ax.set_xticklabels(x_tick_labels)
            x_tick_labels[-1].set_color('black')  # Change color of the rightmost tick label

            self.figure.tight_layout()
            self.canvas.draw()
