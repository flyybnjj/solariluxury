"""
PROCESS AND DEPLOY 100% REAL PHOTOGRAPHY ASSETS
Replaces all placeholder/AI imagery with authentic photography:
- Real Central Cee Highsnobiety photoshoot
- Real Central Cee Jacquemus campaign
- Real Central Cee concert photography
- Real Trapstar Decoded 2.0 Puffer Jacket packshots
- Real Trapstar 3M Reflective Back Arch packshot
- Real Trapstar Chenille Macro Texture
- Real Trapstar Shooters Tracksuit
- Generates 30-frame cinematic scrub sequence from authentic photography
- Copies everything to docs/ and syncs with export_gh_pages.py
"""

import os
import sys
import shutil
import numpy as np
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_IMG = os.path.join(BASE_DIR, "mi_proyecto", "static", "img")
SEQ_DIR = os.path.join(STATIC_IMG, "central_cee_sequence")
DOCS_STATIC_IMG = os.path.join(BASE_DIR, "docs", "static", "img")
DOCS_SEQ_DIR = os.path.join(DOCS_STATIC_IMG, "central_cee_sequence")

os.makedirs(STATIC_IMG, exist_ok=True)
os.makedirs(SEQ_DIR, exist_ok=True)
os.makedirs(DOCS_STATIC_IMG, exist_ok=True)
os.makedirs(DOCS_SEQ_DIR, exist_ok=True)

RAW_VERIFIED = os.path.join(BASE_DIR, "scripts", "raw_verified")
RAW_CC = os.path.join(BASE_DIR, "scripts", "raw_central_cee")

def composite_on_dark(im, bg_color=(6, 6, 8), threshold=15.0, softness=12.0):
    """Cleanly segment a light studio packshot and composite onto deep obsidian background"""
    im_rgb = im.convert('RGB')
    arr = np.array(im_rgb, dtype=np.float32)
    
    # Estimate background from corners
    corner_samples = np.concatenate([
        arr[:15, :15, :].reshape(-1, 3),
        arr[:15, -15:, :].reshape(-1, 3)
    ], axis=0)
    bg_sample = np.mean(corner_samples, axis=0)
    
    dist = np.linalg.norm(arr - bg_sample, axis=2)
    alpha = np.clip((dist - threshold) / softness, 0.0, 1.0) * 255.0
    alpha_im = Image.fromarray(alpha.astype(np.uint8), mode='L')
    alpha_im = alpha_im.filter(ImageFilter.GaussianBlur(radius=0.7))
    
    # Dark gradient background with subtle center lighting
    w, h = im.size
    bg = Image.new('RGB', (w, h), bg_color)
    
    return Image.composite(im_rgb, bg, alpha_im)

def process_images():
    print("=== 1. PROCESSING MAIN REAL PHOTOGRAPHY ASSETS ===")
    
    # 1. Central Cee Front (Highsnobiety Photoshoot)
    cc_high = Image.open(os.path.join(RAW_VERIFIED, "central_cee_highsnobiety.jpg")).convert('RGB')
    cc_front = ImageOps.fit(cc_high, (900, 1200), Image.Resampling.LANCZOS, centering=(0.5, 0.35))
    cc_front = ImageEnhance.Contrast(cc_front).enhance(1.08)
    cc_front.save(os.path.join(STATIC_IMG, "central_cee_front.jpg"), quality=95)
    print("  [OK] central_cee_front.jpg (Real Highsnobiety Shoot)")

    # 2. Central Cee Tilt / Secondary (Jacquemus Campaign)
    cc_jacq = Image.open(os.path.join(RAW_VERIFIED, "central_cee_jacquemus.jpg")).convert('RGB')
    cc_tilt = ImageOps.fit(cc_jacq, (900, 1200), Image.Resampling.LANCZOS, centering=(0.5, 0.3))
    cc_tilt = ImageEnhance.Contrast(cc_tilt).enhance(1.06)
    cc_tilt.save(os.path.join(STATIC_IMG, "central_cee_tilt.jpg"), quality=95)
    print("  [OK] central_cee_tilt.jpg (Real Jacquemus Campaign)")

    # 3. Central Cee Street / Concert (Concert Photography)
    cc_conc = Image.open(os.path.join(RAW_CC, "central_cee_concert.jpg")).convert('RGB')
    cc_street = ImageOps.fit(cc_conc, (1200, 800), Image.Resampling.LANCZOS, centering=(0.5, 0.4))
    cc_street = ImageEnhance.Contrast(cc_street).enhance(1.05)
    cc_street.save(os.path.join(STATIC_IMG, "central_cee_street.jpg"), quality=95)
    print("  [OK] central_cee_street.jpg (Real Live Concert Photography)")

    # 4. Real Trapstar Decoded 2.0 Puffer Hero (NoSauceThePlug packshot composited on dark studio)
    puffer_raw = Image.open(os.path.join(RAW_VERIFIED, "trapstar_decoded_puffer_2_0.png"))
    puffer_dark = composite_on_dark(puffer_raw, bg_color=(7, 7, 10), threshold=12.0, softness=14.0)
    puffer_hero = ImageOps.fit(puffer_dark, (1200, 1200), Image.Resampling.LANCZOS)
    puffer_hero = ImageEnhance.Contrast(puffer_hero).enhance(1.06)
    puffer_hero.save(os.path.join(STATIC_IMG, "trapstar_puffer_hero.jpg"), quality=95)
    print("  [OK] trapstar_puffer_hero.jpg (Real Decoded Puffer 2.0 Packshot)")

    # 5. Real Trapstar 3M Reflective Flash (Plugstation 7 Back 3M Arch)
    puffer_3m_raw = Image.open(os.path.join(RAW_VERIFIED, "plugstation_puffer_7.webp"))
    puffer_3m_dark = composite_on_dark(puffer_3m_raw, bg_color=(7, 7, 10), threshold=10.0, softness=12.0)
    puffer_3m = ImageOps.fit(puffer_3m_dark, (1200, 1200), Image.Resampling.LANCZOS)
    puffer_3m = ImageEnhance.Contrast(puffer_3m).enhance(1.12)
    puffer_3m.save(os.path.join(STATIC_IMG, "trapstar_3m_flash.jpg"), quality=95)
    print("  [OK] trapstar_3m_flash.jpg (Real 3M Reflective Arch Back Packshot)")

    # 6. Real Trapstar Chenille Texture Macro (Plugstation 5 Macro)
    chen_raw = Image.open(os.path.join(RAW_VERIFIED, "plugstation_puffer_5.webp")).convert('RGB')
    chen_macro = ImageOps.fit(chen_raw, (1200, 1200), Image.Resampling.LANCZOS)
    chen_macro = ImageEnhance.Contrast(chen_macro).enhance(1.15)
    chen_macro.save(os.path.join(STATIC_IMG, "trapstar_chenille_texture.jpg"), quality=95)
    print("  [OK] trapstar_chenille_texture.jpg (Real Chenille Macro Texture)")

    # 7. Real Trapstar Puffer Open / Lining (Plugstation 8 Lining)
    open_raw = Image.open(os.path.join(RAW_VERIFIED, "plugstation_puffer_8.webp")).convert('RGB')
    open_img = ImageOps.fit(open_raw, (1200, 1200), Image.Resampling.LANCZOS)
    open_img = ImageEnhance.Contrast(open_img).enhance(1.05)
    open_img.save(os.path.join(STATIC_IMG, "trapstar_puffer_open.jpg"), quality=95)
    print("  [OK] trapstar_puffer_open.jpg (Real Collar/Lining Packshot)")

    # 8. Real Trapstar Shooters Tracksuit (Depop Tracksuit 1)
    track_raw = Image.open(os.path.join(RAW_VERIFIED, "trapstar_tracksuit_depop_1.jpg")).convert('RGB')
    track_img = ImageOps.fit(track_raw, (1200, 1200), Image.Resampling.LANCZOS)
    track_img = ImageEnhance.Contrast(track_img).enhance(1.08)
    track_img.save(os.path.join(STATIC_IMG, "trapstar_tracksuit.jpg"), quality=95)
    print("  [OK] trapstar_tracksuit.jpg (Real Trapstar Shooters Grey Tracksuit)")

def generate_30_frame_sequence():
    print("\n=== 2. GENERATING 30-FRAME CENTRAL CEE SEQUENCE FROM REAL PHOTOGRAPHY ===")
    src_im = Image.open(os.path.join(RAW_VERIFIED, "central_cee_highsnobiety.jpg")).convert('RGB')
    w_orig, h_orig = src_im.size
    
    target_w, target_h = 900, 1200
    total_frames = 30
    
    # Face center coordinate in original image (approx 0.5 horizontal, 0.35 vertical)
    cx, cy = w_orig * 0.50, h_orig * 0.36
    
    for i in range(1, total_frames + 1):
        t = (i - 1) / (total_frames - 1)  # 0.0 to 1.0
        
        # Smooth camera push-in zoom: from 1.0 to 1.32
        zoom = 1.0 + 0.32 * (t ** 1.3)
        
        # Crop box based on zoom centered on Central Cee
        crop_w = w_orig / zoom
        crop_h = (crop_w * (target_h / target_w))
        
        # Shift slightly downwards into intense portrait focus
        shift_y = (t * 0.04) * h_orig
        
        x1 = max(0, cx - crop_w / 2)
        y1 = max(0, cy - crop_h / 2 + shift_y)
        x2 = min(w_orig, x1 + crop_w)
        y2 = min(h_orig, y1 + crop_h)
        
        # Adjust if boundaries exceed
        if x2 - x1 < crop_w:
            x1 = max(0, x2 - crop_w)
        if y2 - y1 < crop_h:
            y1 = max(0, y2 - crop_h)
            
        frame = src_im.crop((x1, y1, x2, y2))
        frame = frame.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        # Subtle atmospheric lighting progression:
        # Initial frames: clear cold daylight -> later frames: deep contrast & vignette
        contrast = 1.05 + 0.12 * t
        brightness = 1.0 - 0.08 * t
        frame = ImageEnhance.Contrast(frame).enhance(contrast)
        frame = ImageEnhance.Brightness(frame).enhance(brightness)
        
        # Save as WebP
        filename = f"cc_{str(i).padStart(2, '0') if hasattr(str(i), 'padStart') else str(i).zfill(2)}.webp"
        out_path = os.path.join(SEQ_DIR, filename)
        frame.save(out_path, format="WEBP", quality=90)
        
    print(f"  [OK] Generated {total_frames} frames in {SEQ_DIR}")

def sync_to_docs():
    print("\n=== 3. SYNCING REAL ASSETS TO DOCS STATIC DIRECTORY ===")
    for fname in os.listdir(STATIC_IMG):
        src = os.path.join(STATIC_IMG, fname)
        if os.path.isfile(src):
            dst = os.path.join(DOCS_STATIC_IMG, fname)
            shutil.copy2(src, dst)
            
    for fname in os.listdir(SEQ_DIR):
        src = os.path.join(SEQ_DIR, fname)
        if os.path.isfile(src):
            dst = os.path.join(DOCS_SEQ_DIR, fname)
            shutil.copy2(src, dst)
            
    print(f"  [OK] Synced all assets and sequence frames to docs/static/img")

if __name__ == "__main__":
    process_images()
    generate_30_frame_sequence()
    sync_to_docs()
    print("\nAll assets processed and synced successfully!")
