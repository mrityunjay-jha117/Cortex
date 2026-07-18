"""
scripts/generate_icon.py — Generates a placeholder icon.ico for the EXE.

Run this once if you don't have a custom icon:
    python scripts/generate_icon.py

For production, replace assets/icon.ico with a proper 256x256 ICO file.
"""

import os
import struct

def create_placeholder_ico(output_path: str = "cognitive_automator/assets/icon.ico") -> None:
    """Generate a minimal valid ICO file with a purple 'CA' icon."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        from PIL import Image, ImageDraw, ImageFont
        sizes = [16, 32, 48, 64, 128, 256]
        images = []
        for size in sizes:
            img = Image.new("RGBA", (size, size), (123, 97, 255, 255))
            draw = ImageDraw.Draw(img)
            # Draw a simple 'CA' text
            font_size = max(size // 3, 6)
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()
            text = "CA"
            bbox = draw.textbbox((0, 0), text, font=font)
            tx = (size - (bbox[2] - bbox[0])) // 2
            ty = (size - (bbox[3] - bbox[1])) // 2
            draw.text((tx, ty), text, fill=(255, 255, 255, 255), font=font)
            images.append(img)

        images[0].save(output_path, format="ICO", sizes=[(s, s) for s in sizes])
        print(f"[OK] Icon generated: {output_path}")

    except ImportError:
        # PIL not available — write a minimal valid ICO (16x16 solid purple)
        _write_minimal_ico(output_path)
        print(f"[OK] Minimal placeholder icon written: {output_path}")


def _write_minimal_ico(path: str) -> None:
    """Write a minimal 16x16 ICO file without PIL."""
    size = 16
    # BMP header for 16x16 BGRA icon
    pixels = bytes([123, 97, 255, 255] * size * size)  # BGRA purple
    bmp_header = struct.pack("<IiiHHIIiiII",
        40, size, size * 2, 1, 32, 0, len(pixels), 0, 0, 0, 0)
    mask = bytes([0x00] * (size * size // 8))
    image_data = bmp_header + pixels + mask

    ico_header = struct.pack("<HHH", 0, 1, 1)
    ico_dir_entry = struct.pack("<BBBBHHII",
        size, size, 0, 0, 1, 32, len(image_data), 22)

    with open(path, "wb") as f:
        f.write(ico_header + ico_dir_entry + image_data)


if __name__ == "__main__":
    create_placeholder_ico()
