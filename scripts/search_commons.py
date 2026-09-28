import urllib.request
import json

url = 'https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=Central+Cee&gsrnamespace=6&prop=imageinfo&iiprop=url|size|mime&format=json'
req = urllib.request.Request(url, headers={'User-Agent': 'TiendaBot/1.0 (test@example.com)'})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        pages = data.get('query', {}).get('pages', {})
        for pid, page in pages.items():
            title = page.get('title')
            ii = page.get('imageinfo', [{}])[0]
            print(f"{title}: {ii.get('url')} ({ii.get('width')} x {ii.get('height')})")
except Exception as e:
    print('Error:', e)
