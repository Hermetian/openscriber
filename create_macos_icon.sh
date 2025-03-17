#!/bin/bash
# Script to create a macOS .icns file from a source PNG

# Check if source file exists
SOURCE_PNG="app_icon.png"
if [ ! -f "$SOURCE_PNG" ]; then
    echo "Error: Source file $SOURCE_PNG not found."
    echo "Please run 'python create_icon.py' first to generate the PNG icon."
    exit 1
fi

# Create iconset directory
ICONSET_DIR="AppIcon.iconset"
mkdir -p "$ICONSET_DIR"

# Generate different sizes for the iconset
echo "Generating icons at different sizes..."
sips -z 16 16     "$SOURCE_PNG" --out "$ICONSET_DIR/icon_16x16.png"
sips -z 32 32     "$SOURCE_PNG" --out "$ICONSET_DIR/icon_16x16@2x.png"
sips -z 32 32     "$SOURCE_PNG" --out "$ICONSET_DIR/icon_32x32.png"
sips -z 64 64     "$SOURCE_PNG" --out "$ICONSET_DIR/icon_32x32@2x.png"
sips -z 128 128   "$SOURCE_PNG" --out "$ICONSET_DIR/icon_128x128.png"
sips -z 256 256   "$SOURCE_PNG" --out "$ICONSET_DIR/icon_128x128@2x.png"
sips -z 256 256   "$SOURCE_PNG" --out "$ICONSET_DIR/icon_256x256.png"
sips -z 512 512   "$SOURCE_PNG" --out "$ICONSET_DIR/icon_256x256@2x.png"
sips -z 512 512   "$SOURCE_PNG" --out "$ICONSET_DIR/icon_512x512.png"
sips -z 1024 1024 "$SOURCE_PNG" --out "$ICONSET_DIR/icon_512x512@2x.png"

# Convert iconset to icns file
echo "Converting iconset to icns file..."
iconutil -c icns "$ICONSET_DIR"

# Move to final location
mv "AppIcon.icns" "app_icon.icns"

# Clean up
rm -rf "$ICONSET_DIR"

echo "Successfully created app_icon.icns!"
echo "You can now run build_app.py to build your application." 