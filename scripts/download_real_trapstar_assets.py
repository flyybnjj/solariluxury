"""
TRAPSTAR LONDON x CENTRAL CEE — Real Asset Downloader & Processor
Uses Playwright to fetch real editorial photographs of Central Cee and authentic Trapstar London garments.
"""

import os
import sys
import asyncio
import json
import urllib.request
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import numpy as np
from playwright.async_api import async_playwright

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
    'Referer': 'https://www.bing.com/'
}

async def search_real_images(page, query, count=6):
    """Search Bing Images for high-res real photographs"""
    url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}&qft=+filterui:imagesize-large"
    print(f"[SEARCH] Query: {query}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)
        
        links = await page.evaluate('''() => {
            const results = [];
            const elements = document.querySelectorAll('a.iusc');
            for (let el of elements) {
                try {
                    const m = JSON.parse(el.getAttribute('m'));
                    if (m && m.murl && (m.murl.startsWith('http://') || m.murl.startsWith('https://'))) {
                        results.push({ murl: m.murl, title: m.t || '', w: m.w || 0, h: m.h || 0 });
                    }
                } catch(e) {}
            }
            return results;
        }''')
        return links[:count]
    except Exception as e:
        print(f"[ERROR] search_real_images failed for {query}: {e}")
        return []

def download_and_verify(url, target_path, min_bytes=10000):
    """Download image, verify format with PIL, save"""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = resp.read()
            if len(data) < min_bytes:
                return False
            with open(target_path, 'wb') as f:
                f.write(data)
                
        with Image.open(target_path) as im:
            im.verify()
        print(f"  [DOWNLOADED] {os.path.basename(target_path)} ({len(data)} bytes)")
        return True
    except Exception as e:
        if os.path.exists(target_path):
            try: os.remove(target_path)
            except: pass
        return False

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=HEADERS['User-Agent'])
        page = await context.new_page()

        targets = [
            # 1. Central Cee Campaign Portrait
            ("Central Cee Highsnobiety Photoshoot", os.path.join(STATIC_IMG, "central_cee_front.jpg")),
            # 2. Central Cee Alternate Pose / Tilt
            ("Central Cee portrait photoshoot studio", os.path.join(STATIC_IMG, "central_cee_tilt.jpg")),
            # 3. Central Cee London Street Style
            ("Central Cee London street photoshoot", os.path.join(STATIC_IMG, "central_cee_street.jpg")),
            # 4. Real Trapstar Decoded Puffer Jacket
            ("Trapstar Decoded Puffer jacket black official", os.path.join(STATIC_IMG, "trapstar_puffer_hero.jpg")),
            # 5. Real Trapstar 3M Reflective Flash
            ("Trapstar reflective jacket 3m flash", os.path.join(STATIC_IMG, "trapstar_3m_flash.jpg")),
            # 6. Real Trapstar Chenille Texture / Logo
            ("Trapstar chenille embroidery decoded hoodie logo", os.path.join(STATIC_IMG, "trapstar_chenille_texture.jpg")),
            # 7. Real Trapstar Puffer Open / Lining
            ("Trapstar decoded jacket hood open lining", os.path.join(STATIC_IMG, "trapstar_puffer_open.jpg")),
            # 8. Real Trapstar Shooters Tracksuit
            ("Trapstar Shooters Tracksuit grey chenille", os.path.join(STATIC_IMG, "trapstar_tracksuit.jpg")),
        ]

        for query, dest_path in targets:
            print(f"\nProcessing target: {os.path.basename(dest_path)}...")
            candidates = await search_real_images(page, query, count=8)
            success = False
            for cand in candidates:
                img_url = cand['murl']
                print(f"  Attempting download from: {img_url[:70]}...")
                if download_and_verify(img_url, dest_path):
                    success = True
                    break
            if not success:
                print(f"  [WARN] Could not download fresh candidate for {os.path.basename(dest_path)}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
