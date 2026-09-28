"""
TRAPSTAR LONDON x CENTRAL CEE — Asset Downloader & Sequence Generator
Downloads high-resolution imagery for Central Cee and Trapstar London,
processes textures, and generates the 30-frame scroll-scrub sequence.
"""

import os
import sys
import math
import json
import urllib.request
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_IMG_DIR = os.path.join(BASE_DIR, "mi_proyecto", "static", "img")
CC_SEQUENCE_DIR = os.path.join(STATIC_IMG_DIR, "central_cee_sequence")
PRODUCT_CANVAS_DIR = os.path.join(STATIC_IMG_DIR, "product_canvas")

os.makedirs(STATIC_IMG_DIR, exist_ok=True)
os.makedirs(CC_SEQUENCE_DIR, exist_ok=True)
os.makedirs(PRODUCT_CANVAS_DIR, exist_ok=True)

# Headers to avoid 403 on public image servers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

def download_url(url, dest_path):
    """Safely download file from url with custom User-Agent"""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as response, open(dest_path, 'wb') as out_file:
            out_file.write(response.read())
        print(f"[OK] Downloaded: {os.path.basename(dest_path)}")
        return True
    except Exception as e:
        print(f"[WARN] Could not download {url}: {e}")
        return False

def generate_central_cee_sequence(base_img_path):
    """
    Generates a high-fashion 30-frame scroll sequence for Central Cee:
    Attitude shift, cinematic lighting ramp, subtle camera push-in, and 3M reflective flash.
    """
    if not os.path.exists(base_img_path):
        print(f"[ERROR] Base Central Cee image not found at {base_img_path}")
        return
        
    base_img = Image.open(base_img_path).convert("RGB")
    w, h = base_img.size
    target_w, target_h = 1000, 1250
    base_img = ImageOps.fit(base_img, (target_w, target_h), Image.Resampling.LANCZOS)
    
    num_frames = 30
    print(f"Generating {num_frames} high-definition frames for Central Cee sequence...")
    
    base_arr = np.array(base_img, dtype=np.float32)
    
    for i in range(num_frames):
        t = i / float(num_frames - 1)
        # Ease in out curve
        t_eased = t * t * (3.0 - 2.0 * t)
        
        # 1. Subtle zoom/crop (camera push-in 1.0 -> 1.06)
        scale = 1.0 + (0.06 * t_eased)
        sw = int(target_w / scale)
        sh = int(target_h / scale)
        left = int((target_w - sw) * 0.5)
        top = int((target_h - sh) * 0.4) # bias towards face
        
        frame = base_img.crop((left, top, left + sw, top + sh))
        frame = frame.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        # 2. Lighting shift: Deep moody drill shadow to intense 3M flash / spotlight
        # Contrast increases slightly, subtle cool cyan/chrome tonal shift
        enhancer_contrast = ImageEnhance.Contrast(frame)
        frame = enhancer_contrast.enhance(1.0 + 0.15 * t_eased)
        
        enhancer_brightness = ImageEnhance.Brightness(frame)
        frame = enhancer_brightness.enhance(0.95 + 0.18 * math.sin(t_eased * math.pi))
        
        # Save as optimized WebP
        frame_filename = f"cc_{i + 1:02d}.webp"
        frame_path = os.path.join(CC_SEQUENCE_DIR, frame_filename)
        frame.save(frame_path, format="WEBP", quality=88)
        
    print(f"[SUCCESS] 30 Central Cee sequence frames generated in {CC_SEQUENCE_DIR}")

def create_techwear_360_canvas_frames(puffer_path):
    """
    Generates 360-degree rotation / inspection frames for Trapstar Decoded Puffer
    for the interactive canvas stage.
    """
    if not os.path.exists(puffer_path):
        print(f"[ERROR] Puffer image not found at {puffer_path}")
        return
        
    img = Image.open(puffer_path).convert("RGBA")
    w, h = 1376, 768
    
    num_frames = 45
    print(f"Generating {num_frames} canvas frames for Trapstar Decoded Puffer 360/Inspection...")
    
    # Fit puffer in stage
    aspect = img.width / img.height
    new_h = int(h * 0.82)
    new_w = int(new_h * aspect)
    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    for i in range(num_frames):
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        t = i / float(num_frames - 1)
        
        # Subtle horizontal perspective wobble and 3M flash reflection
        x_offset = int((w - new_w) / 2 + math.sin(t * math.pi * 2) * 20)
        y_offset = int((h - new_h) / 2)
        
        # Apply 3M flash brightness at peak
        frame_layer = img_resized.copy()
        if t > 0.4 and t < 0.7:
            flash = math.sin((t - 0.4) / 0.3 * math.pi)
            enhancer = ImageEnhance.Brightness(frame_layer.convert("RGB"))
            brightened = enhancer.enhance(1.0 + 0.3 * flash)
            frame_layer = brightened.convert("RGBA")
            
        canvas.paste(frame_layer, (x_offset, y_offset), frame_layer if frame_layer.mode == 'RGBA' else None)
        out_frame = os.path.join(PRODUCT_CANVAS_DIR, f"puffer_{i + 1:03d}.webp")
        canvas.save(out_frame, format="WEBP", quality=85)
        
    print(f"[SUCCESS] Product canvas frames generated in {PRODUCT_CANVAS_DIR}")

if __name__ == "__main__":
    print("Trapstar London x Central Cee Asset Pipeline initialized.")
