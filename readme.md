# OpenScriber

A telemedicine transcription and analysis tool that helps healthcare providers efficiently process and analyze patient conversations.

## Features

- Real-time audio recording and transcription
- Automated analysis of medical conversations
- Customizable analysis prompts
- Secure storage of transcripts and audio
- Multi-user support with individual encryption

## Installation

```bash
pip install openscriber
```

## Requirements

- Python 3.8 or higher
- PyQt5 for the GUI
- PyAudio for audio recording
- Whisper for transcription
- Other dependencies are automatically installed

## Usage

1. Run the application:
```bash
openscriber
```

2. Create an account or log in
3. Start recording your medical conversation
4. The application will automatically transcribe and analyze the conversation
5. View and copy the results as needed

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/openscriber.git
cd openscriber
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
