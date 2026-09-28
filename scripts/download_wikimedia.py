import urllib.request
import os
from PIL import Image

TARGETS = [
    ("https://upload.wikimedia.org/wikipedia/commons/3/30/Central_cee-5.jpg", "central_cee_concert.jpg"),
    ("https://upload.wikimedia.org/wikipedia/commons/1/14/Central_Cee.jpg", "central_cee_wide.jpg"),
    ("https://upload.wikimedia.org/wikipedia/commons/e/e3/Central_Cee_%28cropped%29.jpg", "central_cee_cropped.jpg"),
    ("https://upload.wikimedia.org/wikipedia/commons/c/c9/Central_Cee_in_2020.png", "central_cee_2020.png")
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "scripts", "raw_central_cee")
os.makedirs(OUT_DIR, exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none'
}

for url, filename in TARGETS:
    out_path = os.path.join(OUT_DIR, filename)
    try:
        print(f"Downloading {filename} from {url}...")
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
            with open(out_path, 'wb') as f:
                f.write(data)
        with Image.open(out_path) as im:
            print(f"  [OK] {filename}: {im.size[0]}x{im.size[1]} ({len(data)} bytes)")
    except Exception as e:
        print(f"  [ERROR] {filename}: {e}")
