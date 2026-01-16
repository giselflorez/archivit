#!/usr/bin/env python3
"""
PWA Icon Generator for ARC-8
Generates all required icon sizes from a base design
"""

import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Note: Pillow not installed. Run: pip install Pillow")

# Icon sizes required for PWA
ICON_SIZES = [
    (72, 72),
    (96, 96),
    (128, 128),
    (144, 144),
    (152, 152),
    (180, 180),  # Apple touch icon
    (192, 192),
    (384, 384),
    (512, 512),
]

# Sacred palette colors
COLORS = {
    'void': '#030308',
    'gold': '#d4a574',
    'text': '#f0ece7',
}


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_icon(size, output_path, is_maskable=False):
    """Create a single icon at the specified size"""
    if not HAS_PIL:
        print(f"Skipping {output_path} - Pillow not installed")
        return

    width, height = size
    img = Image.new('RGBA', (width, height), hex_to_rgb(COLORS['void']) + (255,))
    draw = ImageDraw.Draw(img)

    # Calculate dimensions
    center = width // 2
    margin = width * 0.1 if is_maskable else width * 0.05

    # Draw outer ring
    ring_radius = (width // 2) - margin
    ring_width = max(2, width // 64)
    draw.ellipse(
        [center - ring_radius, center - ring_radius,
         center + ring_radius, center + ring_radius],
        outline=hex_to_rgb(COLORS['gold']),
        width=ring_width
    )

    # Draw center circle
    center_radius = width // 16
    draw.ellipse(
        [center - center_radius, center - center_radius,
         center + center_radius, center + center_radius],
        fill=hex_to_rgb(COLORS['gold'])
    )

    # Draw "8" text
    try:
        font_size = width // 4
        # Try to use Inter font, fall back to default
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            font = ImageFont.load_default()

        text = "8"
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Center the text
        x = center - text_width // 2
        y = center - text_height // 2 - (font_size // 8)

        draw.text((x, y), text, fill=hex_to_rgb(COLORS['text']), font=font)
    except Exception as e:
        print(f"Warning: Could not draw text - {e}")

    # Save the icon
    img.save(output_path, 'PNG')
    print(f"Created: {output_path}")


def main():
    """Generate all PWA icons"""
    # Create icons directory
    icons_dir = Path(__file__).parent.parent / 'public' / 'icons'
    icons_dir.mkdir(parents=True, exist_ok=True)

    print("Generating PWA icons...")
    print(f"Output directory: {icons_dir}")
    print()

    # Generate standard icons
    for size in ICON_SIZES:
        filename = f"icon-{size[0]}x{size[1]}.png"
        output_path = icons_dir / filename
        create_icon(size, output_path)

    # Generate maskable icon (512x512 with extra padding)
    create_icon((512, 512), icons_dir / 'maskable-512x512.png', is_maskable=True)

    # Generate Apple touch icon
    create_icon((180, 180), icons_dir / 'apple-touch-icon.png')

    # Generate favicon
    create_icon((32, 32), icons_dir / 'favicon-32x32.png')
    create_icon((16, 16), icons_dir / 'favicon-16x16.png')

    print()
    print("Icon generation complete!")
    print()
    print("Note: For production, replace these with professionally designed icons")
    print("that match the ARC-8 brand guidelines in the sacred palette.")


if __name__ == '__main__':
    main()
