import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, \
    QVBoxLayout, QHBoxLayout, QFileDialog, QWidget, QSpacerItem, QSizePolicy, \
    QGridLayout, QCheckBox
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

from waveform_widget import WaveformWidget 
from spectrogram_widget import SpectrogramWidget

import sounddevice as sd
import threading
import librosa

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Fields
        self.file_name = "" #file_name field
        self.audio_window = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Choose Audio File")
        self.setGeometry(100, 100, 400, 300)

        # Create a label for the folder icon 
        self.folder_icon_button = QPushButton('', self)
        self.folder_icon_button.clicked.connect(self.openFileDialog)
        self.folder_icon_button.setIcon(QIcon("audio gui\\images\\icons\\folder.png"))
        self.folder_icon_button.setIconSize(QSize(50,50))
        self.folder_icon_button.setFixedSize(50, 50)  # Set a fixed size for the icon label
        self.folder_icon_button.setFlat(True)

        # Create a label for displaying the selected audio file name
        self.audio_file_label = QLabel("Choose an audio file.", self)
        self.audio_file_label.setAlignment(Qt.AlignCenter)
        self.audio_file_label.setFixedSize(1000, 50)
        self.audio_file_label.setStyleSheet("border: 1px solid black;")

        # Create a button to confirm the selection (initially hidden)
        self.confirm_button = QPushButton("Confirm", self)
        self.confirm_button.setFixedSize(200, 50)
        self.confirm_button.clicked.connect(self.onConfirmClicked)
        self.confirm_button.hide()

        # Layouts to arrange the elements
        main_layout = QVBoxLayout()
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.folder_icon_button)
        folder_layout.addItem(QSpacerItem(20, 20, hPolicy=QSizePolicy.Fixed))  # Adding a horizontal spacer
        folder_layout.addWidget(self.audio_file_label)

        # Create a vertical layout for folder_layout and confirm_button
        confirm_layout = QVBoxLayout()
        confirm_layout.addLayout(folder_layout)
        confirm_layout.addItem(QSpacerItem(20, 20, vPolicy=QSizePolicy.Fixed))  # Adding vertical spacer
        confirm_layout.addWidget(self.confirm_button)
        confirm_layout.setAlignment(Qt.AlignHCenter)  # Center confirm_button horizontally

        main_layout.addLayout(confirm_layout)  # Add confirm_layout to the main_layout

        # Create a central widget to hold the main layout
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def openFileDialog(self, event):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly  # Set the file dialog to read-only mode
        file_name, _ = QFileDialog.getOpenFileName(self, "Choose an audio file", "", "Audio Files (*.wav);;All Files (*)", options=options)

        if file_name:
            # Update the audio_file_label text with the selected file name
            self.audio_file_label.setText(file_name.split('/')[-1])

            # Stores the file_name in a field
            self.file_name = file_name

            # Show the confirm button when an audio file is selected
            self.confirm_button.show()
    
    def onConfirmClicked(self):
        if self.file_name:
            # Create a new instance of AudioWindow and show it in full-screen mode
            self.audio_window = AudioWindow(self.file_name)
            self.audio_window.showMaximized()

            # Run backend
            self.audio_window.waveform_widget.runBackendProcessing()

            # Close the current window
            self.close()
            
class AudioWindow(QMainWindow):
    def __init__(self, file_name):
        super().__init__()

        # Fields
        self.file_name = file_name
        self.audio_data = None
        self.sample_rate = None
        self.playing = False  # Keep track of audio playback state
        self.start_index = None  # Start index of selected audio
        self.end_index = None  # End index of selected audio

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Audio Window")
        self.setGeometry(100, 100, 800, 600)

        # Play button
        self.audio_control_button = QPushButton('', self)
        self.audio_control_button.clicked.connect(self.onClickAudioControl)
        self.audio_control_button.setIcon(QIcon("audio gui\\images\\icons\\play.png"))
        self.audio_control_button.setIconSize(QSize(30, 30))
        self.audio_control_button.setStyleSheet("border-radius: 20; border: 2px solid black")
        self.audio_control_button.setFixedSize(40, 40)  # Set fixed size for the button

        # Create checkboxes and labels
        self.adjust_labels_checkbox = QCheckBox("Adjust Labels", self)
        self.show_spectrogram_checkbox = QCheckBox("Show Spectrograms", self)
        self.adjust_labels_checkbox.setChecked(False)  # Set default state
        self.show_spectrogram_checkbox.setChecked(False)  # Set default state

        # Connect checkbox signals to appropriate slots/methods
        self.adjust_labels_checkbox.stateChanged.connect(self.onAdjustLabelsCheckboxChanged)
        self.show_spectrogram_checkbox.stateChanged.connect(self.onShowSpectrogramCheckboxChanged)

        # Create the waveform widget and set the audio data
        self.waveform_widget = WaveformWidget(self.file_name, parent=self)
        self.waveform_widget.set_selection_bounds.connect(self.selection_bounds)

        # Create the spectrogram widget (initially hidden)
        self.spectrogram_widget = SpectrogramWidget(self.file_name, parent=self)
        self.spectrogram_widget.hide()

        # Create layout for checkboxes and labels
        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.adjust_labels_checkbox)
        checkbox_layout.addWidget(self.show_spectrogram_checkbox)

        # Create layout for audio control button and checkboxes
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.audio_control_button, alignment=Qt.AlignCenter)
        control_layout.addLayout(checkbox_layout)

        layout = QGridLayout()
        layout.addWidget(self.waveform_widget, 0, 0, 1, 1, alignment=Qt.AlignTop)
        layout.addLayout(control_layout, 1, 0, 1, 1, alignment=Qt.AlignCenter | Qt.AlignTop)
        layout.addWidget(self.spectrogram_widget, 2, 0, 1, 1, alignment=Qt.AlignTop)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Load audio data
        self.loadAudioData()

    def loadAudioData(self):
        try:
            # Load the audio data using librosa
            self.audio_data, self.sample_rate = librosa.load(self.file_name, sr=None, mono=True, dtype=float)
            self.waveform_widget.loadAudioData()
            self.spectrogram_widget.loadAudioData()
        except Exception as e:
            print(f"Error loading audio data: {str(e)}")
            self.audio_data = None

    def selection_bounds(self, start_index, end_index):
        self.start_index = start_index
        self.end_index = end_index

        if start_index < 0:
            self.start_index = None
        if end_index < 0:
            self.end_index = None

    def onClickAudioControl(self):
        if self.playing:
            self.stopAudio()  # If audio is playing, stop it
        else:
            self.playAudio()  # If audio is not playing, start playing

        # Toggle the playing state
        self.playing = not self.playing

        # Update the button icon based on the playing state
        if self.playing:
            self.audio_control_button.setIcon(QIcon("audio gui\\images\\icons\\stop.png"))
        else:
            self.audio_control_button.setIcon(QIcon("audio gui\\images\\icons\\play.png"))

    def playAudio(self):
        if self.audio_data is not None:
            audio_data = self.audio_data
            sample_rate = self.sample_rate

            # If end_index is not provided, play the entire audio
            if self.end_index is None:
                self.end_index = len(audio_data)

            # Extract the selected portion of the audio
            selected_audio = audio_data[self.start_index:self.end_index]

            # Create a thread for audio playback
            def play_thread():
                # Play the audio without a callback
                sd.play(selected_audio, sample_rate)

                # Wait until the audio playback is complete
                sd.wait()

                # Audio playback completed  
                self.audio_control_button.setIcon(QIcon("audio gui\\images\\icons\\play.png"))
                self.playing = False

            # Start the playback thread
            threading.Thread(target=play_thread).start()

    def stopAudio(self):
        # Stop audio playback
        sd.stop()

    def onAdjustLabelsCheckboxChanged(self, state):
        if state == Qt.Checked:
            # Handle checkbox checked state
            self.show_spectrogram_checkbox.setChecked(False)
            print("Adjust Labels checkbox checked")
        else:
            # Handle checkbox unchecked state
            print("Adjust Labels checkbox unchecked")

    def onShowSpectrogramCheckboxChanged(self, state):
        if state == Qt.Checked:
            # Show the spectrogram widget
            self.adjust_labels_checkbox.setChecked(False)
            self.spectrogram_widget.show()
        else:
            # Hide the spectrogram widget
            self.spectrogram_widget.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
