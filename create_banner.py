#!/usr/bin/env python3
"""
Generate RedMess banner.png
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Create 800x200 banner
width, height = 800, 200
img = Image.new('RGB', (width, height), color='#0a0a0a')
draw = ImageDraw.Draw(img)

# Try to use a monospace font
try:
    font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 60)
    font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 20)
except:
    font_large = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Red accent color
red = '#ff0000'
gray = '#888888'

# Draw "RedMess" in center
text = "RedMess"
bbox = draw.textbbox((0, 0), text, font=font_large)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (width - text_width) // 2
y = 50

draw.text((x, y), text, fill=red, font=font_large)

# Draw tagline
tagline = "Red Team Reconnaissance & OSINT Suite"
bbox2 = draw.textbbox((0, 0), tagline, font=font_small)
tagline_width = bbox2[2] - bbox2[0]
x2 = (width - tagline_width) // 2
y2 = y + text_height + 20

draw.text((x2, y2), tagline, fill=gray, font=font_small)

# Add corner decorators
draw.rectangle([(0, 0), (5, 50)], fill=red)
draw.rectangle([(795, 0), (800, 50)], fill=red)
draw.rectangle([(0, 150), (5, 200)], fill=red)
draw.rectangle([(795, 150), (800, 200)], fill=red)

# Save
output_path = '/root/RedMess/banner.png'
img.save(output_path)
print(f"✓ Banner created: {output_path}")
