import asyncio
from playwright.async_api import async_playwright

async def test_ddg():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        url = "https://duckduckgo.com/?q=Trapstar+London+Decoded+Puffer+black&iax=images&ia=images"
        await page.goto(url, wait_until="networkidle", timeout=25000)
        await page.wait_for_timeout(3000)
        
        imgs = await page.evaluate('''() => {
            const results = [];
            const tiles = document.querySelectorAll('.tile--img__media img, .tile--img img, img.tile--img__img');
            for (let el of tiles) {
                const src = el.src || el.getAttribute('data-src');
                if (src) results.push(src);
            }
            return results.slice(0, 10);
        }''')
        print(f"Found {len(imgs)} images on DuckDuckGo:")
        for im in imgs:
            print(" ", im)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_ddg())
