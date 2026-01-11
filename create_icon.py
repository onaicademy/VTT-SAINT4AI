"""Create premium microphone icon for VTT"""
from PIL import Image, ImageDraw
import os

def create_premium_icon():
    """Create sleek premium icon with microphone."""
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2

    # Outer glow effect
    for i in range(15):
        alpha = int(40 - i * 2.5)
        r = 115 + i * 2
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(99, 102, 241, alpha))

    # Main dark circle
    r = 110
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(15, 15, 20, 255))

    # Inner gradient circle
    r = 102
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(22, 22, 28, 255))

    # Accent border
    r = 98
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(99, 102, 241, 200), width=2)

    # Microphone - premium design
    accent = (99, 102, 241, 255)  # Purple accent
    white = (255, 255, 255, 255)
    gray = (160, 160, 170, 255)

    # Mic body dimensions
    mic_w = 40
    mic_h = 75
    mic_top = cy - 50

    # Mic capsule (rounded rectangle effect)
    # Top ellipse
    draw.ellipse([cx - mic_w//2, mic_top, cx + mic_w//2, mic_top + mic_w], fill=accent)
    # Body
    draw.rectangle([cx - mic_w//2, mic_top + mic_w//2, cx + mic_w//2, mic_top + mic_h], fill=accent)
    # Bottom ellipse
    draw.ellipse([cx - mic_w//2, mic_top + mic_h - mic_w//2, cx + mic_w//2, mic_top + mic_h + mic_w//2], fill=accent)

    # Mic grille effect (horizontal lines)
    grille_color = (70, 72, 180, 255)
    for i in range(5):
        y = mic_top + 18 + i * 11
        draw.line([cx - 14, y, cx + 14, y], fill=grille_color, width=2)

    # Highlight on mic (shine effect)
    draw.line([cx - 12, mic_top + 12, cx - 12, mic_top + mic_h - 5], fill=(140, 142, 255, 150), width=3)

    # Stand arc
    arc_y = mic_top + mic_h + 12
    draw.arc([cx - 35, arc_y - 25, cx + 35, arc_y + 25], start=0, end=180, fill=gray, width=4)

    # Stand vertical
    stand_y = arc_y + 12
    draw.line([cx, stand_y, cx, stand_y + 28], fill=gray, width=4)

    # Stand base
    base_y = stand_y + 28
    draw.line([cx - 22, base_y, cx + 22, base_y], fill=gray, width=4)
    # Base feet
    draw.ellipse([cx - 25, base_y - 3, cx - 19, base_y + 3], fill=gray)
    draw.ellipse([cx + 19, base_y - 3, cx + 25, base_y + 3], fill=gray)

    # Save multi-size ICO
    sizes_list = [256, 128, 64, 48, 32, 16]
    images = [img.resize((s, s), Image.Resampling.LANCZOS) for s in sizes_list]

    images[0].save('icon.ico', format='ICO', sizes=[(s, s) for s in sizes_list], append_images=images[1:])
    img.save('icon.png', format='PNG')

    print(f"Premium icon created!")
    print(f"  ICO: {os.path.abspath('icon.ico')}")
    print(f"  PNG: {os.path.abspath('icon.png')}")

if __name__ == "__main__":
    create_premium_icon()
