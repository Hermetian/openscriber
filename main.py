import sys
import os
import threading
import time
import wave
import datetime
import numpy as np
import json

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget,
    QLabel, QListWidget, QHBoxLayout, QLineEdit, QDialog,
    QFormLayout, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, QEvent, pyqtSignal

import pyaudio
from cryptography.fernet import Fernet
import whisper

# --- Global Constants & Directories ---
TRANSCRIPTS_DIR = "transcripts"
AUDIO_DIR = "audio"
KEY_FILE = "key.key"

for folder in [TRANSCRIPTS_DIR, AUDIO_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- Encryption Helpers ---
def load_or_create_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    return key

encryption_key = load_or_create_key()
fernet = Fernet(encryption_key)

def save_encrypted_transcript(filename, transcript_text):
    # Encrypts and writes transcript text to disk.
    encrypted = fernet.encrypt(transcript_text.encode())
    with open(filename, "wb") as f:
        f.write(encrypted)

def load_encrypted_transcript(filename):
    with open(filename, "rb") as f:
        encrypted = f.read()
    try:
        decrypted = fernet.decrypt(encrypted)
        return decrypted.decode()
    except Exception as e:
        return "Error decrypting file."

# --- Dummy AI Functions ---
def transcribe_audio(audio_file):
    # Load the Whisper model only once and cache it as a function attribute.
    if not hasattr(transcribe_audio, "model"):
        transcribe_audio.model = whisper.load_model("base")
    result = transcribe_audio.model.transcribe(audio_file)
    return result["text"]

def summarize_text(text):
    """
    Replace this stub with an actual local LLaMA-based summarization.
    """
    time.sleep(2)  # simulate processing delay
    return f"Summary: {text[:50]}..."

# --- Login Dialog ---
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.setWindowTitle("Login")
        layout = QFormLayout(self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addRow("Password:", self.password_input)
        self.password_input.returnPressed.connect(self.check_password)
        self.setLayout(layout)
        self.correct_password = "demo"  # hard-coded for demonstration

    def check_password(self):
        if self.password_input.text() == self.correct_password:
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Incorrect password")
            self.password_input.clear()

# --- Main Application Window ---
class MainWindow(QMainWindow):
    # Signals to safely update the UI from worker threads.
    transcription_done = pyqtSignal(str, str)
    transcription_progress_update = pyqtSignal(int)
    summary_done = pyqtSignal(str)

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("OpenChart - Telemedicine Transcriber")
        self.resize(900, 600)
        
        # Audio recording parameters (PyAudio)
        self.audio = pyaudio.PyAudio()
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.is_recording = False
        self.frames = []
        self.stream = None
        
        # Set up UI components
        self.setup_ui()
        
        # Connect signals
        self.transcription_done.connect(self.on_transcription_done)
        self.transcription_progress_update.connect(self.update_transcription_progress)
        self.summary_done.connect(self.on_summary_done)
        
        # For auto logout a QTimer could be added here to track inactivity.
        # self.logout_timer = QTimer(self)
        # self.logout_timer.setInterval(5*60*1000)  # 5 minutes
        # self.logout_timer.timeout.connect(self.handle_logout)
        # self.logout_timer.start()
        
    def setup_ui(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Left: Transcript List
        self.transcript_list = QListWidget()
        self.transcript_list.setFixedWidth(250)
        self.transcript_list.itemClicked.connect(self.load_transcript)
        main_layout.addWidget(self.transcript_list)
        self.refresh_transcript_list()
        
        # Right: Main panel with controls and transcript view
        right_panel = QVBoxLayout()
        
        # Status label
        self.status_label = QLabel("Idle")
        right_panel.addWidget(self.status_label)
        
        # Record button
        self.record_button = QPushButton("Record")
        self.record_button.clicked.connect(self.toggle_recording)
        right_panel.addWidget(self.record_button)
        
        # Transcription progress indicator (hidden by default)
        self.transcription_progress = QProgressBar()
        self.transcription_progress.setVisible(False)
        self.transcription_progress.setFormat("Transcribing...")
        right_panel.addWidget(self.transcription_progress)
        
        # Transcript Text area
        self.transcript_text = QTextEdit()
        self.transcript_text.setPlaceholderText("Transcript appears here after recording...")
        right_panel.addWidget(self.transcript_text)
        
        # Summary button and area
        self.summary_button = QPushButton("Generate Summary")
        self.summary_button.clicked.connect(self.generate_summary)
        right_panel.addWidget(self.summary_button)
        
        self.summary_text = QTextEdit()
        self.summary_text.setPlaceholderText("Summary appears here...")
        right_panel.addWidget(self.summary_text)
        
        main_layout.addLayout(right_panel)
    
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        self.status_label.setText("Recording...")
        self.record_button.setText("Stop")
        self.is_recording = True
        self.frames = []
        # Open stream for recording
        self.stream = self.audio.open(format=self.FORMAT,
                                      channels=self.CHANNELS,
                                      rate=self.RATE,
                                      input=True,
                                      frames_per_buffer=self.CHUNK)
        # Start recording in a separate thread
        self.recording_thread = threading.Thread(target=self.record)
        self.recording_thread.start()
    
    def record(self):
        while self.is_recording:
            try:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                print("Recording error:", e)
                self.is_recording = False
                break
    
    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            if self.recording_thread.is_alive():
                self.recording_thread.join()
            if self.stream and self.stream.is_active():
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except Exception as e:
                    print("Error stopping stream:", e)
            self.record_button.setText("Record")
            self.status_label.setText("Processing audio...")
            # Show the transcription progress indicator as busy
            self.transcription_progress.setVisible(True)
            self.transcription_progress.setRange(0, 0)
            
            # Save audio to file with a timestamp-based name
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = os.path.join(AUDIO_DIR, f"session_{timestamp}.wav")
            try:
                wf = wave.open(audio_filename, "wb")
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
                wf.setframerate(self.RATE)
                wf.writeframes(b"".join(self.frames))
                wf.close()
                # Start transcription in a background thread
                t = threading.Thread(target=self.process_transcription, args=(audio_filename,))
                t.start()
            except Exception as e:
                print("Error saving audio file:", e)
                self.status_label.setText("Error saving audio file")
    
    def process_transcription(self, audio_file):
        # Load full audio using Whisper's utility
        audio = whisper.load_audio(audio_file)
        sr = 16000  # Whisper's expected sample rate
        chunk_duration = 30  # Process audio in 30-second chunks
        chunk_length = chunk_duration * sr
        total_length = audio.shape[0]
        total_chunks = int(np.ceil(total_length / chunk_length))
        
        # Determine state file to persist progress
        state_file = audio_file + '.state'
        start_chunk = 0
        transcript = ""
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                state = json.load(f)
                start_chunk = state.get("last_processed_chunk", 0) + 1
                transcript = state.get("transcript", "")
        
        # Load Whisper model (reuse if already loaded)
        if not hasattr(transcribe_audio, "model"):
            transcribe_audio.model = whisper.load_model("base")
        model = transcribe_audio.model
        
        # Process audio in chunks
        for i in range(start_chunk, total_chunks):
            start_sample = i * chunk_length
            end_sample = min((i + 1) * chunk_length, total_length)
            audio_chunk = audio[start_sample:end_sample]
            # Pad last chunk with zeros if needed
            if audio_chunk.shape[0] < chunk_length:
                pad_width = chunk_length - audio_chunk.shape[0]
                audio_chunk = np.pad(audio_chunk, (0, pad_width), mode='constant')
            
            # Compute mel spectrogram and decode transcript for this chunk
            mel = whisper.log_mel_spectrogram(audio_chunk)
            options = whisper.DecodingOptions()
            result = whisper.decode(model, mel, options)
            chunk_transcript = result.text
            transcript += chunk_transcript + " "
            
            # Persist state after processing this chunk
            with open(state_file, 'w') as f:
                json.dump({"last_processed_chunk": i, "transcript": transcript}, f)
            
            # Update progress on UI using signal
            progress_percent = int(((i + 1) / total_chunks) * 100)
            self.transcription_progress_update.emit(progress_percent)
        
        # Remove state file after completion
        if os.path.exists(state_file):
            os.remove(state_file)
        
        self.transcription_done.emit(audio_file, transcript)
    
    def on_transcription_done(self, audio_file, transcript):
        # Update transcript text area
        self.transcript_text.setPlainText(transcript)
        self.status_label.setText("Transcription complete.")
        # Hide the transcription progress indicator
        self.transcription_progress.setVisible(False)
        # Save transcript to an encrypted file.
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        transcript_filename = os.path.join(TRANSCRIPTS_DIR, f"transcript_{timestamp}.bin")
        save_encrypted_transcript(transcript_filename, transcript)
        self.refresh_transcript_list()
    
    def generate_summary(self):
        transcript = self.transcript_text.toPlainText().strip()
        if not transcript:
            QMessageBox.warning(self, "Warning", "No transcript available to summarize.")
            return
        self.status_label.setText("Generating summary...")
        # Start summarization in background thread
        t = threading.Thread(target=self.process_summary, args=(transcript,))
        t.start()
    
    def process_summary(self, transcript):
        summary = summarize_text(transcript)
        self.summary_done.emit(summary)
    
    def on_summary_done(self, summary):
        self.summary_text.setPlainText(summary)
        self.status_label.setText("Summary complete.")
    
    def refresh_transcript_list(self):
        self.transcript_list.clear()
        for fname in sorted(os.listdir(TRANSCRIPTS_DIR), reverse=True):
            if fname.endswith(".bin"):
                self.transcript_list.addItem(fname)
    
    def load_transcript(self, item):
        fname = item.text()
        filepath = os.path.join(TRANSCRIPTS_DIR, fname)
        transcript = load_encrypted_transcript(filepath)
        self.transcript_text.setPlainText(transcript)
        # Clear summary if a different transcript is viewed.
        self.summary_text.clear()
        self.status_label.setText(f"Loaded transcript: {fname}")
    
    # For auto logout you could override eventFilter here:
    # def eventFilter(self, obj, event):
    #     if event.type() in [QEvent.KeyPress, QEvent.MouseMove, QEvent.MouseButtonPress]:
    #         self.logout_timer.start()  # reset timer on user activity
    #     return super(MainWindow, self).eventFilter(obj, event)
    
    # def handle_logout(self):
    #     # Lock the app and require login again
    #     QMessageBox.information(self, "Session Timeout", "Logging out due to inactivity.")
    #     dlg = LoginDialog(self)
    #     if dlg.exec_() != QDialog.Accepted:
    #         self.close()
    #     else:
    #         self.logout_timer.start()

    # New slot for updating progress bar
    def update_transcription_progress(self, progress):
        self.transcription_progress.setVisible(True)
        self.transcription_progress.setRange(0, 100)
        self.transcription_progress.setValue(progress)

def main():
    app = QApplication(sys.argv)
    
    # Show login dialog first
    login = LoginDialog()
    if login.exec_() != QDialog.Accepted:
        sys.exit(0)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 