import os
import re
import json
import urllib.request
import urllib.parse
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_IMG = os.path.join(BASE_DIR, "mi_proyecto", "static", "img")
os.makedirs(STATIC_IMG, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
}

def search_ddg_images(query, max_results=10):
    try:
        req = urllib.request.Request(f'https://duckduckgo.com/?q={urllib.parse.quote(query)}', headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        
        vqd_match = re.search(r'vqd=([0-9-]+)', html) or re.search(r'vqd=["\']?([0-9-]+)', html)
        if not vqd_match:
            return []
        vqd = vqd_match.group(1)
        
        api_url = f'https://duckduckgo.com/i.js?l=us-en&o=json&q={urllib.parse.quote(query)}&vqd={vqd}&f=,,,&p=1'
        req2 = urllib.request.Request(api_url, headers=HEADERS)
        with urllib.request.urlopen(req2, timeout=10) as resp2:
            data = json.loads(resp2.read().decode('utf-8'))
            return [r.get('image') for r in data.get('results', []) if r.get('image')]
    except Exception as e:
        print(f"Error {query}: {e}")
        return []

targets = [
    ("central cee syna world outfit pinterest", "cc_look_01_syna.jpg"),
    ("central cee trapstar jacket photoshoot high quality", "cc_look_02_trapstar.jpg"),
    ("central cee jacquemus front row sunglasses", "cc_look_03_jacquemus.jpg"),
    ("central cee highsnobiety editorial photoshoot", "cc_look_04_highsnobiety.jpg"),
    ("central cee nike tech fleece black aesthetic", "cc_look_05_nike_tech.jpg"),
    ("central cee london street style denim balaclava", "cc_look_06_balaclava.jpg"),
    ("central cee jewelry chain diamond close up", "cc_look_07_diamond_chain.jpg"),
    ("central cee concert stage live microphone", "cc_look_08_live_concert.jpg"),
    ("central cee studio portrait headphones bape", "cc_look_09_studio_bape.jpg"),
    ("central cee sunglasses beanie syna world logo", "cc_look_10_beanie_syna.jpg"),
]

print("=== BUSCANDO Y DESCARGANDO IMÁGENES DE ALTA CALIDAD PARA EL CARRUSEL ===")

for q, out_filename in targets:
    out_path = os.path.join(STATIC_IMG, out_filename)
    imgs = search_ddg_images(q, max_results=8)
    saved = False
    for img_url in imgs:
        try:
            req_img = urllib.request.Request(img_url, headers=HEADERS)
            with urllib.request.urlopen(req_img, timeout=8) as r:
                data = r.read()
                if len(data) < 25000:  # Skip tiny thumbnails
                    continue
                temp_path = out_path + ".tmp"
                with open(temp_path, "wb") as f:
                    f.write(data)
                
                with Image.open(temp_path) as im:
                    im = im.convert("RGB")
                    # Resize to portrait 800x1000 with clean crop
                    w, h = im.size
                    if w < 300 or h < 300:
                        continue
                    # Crop center to 4:5 ratio
                    target_ratio = 4.0 / 5.0
                    current_ratio = w / h
                    if current_ratio > target_ratio:
                        new_w = int(h * target_ratio)
                        offset = (w - new_w) // 2
                        im = im.crop((offset, 0, offset + new_w, h))
                    else:
                        new_h = int(w / target_ratio)
                        offset = (h - new_h) // 2
                        im = im.crop((0, offset, w, offset + new_h))
                    
                    im = im.resize((800, 1000), Image.Resampling.LANCZOS)
                    im.save(out_path, "JPEG", quality=92)
                
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                print(f"[OK] {out_filename} ({im.size[0]}x{im.size[1]}) <- {img_url[:70]}...")
                saved = True
                break
        except Exception:
            continue
    if not saved:
        print(f"[FALLBACK] No se pudo descargar {out_filename}, se usará alternativa existente.")

