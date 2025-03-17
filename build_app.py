#!/usr/bin/env python3
import sys
import os
import platform
import subprocess
import shutil

# Configuration
APP_NAME = "OpenScriber"
MAIN_SCRIPT = "openscriber/openscriber.py"
VERSION = "1.0.0"
AUTHOR = "OpenScriber"

# Detect platform
is_windows = platform.system() == "Windows"
is_mac = platform.system() == "Darwin"

# Create build directory if it doesn't exist
if not os.path.exists("dist"):
    os.makedirs("dist")

# Install required packages for packaging
print("Installing packaging requirements...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"])

# Additional requirements based on platform
if is_mac:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "dmgbuild"])

# Remove previous build artifacts
for clean_dir in ["build", os.path.join("dist", APP_NAME)]:
    if os.path.exists(clean_dir):
        print(f"Cleaning up {clean_dir}...")
        shutil.rmtree(clean_dir)

# Basic PyInstaller arguments
pyinstaller_args = [
    "--name=%s" % APP_NAME,
    "--onedir",
    "--windowed",
    "--noconfirm",
    "--clean",
    # Data files
    "--add-data=prompts_config.json:.",
    # Hidden imports
    "--hidden-import=huggingface_hub",
    "--hidden-import=ctransformers",
    "--hidden-import=whisper",
    "--hidden-import=pyaudio",
    "--hidden-import=cryptography",
    "--hidden-import=numpy",
    "--hidden-import=hashlib",
    # ML models directory
    "--add-data=models:models",
]

# Platform-specific configurations
if is_windows:
    # Add Windows-specific icon only if it exists
    icon_path = "app_icon.ico"
    if os.path.exists(icon_path):
        pyinstaller_args.append(f"--icon={icon_path}")
    
    # Add PyQt5 DLLs
    pyinstaller_args.extend([
        "--add-binary=venv/Lib/site-packages/PyQt5/Qt5/bin/Qt5Core.dll;PyQt5/Qt5/bin/",
        "--add-binary=venv/Lib/site-packages/PyQt5/Qt5/bin/Qt5Gui.dll;PyQt5/Qt5/bin/",
        "--add-binary=venv/Lib/site-packages/PyQt5/Qt5/bin/Qt5Widgets.dll;PyQt5/Qt5/bin/",
    ])
elif is_mac:
    # Add macOS-specific icon only if it exists
    icon_path = "app_icon.icns"
    if os.path.exists(icon_path):
        pyinstaller_args.append(f"--icon={icon_path}")
    
    pyinstaller_args.append("--osx-bundle-identifier=com.openscriber.openscriber")

# Add main script as the last argument
pyinstaller_args.append(MAIN_SCRIPT)

# Run PyInstaller
print("Building application with PyInstaller...")
subprocess.check_call([sys.executable, "-m", "PyInstaller"] + pyinstaller_args)

# Additional platform-specific post-processing
if is_mac:
    # Create a DMG for macOS
    print("Creating DMG file...")
    try:
        # Simple DMG creation using hdiutil
        dmg_file = f"dist/{APP_NAME}-{VERSION}.dmg"
        subprocess.check_call([
            "hdiutil", "create", 
            "-volname", APP_NAME, 
            "-srcfolder", f"dist/{APP_NAME}.app", 
            "-ov", "-format", "UDZO", 
            dmg_file
        ])
        print(f"DMG created at {dmg_file}")
    except Exception as e:
        print(f"Error creating DMG: {str(e)}")
        print("Creating DMG with dmgbuild instead...")
        # Alternative: use dmgbuild if available
        try:
            import dmgbuild
            settings = {
                'format': 'UDZO',
                'volume_name': APP_NAME,
                'files': [f"dist/{APP_NAME}.app"],
                'symlinks': {'Applications': '/Applications'},
                'icon_locations': {
                    f'{APP_NAME}.app': (100, 100),
                    'Applications': (300, 100)
                }
            }
            dmgbuild.build_dmg(f"dist/{APP_NAME}-{VERSION}.dmg", APP_NAME, settings)
            print(f"DMG created at dist/{APP_NAME}-{VERSION}.dmg")
        except Exception as e:
            print(f"Failed to create DMG with dmgbuild: {str(e)}")
            print("Please manually create a DMG from the app bundle.")

if is_windows:
    # For Windows, we may want to create an installer
    # This is a simple example using an NSIS template
    print("Note: For a professional Windows installer, consider using NSIS or Inno Setup")
    print(f"Executable created at dist/{APP_NAME}/{APP_NAME}.exe")

print("Build process completed!")