#!/usr/bin/env python3
import os
import sys
import random
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_brooklyn_icon(output_path="app_icon.png", size=1024):
    """
    Create a Brooklyn-inspired icon for OpenScriber with authentic handcrafted vibes.
    
    Args:
        output_path: Path to save the PNG icon
        size: Size of the icon in pixels (square)
    """
    # Brooklyn-inspired color palette
    bg_colors = [
        (242, 231, 213),  # Vintage cream
        (217, 104, 49),   # Rust/brick
        (84, 11, 14),     # Deep burgundy
        (45, 41, 38),     # Dark espresso
        (74, 78, 105),    # Denim blue
    ]
    
    accent_colors = [
        (191, 86, 41),    # Burnt orange
        (20, 30, 40),     # Navy blue
        (171, 39, 79),    # Raspberry
        (241, 185, 48),   # Mustard yellow
        (26, 71, 42),     # Forest green
    ]
    
    # Choose colors
    bg_color = random.choice(bg_colors)
    accent_color = random.choice([c for c in accent_colors if c != bg_color])
    text_color = (240, 240, 240) if sum(bg_color) < 500 else (20, 20, 20)
    
    # Create base image with texture
    img = Image.new('RGB', (size, size), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Add subtle texture/noise
    for _ in range(size * size // 200):  # Reduced noise amount
        x = random.randint(0, size-1)
        y = random.randint(0, size-1)
        r, g, b = img.getpixel((x, y))
        noise = random.randint(-10, 10)  # Reduced noise intensity
        img.putpixel((x, y), (
            max(0, min(255, r + noise)),
            max(0, min(255, g + noise)),
            max(0, min(255, b + noise))
        ))
    
    # Add a distressed circle or geometric element
    style = random.choice(["circle", "diamond", "triangle", "hexagon"])
    
    if style == "circle":
        # Distressed circle
        padding = size * 0.1
        circle_size = size - (2 * padding)
        for i in range(5):  # Reduced number of circles
            offset = random.randint(-5, 5)  # Smaller offset
            draw.ellipse([
                padding + offset, 
                padding + offset, 
                padding + circle_size + offset, 
                padding + circle_size + offset
            ], outline=accent_color, width=max(3, size // 100))
    
    elif style == "diamond":
        # Diamond shape
        center = size // 2
        diamond_size = size * 0.4
        for i in range(3):  # Reduced number
            offset = random.randint(-5, 5)  # Smaller offset
            draw.polygon([
                (center + offset, center - diamond_size + offset),
                (center + diamond_size + offset, center + offset),
                (center + offset, center + diamond_size + offset),
                (center - diamond_size + offset, center + offset)
            ], outline=accent_color, width=max(3, size // 100))
    
    elif style == "triangle":
        # Triangle
        padding = size * 0.15
        for i in range(3):  # Reduced number
            offset_x = random.randint(-5, 5)  # Smaller offset
            offset_y = random.randint(-5, 5)
            draw.polygon([
                (size // 2 + offset_x, padding + offset_y),
                (padding + offset_x, size - padding + offset_y),
                (size - padding + offset_x, size - padding + offset_y)
            ], outline=accent_color, width=max(3, size // 100))
    
    else:  # hexagon
        # Hexagon
        center = size // 2
        radius = size * 0.4
        for i in range(3):  # Reduced number
            points = []
            offset_x = random.randint(-5, 5)  # Smaller offset
            offset_y = random.randint(-5, 5)
            for i in range(6):
                angle = math.pi / 3 * i
                x = center + radius * math.cos(angle) + offset_x
                y = center + radius * math.sin(angle) + offset_y
                points.append((x, y))
            draw.polygon(points, outline=accent_color, width=max(3, size // 100))
    
    # Try to load a hip handwritten or vintage font
    try:
        font_size = int(size * 0.35)  # Larger text
        try:
            # Try system fonts that might look good
            font_options = []
            if os.name == 'nt':  # Windows
                font_options = [
                    "Impact.ttf", 
                    "Gabriola.ttf",
                    "Georgia.ttf"
                ]
            elif sys.platform == 'darwin':  # macOS
                font_options = [
                    "/Library/Fonts/Chalkduster.ttf",
                    "/Library/Fonts/AmericanTypewriter.ttc",
                    "/Library/Fonts/Futura.ttc",
                    "/Library/Fonts/MarkerFelt.ttc"
                ]
            else:  # Linux
                font_options = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                ]
            
            # Try fonts until one works
            font = None
            for font_path in font_options:
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except OSError:
                    continue
                    
            # If none worked, fall back to default
            if font is None:
                font = ImageFont.load_default()
                font_size = int(size * 0.3)
        except OSError:
            font = ImageFont.load_default()
            font_size = int(size * 0.3)
    except Exception as e:
        print(f"Font error: {e}")
        # If all fails, use a simple shape and return early
        center = size // 2
        radius = size * 0.3
        draw.ellipse([
            center - radius, 
            center - radius, 
            center + radius, 
            center + radius
        ], fill=accent_color)
        img.save(output_path)
        print(f"Created a simple icon at {output_path}")
        return
    
    # Draw the text directly onto the image
    text = "OS"
    
    # Calculate text position (centered)
    try:
        # For newer Pillow versions
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        text_width = right - left
        text_height = bottom - top
        position = ((size - text_width) / 2 - left, (size - text_height) / 2 - top)
    except AttributeError:
        # For older Pillow versions
        text_width = font_size
        text_height = font_size
        position = ((size - text_width) / 2, (size - text_height) / 2)
    
    # Add a subtle shadow for depth
    shadow_offset = max(2, size // 200)
    shadow_color = tuple(max(0, c - 60) for c in bg_color)  # Darker version of bg color
    draw.text((position[0] + shadow_offset, position[1] + shadow_offset), text, font=font, fill=shadow_color)
    
    # Draw main text
    draw.text(position, text, font=font, fill=text_color)
    
    # Apply slight blur for a softer look (optional)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    img = img.filter(ImageFilter.SHARPEN)  # Then sharpen to keep details
    
    # Save the icon
    img.save(output_path)
    print(f"Created Brooklyn-inspired icon at {output_path}")
    
    # Instructions for converting to platform-specific formats
    print("\nTo convert to platform-specific formats:")
    if sys.platform == 'darwin':
        print("For macOS (.icns):")
        print("1. Run the create_macos_icon.sh script:")
        print("   chmod +x create_macos_icon.sh")
        print("   ./create_macos_icon.sh")
    else:
        print("For Windows (.ico):")
        print("1. Install the pillow library if not already installed:")
        print("   pip install pillow")
        print("2. Run the following Python code:")
        print("   from PIL import Image")
        print("   img = Image.open('app_icon.png')")
        print("   img.save('app_icon.ico')")

if __name__ == "__main__":
    # Create directories for icons if they don't exist
    if not os.path.exists("resources"):
        os.makedirs("resources")
    
    # Create multiple options
    num_options = 3
    print(f"Generating {num_options} Brooklyn-style icon options...")
    
    for i in range(num_options):
        if i == 0:
            output_path = "app_icon.png"
        else:
            output_path = f"app_icon_option_{i}.png"
        
        create_brooklyn_icon(output_path=output_path)
    
    # Attempt to convert main option to platform-specific format automatically
    try:
        from PIL import Image
        img = Image.open("app_icon.png")
        
        if sys.platform == 'darwin':  # macOS
            # Can't create icns directly with PIL, use the shell script
            pass
        else:  # Windows
            img.save("app_icon.ico")
            print("Successfully created app_icon.ico")
    except Exception as e:
        print(f"Could not automatically convert icon: {e}")
        print("Please follow the manual instructions above.") 