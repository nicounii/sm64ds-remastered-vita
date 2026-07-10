#!/usr/bin/env python3
"""Generate PS Vita LiveArea assets from Super Mario 64 DS artwork.

Produces 8-bit indexed PNGs compatible with PS Vita (fixes error 0x8010113D).
Downloads official SM64DS artwork from pidgi.net if not already cached.
"""

from PIL import Image, ImageDraw, ImageFilter
import os
import urllib.request
import shutil

CACHE_DIR = '/tmp/sm64ds_artwork'
ASSET_DIR = 'platform/vita/sce_sys'
LIVEAREA_DIR = os.path.join(ASSET_DIR, 'livearea/contents')

# Artwork URLs (from pidgi.net, CC-BY-SA)
URLS = {
    'logo.jpg': 'https://cdn.pidgi.net/images/e/e9/Logo_EN_-_Super_Mario_64_DS.jpg',
    'mario.png': 'https://cdn.pidgi.net/images/4/47/Mario_-_Super_Mario_64_DS.png',
    'group.png': 'https://cdn.pidgi.net/images/8/83/Group_-_Super_Mario_64_DS.png',
}


def ensure_dirs():
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(LIVEAREA_DIR, exist_ok=True)


def download_artwork():
    """Download artwork if not already cached."""
    for name, url in URLS.items():
        path = os.path.join(CACHE_DIR, name)
        if not os.path.exists(path):
            print(f"Downloading {name}...")
            urllib.request.urlretrieve(url, path)
            print(f"  -> saved {path}")
        else:
            print(f"  {name} already cached")


def quantize_png(img, colors=256, keep_alpha=False):
    """Convert image to 8-bit indexed PNG (Vita-compatible).

    Vita requires 8-bit colormap PNGs (color type 3). For alpha,
    we use key-color transparency via tRNS chunk (single transparent color).
    """
    if keep_alpha and img.mode == 'RGBA':
        # To preserve alpha in indexed PNG: composite over a dark color first,
        # then use that color as the transparent key via tRNS: quantize, then
        # remap fully-transparent pixels to index 0 and set tRNS[0]=0.
        r, g, b, a = img.split()
        # Create RGB from non-transparent pixels; transparent->black
        rgb = Image.merge('RGB', (r, g, b))
        quant_rgb = rgb.quantize(colors=min(colors, 255), method=Image.Quantize.MEDIANCUT)
        # Build a palette with index 0 = transparent key (black, 0,0,0)
        pal = list(quant_rgb.palette.palette)
        # Create output where transparent pixels map to index 0
        quant = Image.new('P', img.size)
        quant.putpalette(pal)
        # Copy quantized values
        quant_data = list(quant_rgb.getdata())
        alpha_data = list(a.getdata())
        # Force index 0 where alpha is 0
        new_data = []
        for q_val, alpha_val in zip(quant_data, alpha_data):
            if alpha_val < 128:
                new_data.append(0)
            else:
                new_data.append(q_val)
        quant.putdata(new_data)
        # Ensure palette[0] = a very dark color that won't appear elsewhere
        pal_list = list(quant.palette.palette)
        pal_list[0:3] = [0, 0, 0]
        while len(pal_list) < 768:
            pal_list.extend([0, 0, 0])
        quant.putpalette(pal_list)
        # Tag: index 0 is transparent
        quant.info['transparency'] = 0
        return quant
    elif img.mode in ('RGBA', 'LA'):
        # Strip alpha, composite over black, then quantize
        if img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, (0, 0, 0))
            bg.paste(img, mask=img.split()[3])
            return bg.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
        else:
            l, a = img.split()
            bg = Image.new('L', img.size, 0)
            bg.paste(l, mask=a)
            return bg.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    elif img.mode == 'RGB':
        return img.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    elif img.mode == 'P':
        if hasattr(img, 'palette') and img.palette.mode == 'RGBA':
            return img.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
        return img
    else:
        rgb = img.convert('RGB')
        return rgb.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)


def save_vita_png(img, path, keep_alpha=False):
    """Save as Vita-compatible 8-bit indexed PNG.
    
    Args:
        img: PIL Image to save
        path: output path
        keep_alpha: True for startup.png (preserve transparency via tRNS),
                    False for icon0/bg0 (strip alpha, use flat quantize)
    """
    quant = quantize_png(img, keep_alpha=keep_alpha)
    quant.save(path, 'PNG', transparency=quant.info.get('transparency', None))
    size_kb = os.path.getsize(path) / 1024
    print(f"  -> saved {path} ({quant.size[0]}x{quant.size[1]}, {quant.mode}, {size_kb:.1f} KB)")


def create_icon0():
    """Create 128x128 app icon — Mario face cropped from artwork."""
    mario_path = os.path.join(CACHE_DIR, 'mario.png')
    mario = Image.open(mario_path).convert('RGBA')

    # Crop to Mario's face area (center-top portion)
    w, h = mario.size
    # Mario's face is roughly in the top-center third
    face_box = (w * 0.25, h * 0.05, w * 0.75, h * 0.55)
    face = mario.crop(face_box)

    # Resize to 128x128
    icon = face.resize((128, 128), Image.LANCZOS)

    path = os.path.join(ASSET_DIR, 'icon0.png')
    save_vita_png(icon, path, keep_alpha=False)
    return icon


def create_bg0_polygon():
    """Create bg0 as a styled SM64-themed background using game textures."""
    # 840x500 LiveArea background
    bg = Image.new('RGB', (840, 500), color='#1a0a2e')

    draw = ImageDraw.Draw(bg)

    # Gradient-like effect with stars
    import random
    random.seed(42)
    for _ in range(80):
        x = random.randint(0, 839)
        y = random.randint(0, 499)
        r = random.randint(1, 3)
        brightness = random.randint(100, 255)
        draw.ellipse([x - r, y - r, x + r, y + r],
                     fill=(brightness, brightness, brightness))

    return bg


def create_bg0():
    """Create 840x500 LiveArea background with SM64DS style."""
    # SM64DS theme: dark background with characters
    bg = Image.new('RGB', (840, 500), color='#0d0d2b')

    # Group artwork as backdrop
    group_path = os.path.join(CACHE_DIR, 'group.png')
    group = Image.open(group_path).convert('RGBA')
    
    # Scale group to fill width, maintain aspect
    group.thumbnail((840, 420), Image.LANCZOS)
    gw, gh = group.size

    # Semi-transparent overlay
    r, g, b, a = group.split()
    a = a.point(lambda x: int(x * 0.35))
    group_t = Image.merge('RGBA', (r, g, b, a))
    
    bg_rgba = bg.convert('RGBA')
    bg_rgba.paste(group_t, ((840 - gw) // 2, 500 - gh - 10), group_t)
    bg = bg_rgba.convert('RGB')

    # Logo on the top
    logo_path = os.path.join(CACHE_DIR, 'logo.jpg')
    logo = Image.open(logo_path).convert('RGBA')
    
    # Scale logo to fit width
    logo.thumbnail((700, 300), Image.LANCZOS)
    lw, lh = logo.size

    # Create white-background version of logo
    logo_rgb = Image.new('RGB', logo.size, (255, 255, 255))
    logo_rgb.paste(logo, mask=logo.split()[3] if logo.mode == 'RGBA' else None)
    
    # Position logo at top
    logo_x = (840 - lw) // 2
    logo_y = 30
    bg.paste(logo_rgb, (logo_x, logo_y))
    
    # Add "REMASTERED" subtitle text below logo
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    draw = ImageDraw.Draw(bg)
    # Semi-transparent bar behind text
    bar_y = logo_y + lh + 15
    draw.rectangle([(0, bar_y - 5), (840, bar_y + 50)], fill=(0, 0, 0, 128) if hasattr(Image, 'alpha') else '#00000088')
    draw.text((420, bar_y + 20), "PS VITA PORT", fill='#ffcc00', font=font, anchor='mt')

    return bg


def create_startup():
    """Create 280x158 startup/boot image."""
    # Use logo + Mario
    bg = Image.new('RGBA', (280, 158), (0, 0, 0, 0))

    # Logo
    logo_path = os.path.join(CACHE_DIR, 'logo.jpg')
    logo = Image.open(logo_path).convert('RGBA')
    logo.thumbnail((250, 110), Image.LANCZOS)
    lw, lh = logo.size

    # White bg for the jpg logo
    logo_rgb = Image.new('RGB', logo.size, (255, 255, 255))
    logo_rgb.paste(logo, mask=logo.split()[3] if logo.mode == 'RGBA' else None)

    # Place logo
    bg.paste(logo_rgb, ((280 - lw) // 2, 10))

    # Subtitle
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except:
        font = ImageFont.load_default()

    draw = ImageDraw.Draw(bg)
    draw.text((140, lh + 20), "REMASTERED", fill='#ffcc00', font=font, anchor='mt')

    # Add small Mario head from game textures
    mario_head_path = os.path.join(os.path.dirname(__file__), 'textures/hud/hud_mario_head.rgba16.png')
    try:
        head = Image.open(mario_head_path).convert('RGBA')
        head = head.resize((32, 32), Image.NEAREST)
        bg.paste(head, (140 - 16, 158 - 38), head)
    except Exception:
        pass

    path = os.path.join(LIVEAREA_DIR, 'startup.png')
    save_vita_png(bg, path, keep_alpha=True)
    return bg


def create_bg0_fallback():
    """Fallback bg0 if the artwork download fails."""
    bg = Image.new('RGB', (840, 500), color='#0d0d2b')
    draw = ImageDraw.Draw(bg)

    # Draw simple stars
    import random
    random.seed(42)
    for _ in range(100):
        x = random.randint(0, 839)
        y = random.randint(0, 499)
        r = random.randint(1, 3)
        c = random.randint(100, 255)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(c, c, c))

    # Try to add at least the logo
    try:
        logo_path = os.path.join(CACHE_DIR, 'logo.jpg')
        if os.path.exists(logo_path):
            logo = Image.open(logo_path)
            logo.thumbnail((700, 300), Image.LANCZOS)
            lw, lh = logo.size
            bg.paste(logo, ((840 - lw) // 2, 30))
    except Exception:
        pass

    return bg


def main():
    ensure_dirs()

    # Step 1: Download SM64DS artwork
    print("=== Downloading SM64DS artwork ===")
    download_artwork()

    # Step 2: Generate Vita bubble assets
    print("\n=== Generating icon0.png (128x128 app icon) ===")
    try:
        create_icon0()
    except Exception as e:
        print(f"  ERROR creating icon0: {e}")
        # Fallback: simple blue icon with text
        icon = Image.new('RGB', (128, 128), color='#e31f1f')
        draw = ImageDraw.Draw(icon)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        except:
            font = ImageFont.load_default()
        draw.text((64, 64), "SM64\nDS-R", fill='white', font=font, anchor='mm', align='center')
        save_vita_png(icon, os.path.join(ASSET_DIR, 'icon0.png'), keep_alpha=False)

    print("\n=== Generating bg0.png (840x500 LiveArea background) ===")
    try:
        bg = create_bg0()
        save_vita_png(bg, os.path.join(LIVEAREA_DIR, 'bg0.png'), keep_alpha=False)
    except Exception as e:
        print(f"  ERROR creating bg0: {e}")
        bg = create_bg0_fallback()
        save_vita_png(bg, os.path.join(LIVEAREA_DIR, 'bg0.png'), keep_alpha=False)

    print("\n=== Generating startup.png (280x158 boot image) ===")
    try:
        create_startup()
    except Exception as e:
        print(f"  ERROR creating startup: {e}")
        startup = Image.new('RGBA', (280, 158), (0, 0, 0, 0))
        save_vita_png(startup, os.path.join(LIVEAREA_DIR, 'startup.png'), keep_alpha=True)

    print("\n=== All Vita assets generated! ===")
    for f in ['icon0.png', 'livearea/contents/bg0.png', 'livearea/contents/startup.png',
              'livearea/contents/template.xml']:
        path = os.path.join(ASSET_DIR, f)
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"  {path}: {size / 1024:.1f} KB")
        else:
            print(f"  {path}: MISSING!")


if __name__ == '__main__':
    main()
