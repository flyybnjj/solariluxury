import urllib.request
import os
import time
from PIL import Image

TARGETS = [
    ("https://upload.wikimedia.org/wikipedia/commons/e/e3/Central_Cee_%28cropped%29.jpg", "central_cee_cropped.jpg"),
    ("https://upload.wikimedia.org/wikipedia/commons/c/c9/Central_Cee_in_2020.png", "central_cee_2020.png")
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "scripts", "raw_central_cee")

headers = {
    'User-Agent': 'CentralCeeCampaignBot/1.0 (https://github.com/avalo; contact@example.com) EducationalProject',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
}

for url, filename in TARGETS:
    out_path = os.path.join(OUT_DIR, filename)
    time.sleep(3)
    try:
        print(f"Downloading {filename}...")
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
            with open(out_path, 'wb') as f:
                f.write(data)
        with Image.open(out_path) as im:
            print(f"  [OK] {filename}: {im.size[0]}x{im.size[1]} ({len(data)} bytes)")
    except Exception as e:
        print(f"  [ERROR] {filename}: {e}")
