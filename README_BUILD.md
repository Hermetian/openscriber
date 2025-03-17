# Building OpenScriber Executables

This document provides instructions for building executable files (.exe for Windows and .dmg for macOS) for the OpenScriber application.

## Prerequisites

1. Python 3.8 or newer
2. PyQt5
3. All dependencies listed in requirements.txt

## Setup Environment

Before building, make sure your development environment is properly set up:

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Building Executables

### Automatic Build Process

The easiest way to build the application is to use the included build script:

```bash
python build_app.py
```

This script will:
1. Install required packaging tools
2. Clean up previous build artifacts
3. Run PyInstaller with appropriate configurations
4. Create platform-specific packages (.exe on Windows, .dmg on macOS)

### Manual Build Process

If you prefer to build manually or need to customize the build process:

#### Windows (.exe)

```bash
pyinstaller --name=OpenScriber --onedir --windowed --noconfirm --clean ^
  --icon=app_icon.ico ^
  --add-data="prompts_config.json;." ^
  --hidden-import=huggingface_hub ^
  --hidden-import=ctransformers ^
  --hidden-import=whisper ^
  --hidden-import=pyaudio ^
  --hidden-import=cryptography ^
  --hidden-import=numpy ^
  --hidden-import=hashlib ^
  --add-data="models;models" ^
  openscriber/openscriber.py
```

The executable will be located at `dist/OpenScriber/OpenScriber.exe`.

#### macOS (.dmg)

```bash
pyinstaller --name=OpenScriber --onedir --windowed --noconfirm --clean \
  --icon=app_icon.icns \
  --osx-bundle-identifier=com.openscriber.openscriber \
  --add-data="prompts_config.json:." \
  --hidden-import=huggingface_hub \
  --hidden-import=ctransformers \
  --hidden-import=whisper \
  --hidden-import=pyaudio \
  --hidden-import=cryptography \
  --hidden-import=numpy \
  --hidden-import=hashlib \
  --add-data="models:models" \
  openscriber/openscriber.py

# Create DMG (requires hdiutil, which is standard on macOS)
hdiutil create -volname "OpenScriber" -srcfolder "dist/OpenScriber.app" -ov -format UDZO "dist/OpenScriber-1.0.0.dmg"
```

The application bundle will be located at `dist/OpenScriber.app` and the DMG at `dist/OpenScriber-1.0.0.dmg`.

## Handling Machine Learning Models

The application uses Whisper and Mistral 7B models, which can be:

1. **Bundled with the application**: Include the models in the `models` directory before building.
2. **Downloaded at runtime**: The app will download required models on first run.

For smaller distribution size, option 2 is recommended, though it requires internet connectivity on first run.

## Common Issues

### Missing Dependencies

If you encounter errors about missing dependencies:
- For PyQt5 issues: Make sure you have the proper PyQt5 bindings installed
- For platform-specific libraries: Ensure you have all system dependencies installed

### Large File Size

The executable may be large due to included libraries and models:
- To reduce size, consider using UPX compression (add `--upx-dir=/path/to/upx` to PyInstaller)
- For production, consider an installer that downloads ML models separately

### macOS Security Issues

On macOS, users may need to bypass Gatekeeper:
1. Right-click on the app and select "Open"
2. Click "Open" in the security dialog

## Code Signing

For production releases, consider code signing your executables:
- On Windows, use a code signing certificate with SignTool
- On macOS, use a Developer ID certificate with codesign

## Additional Resources

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [PyQt5 Deployment](https://doc.qt.io/qt-5/deployment.html)
- [macOS Application Packaging](https://developer.apple.com/documentation/xcode/distributing_your_app_for_beta_testing_and_releases) 