import os
import sys
import re
import json
import urllib.request
import urllib.parse
from PIL import Image, ImageOps, ImageEnhance
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_IMG = os.path.join(BASE_DIR, "mi_proyecto", "static", "img")
SEQ_DIR = os.path.join(STATIC_IMG, "central_cee_sequence")
DOCS_STATIC_IMG = os.path.join(BASE_DIR, "docs", "static", "img")
DOCS_SEQ_DIR = os.path.join(DOCS_STATIC_IMG, "central_cee_sequence")

os.makedirs(STATIC_IMG, exist_ok=True)
os.makedirs(SEQ_DIR, exist_ok=True)
os.makedirs(DOCS_STATIC_IMG, exist_ok=True)
os.makedirs(DOCS_SEQ_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
}

def search_ddg_images(query, max_results=15):
    """Search DuckDuckGo Images API for real photographs"""
    try:
        url = 'https://duckduckgo.com/'
        req = urllib.request.Request(f'https://duckduckgo.com/?q={urllib.parse.quote(query)}', headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        
        vqd_match = re.search(r'vqd=["\']?([0-9-]+)', html)
        if not vqd_match:
            print(f"[WARN] No vqd token for query: {query}")
            return []
        vqd = vqd_match.group(1)
        
        api_url = f'https://duckduckgo.com/i.js?l=us-en&o=json&q={urllib.parse.quote(query)}&vqd={vqd}&f=,,,&p=1'
        req2 = urllib.request.Request(api_url, headers=HEADERS)
        with urllib.request.urlopen(req2, timeout=10) as resp2:
            data = json.loads(resp2.read().decode('utf-8'))
            results = []
            for r in data.get('results', []):
                img_url = r.get('image')
                if img_url and (img_url.endswith('.jpg') or img_url.endswith('.png') or img_url.endswith('.jpeg') or 'images' in img_url):
                    results.append({
                        'title': r.get('title'),
                        'image': img_url,
                        'w': r.get('width', 0),
                        'h': r.get('height', 0)
                    })
                if len(results) >= max_results:
                    break
            return results
    except Exception as e:
        print(f"[ERROR] search_ddg_images for '{query}': {e}")
        return []

def download_image(url, out_path, min_size=5000):
    """Download image, verify it is valid, and save"""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as response:
            content = response.read()
            if len(content) < min_size:
                return False
            with open(out_path, 'wb') as f:
                f.write(content)
        
        # Test if PIL can open it
        with Image.open(out_path) as im:
            im.verify()
        print(f"[OK] Downloaded valid image: {os.path.basename(out_path)} ({len(content)} bytes)")
        return True
    except Exception as e:
        if os.path.exists(out_path):
            try: os.remove(out_path)
            except: pass
        return False

if __name__ == "__main__":
    print("Testing image scraper...")
    res = search_ddg_images("Central Cee Trapstar", 5)
    for r in res:
        print(r['title'], "->", r['image'])
