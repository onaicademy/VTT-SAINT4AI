"""
Create icon for VTT @SAINT4AI
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """Create app icon with microphone symbol."""
    sizes = [256, 128, 64, 48, 32, 16]
    images = []

    for size in sizes:
        # Create image with gradient background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw circular background
        padding = size // 16
        draw.ellipse(
            [padding, padding, size - padding, size - padding],
            fill=(45, 90, 39),  # Dark green
            outline=(60, 120, 50)
        )

        # Draw microphone symbol (simplified)
        center = size // 2
        mic_width = size // 4
        mic_height = size // 3

        # Microphone body
        draw.rounded_rectangle(
            [center - mic_width//2, size//4,
             center + mic_width//2, size//4 + mic_height],
            radius=mic_width//2,
            fill=(255, 255, 255)
        )

        # Microphone stand arc
        arc_size = size // 3
        draw.arc(
            [center - arc_size//2, size//3,
             center + arc_size//2, size//3 + arc_size],
            start=0, end=180,
            fill=(255, 255, 255),
            width=max(2, size//20)
        )

        # Stand line
        line_width = max(2, size//20)
        draw.line(
            [center, size//3 + arc_size//2, center, size - size//4],
            fill=(255, 255, 255),
            width=line_width
        )

        # Stand base
        base_width = size // 4
        draw.line(
            [center - base_width//2, size - size//4,
             center + base_width//2, size - size//4],
            fill=(255, 255, 255),
            width=line_width
        )

        images.append(img)

    # Save as ICO
    icon_path = 'icon.ico'
    images[0].save(
        icon_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )

    print(f"Icon created: {os.path.abspath(icon_path)}")

    # Also save PNG for preview
    images[0].save('icon.png', format='PNG')
    print(f"PNG preview: {os.path.abspath('icon.png')}")


if __name__ == "__main__":
    create_icon()
