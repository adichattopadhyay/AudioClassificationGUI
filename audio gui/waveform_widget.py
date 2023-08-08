from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
import matplotlib.patheffects as path_effects
import numpy as np
import librosa
import time as t
from PyQt5.QtCore import pyqtSignal


# Constants for the waveform visualization
WAVEFORM_HEIGHT_PERCENTAGE = 0.35

class WaveformWidget(QWidget):
    # Define signals for audio playback start and stop
    set_selection_bounds = pyqtSignal(int, int)
    audioPlaybackStopRequested = pyqtSignal()

    def __init__(self, file_name, parent=None):
        super().__init__(parent)

        self.file_name = file_name
        self.audio_data = None
        self.processed_data = None
        self.called_tight_layout = False
        self.sample_rate = None

        self.start_index = None
        self.end_index = None

        self.mouse_pressed = False
        self.selection_made = False
        self.is_selecting = False

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

        self.canvas.mpl_connect('button_press_event', self.mousePressEvent)
        self.canvas.mpl_connect('motion_notify_event', self.mouseMoveEvent)
        self.canvas.mpl_connect('button_release_event', self.mouseReleaseEvent)

    def plotWaveform(self):
        if self.audio_data is not None:
            self.figure.clear()  # Clear the existing plot

            # Get the actual width and height of the widget
            width = self.canvas.width()
            height = self.canvas.height()

            # Update the figsize of the figure to match the widget's dimensions
            self.figure.set_size_inches(width, height)

            ax = self.figure.add_subplot(111)
            self.ax = ax
            time = np.arange(len(self.audio_data))  # Time points
            ax.plot(time, self.audio_data)

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

            # Create the selection overlay Rectangle and add it to the plot
            self.selection_overlay = Rectangle((0, 0), 0, 0, color='gray', alpha=0.5)
            ax.add_patch(self.selection_overlay)

            self.figure.tight_layout()  # Stretch the graph to fit the available space
            self.canvas.draw()

    def loadAudioData(self):
        try:
            # Load the audio data using librosa
            self.audio_data, self.sample_rate = librosa.load(self.file_name, sr=None, mono=True, dtype=float)
            self.plotWaveform()
        except Exception as e:
            print(f"Error loading audio data: {str(e)}")
            self.audio_data = None

    def runBackendProcessing(self):
        # Placeholder for backend processing
        # Sleep for 2 seconds to simulate backend processing
        t.sleep(2)

        print("Fake backend done")

        # Dummy data representing the list of timestamps and classifications
        dummy_data = [
            ["00:00:00.397", "00:00:00.648", "Classification A"],
            ["00:00:00.697", "00:00:01.057", "Classification B"],
            ["00:00:01.096", "00:00:01.350", "Classification C"],
        ]

        self.processed_data = dummy_data  # Store the dummy data in self.processed_data
        self.addLines()  # Update the waveform graph with the processed data

    def addLines(self):
        if hasattr(self, 'processed_data') and self.processed_data:
            # Loop through the processed_data and draw lines with labels
            for data in self.processed_data:
                start_time = data[0]  # Start timestamp (e.g., "00:00:02.500")
                end_time = data[1]    # End timestamp (e.g., "00:00:10.200")
                classification = data[2]  # Classification label (e.g., "Classification A")

                # Convert start_time and end_time to time points on the x-axis
                start_time_index = self.convertTimeToIndex(start_time)
                end_time_index = self.convertTimeToIndex(end_time)

                # Draw the line between start_time and end_time
                self.ax.plot([start_time_index, end_time_index], [0, 0], color='red', linewidth=2)

                # Add text label with classification at the midpoint of the line
                text_x = (start_time_index + end_time_index) / 2
                self.ax.text(text_x, 0.05, classification, color='white', fontsize=12, ha='center', va='center', weight='bold', path_effects=[path_effects.Stroke(linewidth=3, foreground='black'),
                       path_effects.Normal()])

    def convertTimeToIndex(self, timestamp):
        # Convert HR:MM:SS.SSS timestamp to time index in milliseconds
        time_parts = timestamp.split(":")
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        seconds, milliseconds = map(float, time_parts[2].split("."))
        time_in_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0

        # Convert time to the sample
        if self.sample_rate is None:
            raise ValueError("Sample rate not available. Load audio data first using loadAudioData().")
        sample_index = int(time_in_seconds * self.sample_rate)

        return sample_index

    def mousePressEvent(self, event):
        # Emit a signal with the start index of the selected audio when the mouse is pressed
        if not self.selection_made and event.xdata is not None:
            self.mouse_pressed = True
            self.start_index = self.convertTimeToIndex(self.sample_to_timestamp(event.xdata))
            self.end_index = None
        elif self.selection_made:
            self.start_index = None
            self.end_index = None
            self.selection_made = False
            self.drawSelection(self.start_index, self.end_index)
            self.set_selection_bounds.emit(-1, -1)

    def mouseMoveEvent(self, event):
        # Update the end index of the selected audio when the mouse is moved while pressed
        if event.xdata is not None and self.mouse_pressed:
            self.is_selecting = True    
            self.end_index = self.convertTimeToIndex(self.sample_to_timestamp(event.xdata))
            self.drawSelection(self.start_index, self.end_index)

    def mouseReleaseEvent(self, event):
        # When the mouse is released, emit a signal with the start and end indices of the selected audio
        if event.xdata is not None and self.is_selecting:
            self.is_selecting = False
            self.mouse_pressed = False
            self.selection_made = True
            self.end_index = self.convertTimeToIndex(self.sample_to_timestamp(event.xdata))
            self.drawSelection(self.start_index, self.end_index)

        # Emit signal to start audio playback with the selected audio range
        if self.start_index is not None and self.end_index is not None:
            self.set_selection_bounds.emit(self.start_index, self.end_index)

    def drawSelection(self, start_index, end_index):
        # Method to update the position of the selection overlay on the waveform plot
        if start_index is not None and end_index is not None:
            # Update the selection overlay position and size
            x = min(start_index, end_index)
            y = -0.5  # Position the selection overlay slightly below the waveform
            selection_width = int(abs(start_index - end_index))
            selection_height = 1.0  # Make the selection overlay cover the full height of the waveform

            self.selection_overlay.set_xy((x, y))
            self.selection_overlay.set_width(selection_width)
            self.selection_overlay.set_height(selection_height)
            self.canvas.draw()
        else:
            self.selection_overlay.set_width(0)
            self.selection_overlay.set_height(0)
            self.canvas.draw()

    def sample_to_timestamp(self, sample):
        # Convert the audio samples to the timestamp format "HR:MM:SS.SSS"
        if self.sample_rate is None:
            raise ValueError("Sample rate not available. Load audio data first using loadAudioData().") 

        time_in_seconds = sample / self.sample_rate
        milliseconds = int((time_in_seconds % 1) * 1000)
        time_obj = t.gmtime(time_in_seconds)
        timestamp = t.strftime("%H:%M:%S.", time_obj) + f"{milliseconds:03d}"
        return timestamp
