import requests
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

queries = [
    'site:pinterest.com central cee aesthetic outfit',
    'site:pinterest.com central cee photoshoot highsnobiety',
    'site:pinterest.com central cee syna world tracksuit'
]

all_pinimg = set()

for q in queries:
    try:
        url = f'https://www.google.com/search?q={requests.utils.quote(q)}&tbm=isch'
        r = requests.get(url, headers=headers, timeout=10)
        print(f"Query '{q}' status: {r.status_code}")
        # Search for pinimg links
        found = re.findall(r'https://i\.pinimg\.com/[0-9a-zA-Z/_.-]+', r.text)
        for u in found:
            # Upgrade resolution to 736x or originals
            hi = re.sub(r'/(?:150x150|236x|474x)/', '/736x/', u)
            all_pinimg.add(hi)
    except Exception as e:
        print(f"Error {q}: {e}")

print(f"Total unique pinimg URLs found: {len(all_pinimg)}")
for u in sorted(all_pinimg):
    print(u)
