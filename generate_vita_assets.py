#!/usr/bin/env python3
"""Generate Vita placeholder assets using Pillow."""

from PIL import Image, ImageDraw, ImageFont
import os

# Create directory structure first
os.makedirs('platform/vita/sce_sys/livearea/contents', exist_ok=True)

# 1. icon0.png: 128x128 — app icon
icon = Image.new('RGB', (128, 128), color='#0066cc')
draw = ImageDraw.Draw(icon)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
except:
    font = ImageFont.load_default()
text = "SM64\nDS-R"
draw.multiline_text((64, 64), text, fill='white', font=font, anchor='mm', align='center')
icon.save('platform/vita/sce_sys/icon0.png', 'PNG')
print("Created platform/vita/sce_sys/icon0.png")

# 2. bg0.png: 840x500 — livearea background
bg = Image.new('RGB', (840, 500), color='#003366')
bg.save('platform/vita/sce_sys/livearea/contents/bg0.png', 'PNG')
print("Created platform/vita/sce_sys/livearea/contents/bg0.png")

# 3. startup.png: 280x158 — livearea startup icon
startup = Image.new('RGB', (280, 158), color='#004488')
startup.save('platform/vita/sce_sys/livearea/contents/startup.png', 'PNG')
print("Created platform/vita/sce_sys/livearea/contents/startup.png")
