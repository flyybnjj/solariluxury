import os
from PIL import Image

def analyze(path):
    im = Image.open(path)
    im = im.convert('RGB')
    w, h = im.size
    # sample corners and center
    center = im.crop((w*0.25, h*0.25, w*0.75, h*0.75))
    stat = center.getextrema()
    print(f"{os.path.basename(path):35} {w}x{h} Extrema: {stat}")

print("=== CENTRAL CEE REAL PHOTOS ===")
analyze("scripts/raw_central_cee/central_cee_concert.jpg")
analyze("scripts/raw_central_cee/central_cee_wide.jpg")
analyze("scripts/raw_verified/central_cee_highsnobiety.jpg")
analyze("scripts/raw_verified/central_cee_jacquemus.jpg")
analyze("scripts/raw_verified/central_cee_fashion_poster.jpg")

print("\n=== TRAPSTAR REAL GARMENTS ===")
analyze("scripts/raw_verified/trapstar_irongate_puffer_official.jpg")
analyze("scripts/raw_verified/trapstar_decoded_puffer_2_0.png")
analyze("scripts/raw_verified/trapstar_decoded_aw23.png")
analyze("scripts/raw_verified/plugstation_puffer_4.webp")
analyze("scripts/raw_verified/plugstation_puffer_5.webp")
analyze("scripts/raw_verified/plugstation_puffer_7.webp")
analyze("scripts/raw_verified/plugstation_puffer_8.webp")
analyze("scripts/raw_verified/trapstar_tracksuit_depop_1.jpg")
analyze("scripts/raw_verified/trapstar_tracksuit_depop_2.jpg")
