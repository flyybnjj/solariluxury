import urllib.request
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

urls = [
    'https://www.thefashionisto.com/central-cee-highsnobiety/',
    'https://pausemag.co.uk/2023/05/central-cee-collaborates-with-syna-world-for-latest-drop/',
    'https://pausemag.co.uk/2022/11/central-cee-syna-world/',
    'https://www.gq-magazine.co.uk/article/central-cee-interview-2023',
    'https://dazeddigital.com/music/article/58580/1/central-cee-interview-drill-rap-doja-23-syna-world',
    'https://rollingstone.co.uk/music/news/central-cee-syna-world-clothing-brand-29402/'
]

all_images = set()

for u in urls:
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode('utf-8', errors='ignore')
            matches = re.findall(r'(https://[^\s"\'<>]+\.(?:jpg|jpeg|png|webp))', html)
            for m in matches:
                # clean up pinterest wrappers
                if 'media=' in m:
                    m = m.split('media=')[-1]
                if any(k in m.lower() for k in ['central-cee', 'central_cee', 'syna', 'highsnobiety', 'pause']):
                    all_images.add(m)
    except Exception as e:
        print(f"Error {u}: {e}")

print("Total images found:", len(all_images))
for img in sorted(all_images):
    print(img)
