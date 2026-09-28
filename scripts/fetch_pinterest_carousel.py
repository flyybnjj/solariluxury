import urllib.request
import urllib.parse
import json
import re
import os
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_IMG_DIR = os.path.join(BASE_DIR, "mi_proyecto", "static", "img")

# Search duckduckgo json or bing for Pinterest Central Cee images
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}

queries = [
    'central cee syna world outfit pinterest',
    'central cee streetwear aesthetic photoshoot',
    'central cee trapstar jacket photoshoot high quality',
    'central cee jacquemus front row fashion',
]

found_images = []

for q in queries:
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            # Look for pinterest or high-res image urls
            urls = re.findall(r'https?://[^\s"\'<>&]+(?:\.jpg|\.png|\.webp)', html, re.IGNORECASE)
            for u in urls:
                if 'pinimg.com' in u or 'highsnobiety' in u or 'gq' in u or 'hypebeast' in u or 'vogue' in u:
                    if u not in found_images:
                        found_images.append(u)
    except Exception as e:
        print(f"Error searching {q}: {e}")

print(f"Found {len(found_images)} candidate images.")
for i in found_images[:20]:
    print(" ", i)
