import urllib.request
import re

endpoints = ['http://127.0.0.1:8080/', 'http://127.0.0.1:8080/productos/']

for url in endpoints:
    print(f"\n--- Checking {url} ---")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read().decode('utf-8')
    
    # Check for trapstar occurrences in user visible text
    matches = re.findall(r'([^<>"\n]{0,30}trapstar[^<>"\n]{0,30})', html, re.IGNORECASE)
    print(f"Trapstar occurrences in text: {len(matches)}")
    for m in matches[:5]:
        print(f"  Match: {m}")
        
    # Check images used for hero
    if 'featured' in html:
        featured_imgs = re.findall(r'<div class="featured-img-col".*?src="([^"]+)"', html, re.DOTALL)
        print("Featured hero images:", featured_imgs)
        
    print(f"Status: OK (length {len(html)})")
