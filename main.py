import sys
import os
os.environ["LLAMA_DISABLE_METAL"] = "1"
os.environ["GGML_METAL_DISABLE"] = "1"
os.environ["LLAMA_DISABLE_MLOCK"] = "1"
import threading
import time
import wave
import datetime
import numpy as np
import json

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget,
    QLabel, QListWidget, QHBoxLayout, QLineEdit, QDialog,
    QFormLayout, QMessageBox, QProgressBar, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer, QEvent, pyqtSignal

import pyaudio
from cryptography.fernet import Fernet
import whisper

# --- Auto-install required packages ---
try:
    from huggingface_hub import hf_hub_download
except ImportError:
    print("Installing huggingface_hub...")
    os.system(f"{sys.executable} -m pip install --upgrade huggingface_hub")
    from huggingface_hub import hf_hub_download

try:
    from ctransformers import AutoModelForCausalLM
except ImportError:
    print("Installing ctransformers...")
    os.system(f"{sys.executable} -m pip install ctransformers")
    from ctransformers import AutoModelForCausalLM

# --- Global Constants & Directories ---
TRANSCRIPTS_DIR = "transcripts"
AUDIO_DIR = "audio"
KEY_FILE = "key.key"
PROMPTS_CONFIG_FILE = "prompts_config.json"

# Default psychiatric prompts
DEFAULT_PROMPTS = [
    {
        "name": "Medication Side Effects",
        "prompt": "Describe any side effects the patient is experiencing with their current medication",
        "enabled": True
    },
    {
        "name": "Current Medications",
        "prompt": "What medication was prescribed to the patient",
        "enabled": True
    }
]

class PromptConfig:
    def __init__(self):
        self.prompts = []
        self.load_or_create_config()
    
    def load_or_create_config(self):
        if os.path.exists(PROMPTS_CONFIG_FILE):
            with open(PROMPTS_CONFIG_FILE, 'r') as f:
                self.prompts = json.load(f)
        else:
            self.prompts = DEFAULT_PROMPTS
            self.save_config()
    
    def save_config(self):
        with open(PROMPTS_CONFIG_FILE, 'w') as f:
            json.dump(self.prompts, f, indent=4)
    
    def add_prompt(self, name, prompt_text):
        self.prompts.append({
            "name": name,
            "prompt": prompt_text,
            "enabled": True
        })
        self.save_config()
    
    def remove_prompt(self, name):
        self.prompts = [p for p in self.prompts if p["name"] != name]
        self.save_config()
    
    def update_prompt(self, name, new_text):
        for prompt in self.prompts:
            if prompt["name"] == name:
                prompt["prompt"] = new_text
                break
        self.save_config()
    
    def toggle_prompt(self, name):
        for prompt in self.prompts:
            if prompt["name"] == name:
                prompt["enabled"] = not prompt["enabled"]
                break
        self.save_config()

for folder in [TRANSCRIPTS_DIR, AUDIO_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- Model Download Helper and Constants for Llama ---
MODELS_DIR = "models"
if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR)

MODEL_REPO = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
MODEL_FILENAME = "mistral-7b-instruct-v0.2.Q5_K_M.gguf"
MODEL_PATH = os.path.join(MODELS_DIR, MODEL_FILENAME)

def download_llama_model():
    """Download the Mistral 7B model from Hugging Face if it doesn't exist."""
    if os.path.exists(MODEL_PATH):
        print(f"Model already exists at {MODEL_PATH}")
        return True
    
    print(f"Downloading Mistral 7B model to {MODEL_PATH}...")
    try:
        hf_hub_download(
            repo_id=MODEL_REPO,
            filename=MODEL_FILENAME,
            local_dir=MODELS_DIR,
            local_dir_use_symlinks=False
        )
        print("Download complete!")
        return True
    except Exception as e:
        print(f"Error downloading model: {str(e)}")
        print("Please ensure you have accepted the model license on Hugging Face and are logged in.")
        print("You can login using: huggingface-cli login")
        return False

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
    Summarize text using a local Mistral 7B model via ctransformers.
    """
    if not hasattr(summarize_text, "model"):
        summarize_text.model = AutoModelForCausalLM.from_pretrained(
            MODEL_REPO,
            model_file=MODEL_FILENAME,
            model_type="llama",
            gpu_layers=0
        )
    prompt = f"Summarize the following text concisely:\n{text}\nSummary:"
    response = summarize_text.model(prompt, max_new_tokens=150, threads=8)
    if isinstance(response, dict) and "choices" in response and len(response["choices"]) > 0:
        summary = response["choices"][0]["text"].strip()
    elif isinstance(response, str):
        summary = response.strip()
    else:
        summary = "No summary generated."
    return summary

# --- Login Dialog ---
class PromptDialog(QDialog):
    def __init__(self, prompt_config, parent=None):
        super(PromptDialog, self).__init__(parent)
        self.prompt_config = prompt_config
        self.setWindowTitle("Manage Prompts")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Prompt list
        self.prompt_list = QListWidget()
        self.refresh_prompt_list()
        layout.addWidget(self.prompt_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_prompt)
        button_layout.addWidget(add_button)
        
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.edit_prompt)
        button_layout.addWidget(edit_button)
        
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_prompt)
        button_layout.addWidget(delete_button)
        
        toggle_button = QPushButton("Toggle")
        toggle_button.clicked.connect(self.toggle_prompt)
        button_layout.addWidget(toggle_button)
        
        layout.addLayout(button_layout)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
    
    def refresh_prompt_list(self):
        self.prompt_list.clear()
        for prompt in self.prompt_config.prompts:
            status = "✓" if prompt["enabled"] else "✗"
            self.prompt_list.addItem(f"{status} {prompt['name']}")
    
    def add_prompt(self):
        name, ok = QInputDialog.getText(self, "Add Prompt", "Enter prompt name:")
        if ok and name:
            prompt_text, ok = QInputDialog.getMultiLineText(self, "Add Prompt", "Enter prompt text:")
            if ok and prompt_text:
                self.prompt_config.add_prompt(name, prompt_text)
                self.refresh_prompt_list()
    
    def edit_prompt(self):
        current = self.prompt_list.currentItem()
        if current:
            name = current.text()[2:]  # Remove status symbol
            for prompt in self.prompt_config.prompts:
                if prompt["name"] == name:
                    new_text, ok = QInputDialog.getMultiLineText(
                        self, "Edit Prompt", "Edit prompt text:",
                        prompt["prompt"]
                    )
                    if ok:
                        self.prompt_config.update_prompt(name, new_text)
                    break
    
    def delete_prompt(self):
        current = self.prompt_list.currentItem()
        if current:
            name = current.text()[2:]  # Remove status symbol
            reply = QMessageBox.question(
                self, "Delete Prompt",
                f"Are you sure you want to delete the prompt '{name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.prompt_config.remove_prompt(name)
                self.refresh_prompt_list()
    
    def toggle_prompt(self):
        current = self.prompt_list.currentItem()
        if current:
            name = current.text()[2:]  # Remove status symbol
            self.prompt_config.toggle_prompt(name)
            self.refresh_prompt_list()

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
    prompt_result_ready = pyqtSignal(str, str)  # prompt_name, result

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("OpenChart - Telemedicine Transcriber")
        self.resize(900, 600)
        
        # Initialize prompt configuration
        self.prompt_config = PromptConfig()
        self.prompt_results = {}  # Store results for each prompt
        
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
        self.prompt_result_ready.connect(self.on_prompt_result_ready)
        
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
        
        # Manage Prompts button
        manage_prompts_button = QPushButton("Manage Prompts")
        manage_prompts_button.clicked.connect(self.show_prompt_dialog)
        right_panel.addWidget(manage_prompts_button)
        
        # Prompts Results Area
        prompts_group = QWidget()
        self.prompts_layout = QVBoxLayout(prompts_group)
        self.prompts_layout.setSpacing(10)
        self.setup_prompt_results_ui()
        right_panel.addWidget(prompts_group)
        
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
        # Run all prompts automatically
        self.run_all_prompts()
    
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
        # Clear prompt results if a different transcript is viewed.
        self.prompt_results = {}
        self.setup_prompt_results_ui()
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

    def setup_prompt_results_ui(self):
        """Set up the UI for displaying prompt results"""
        # Clear existing prompt results widgets
        for i in reversed(range(self.prompts_layout.count())): 
            self.prompts_layout.itemAt(i).widget().setParent(None)
        
        # Create widgets for each prompt
        for prompt in self.prompt_config.prompts:
            if prompt["enabled"]:
                group = QWidget()
                layout = QVBoxLayout(group)
                
                # Header with prompt name and buttons
                header = QHBoxLayout()
                name_label = QLabel(prompt["name"])
                name_label.setStyleSheet("font-weight: bold;")
                header.addWidget(name_label)
                
                rerun_button = QPushButton("Re-run")
                rerun_button.clicked.connect(lambda p=prompt["name"]: self.rerun_prompt(p))
                header.addWidget(rerun_button)
                
                copy_button = QPushButton("Copy")
                copy_button.clicked.connect(lambda p=prompt["name"]: self.copy_prompt_result(p))
                header.addWidget(copy_button)
                
                layout.addLayout(header)
                
                # Result text area
                result_text = QTextEdit()
                result_text.setPlaceholderText("Results will appear here...")
                if prompt["name"] in self.prompt_results:
                    result_text.setPlainText(self.prompt_results[prompt["name"]])
                result_text.textChanged.connect(
                    lambda p=prompt["name"], t=result_text: self.on_prompt_result_edited(p, t)
                )
                layout.addWidget(result_text)
                
                self.prompts_layout.addWidget(group)
    
    def show_prompt_dialog(self):
        """Show the prompt management dialog"""
        dialog = PromptDialog(self.prompt_config, self)
        if dialog.exec_() == QDialog.Accepted:
            self.setup_prompt_results_ui()
    
    def rerun_prompt(self, prompt_name):
        """Re-run a specific prompt"""
        for prompt in self.prompt_config.prompts:
            if prompt["name"] == prompt_name:
                self.run_prompt(prompt)
                break
    
    def copy_prompt_result(self, prompt_name):
        """Copy a prompt's result to clipboard"""
        if prompt_name in self.prompt_results:
            QApplication.clipboard().setText(self.prompt_results[prompt_name])
    
    def on_prompt_result_edited(self, prompt_name, text_edit):
        """Handle manual editing of prompt results"""
        self.prompt_results[prompt_name] = text_edit.toPlainText()
    
    def run_prompt(self, prompt):
        """Run a single prompt against the current transcript"""
        transcript = self.transcript_text.toPlainText()
        if not transcript:
            return
        
        # Create the full prompt with context
        full_prompt = f"Based on the following transcript, {prompt['prompt']}:\n\n{transcript}"
        
        # Run in background thread
        thread = threading.Thread(
            target=self.process_prompt,
            args=(prompt["name"], full_prompt)
        )
        thread.start()
    
    def process_prompt(self, prompt_name, full_prompt):
        """Process a prompt in the background"""
        try:
            result = summarize_text(full_prompt)
            self.prompt_result_ready.emit(prompt_name, result)
        except Exception as e:
            self.prompt_result_ready.emit(prompt_name, f"Error processing prompt: {str(e)}")
    
    def on_prompt_result_ready(self, prompt_name, result):
        """Handle completion of prompt processing"""
        self.prompt_results[prompt_name] = result
        self.setup_prompt_results_ui()  # Refresh the UI
    
    def run_all_prompts(self):
        """Run all enabled prompts"""
        for prompt in self.prompt_config.prompts:
            if prompt["enabled"]:
                self.run_prompt(prompt)

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