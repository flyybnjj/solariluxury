import urllib.request
import os
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "scripts", "raw_verified")
os.makedirs(OUT_DIR, exist_ok=True)

TARGETS = [
    ("https://uk.trapstarlondon.com/cdn/shop/files/Tspj02_Irongate_arch_puffer_jacket__BLACK_WHITE_B.jpg?v=1735216328&width=2560", "trapstar_irongate_puffer_official.jpg"),
    ("https://nosaucetheplug.com/cdn/shop/files/trapstar-jackets-x-small-trapstar-decoded-hooded-puffer-2-0-jacket-black-38448279224554_1100x.png?v=1709577803", "trapstar_decoded_puffer_2_0.png"),
    ("https://www.thefashionisto.com/wp-content/uploads/2023/03/Central-Cee-Highsnobiety-Photoshoot-2023-JEKEUN-Jacket.jpg", "central_cee_highsnobiety.jpg"),
    ("https://i.pinimg.com/736x/4f/57/8f/4f578f3b483e771417664d203e52889c.jpg", "central_cee_jacquemus.jpg"),
    ("https://i.pinimg.com/736x/6c/6d/d8/6c6dd86bffee4512472e6346876fb30f.jpg", "central_cee_fashion_poster.jpg")
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Referer': 'https://www.bing.com/'
}

for url, filename in TARGETS:
    out_path = os.path.join(OUT_DIR, filename)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            with open(out_path, 'wb') as f:
                f.write(data)
        with Image.open(out_path) as im:
            print(f"[OK] {filename}: {im.size[0]}x{im.size[1]} ({len(data)} bytes, {im.format})")
    except Exception as e:
        print(f"[ERROR] {filename}: {e}")
