import re
import os

def update_html():
    html_path = 'mi_proyecto/catalogo/templates/catalogo/inicio.html'
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Change logo
    html = re.sub(
        r'<a href="#experiencePin" class="brand-logo"[^>]*>.*?</a>', 
        r'<a href="#experiencePin" class="brand-logo" aria-label="Home"><img src="{% static \'img/logo_marca.png\' %}" alt="Logo" style="height: 45px; width: auto; object-fit: contain; filter: drop-shadow(0 0 10px rgba(255,0,0,0.4));"></a>', 
        html,
        flags=re.DOTALL
    )

    # Change fonts in Google Fonts URL
    html = re.sub(
        r'family=Inter:wght@300;400;500;600;700;800&family=Montserrat', 
        r'family=Oswald:wght@400;600;700&family=Roboto+Mono:wght@400;500;700', 
        html
    )
    # If the previous regex didn't catch it, let's just do a generic replace
    html = html.replace('Montserrat:wght@300;400;500;600;700;800;900', 'Oswald:wght@400;600;700')
    html = html.replace('Space+Mono:ital,wght@0,400;0,700;1,400', 'Roboto+Mono:wght@400;500;700')

    # Ensure blur overlay exists in HTML for the animation
    if 'id="modelVideoWrapper"' in html and 'id="scrollBlurOverlay"' not in html:
        html = html.replace(
            '<div class="model-video-wrapper" id="modelVideoWrapper">',
            '<div class="model-video-wrapper" id="modelVideoWrapper">\n            <div class="scroll-blur-overlay" id="scrollBlurOverlay"></div>'
        )

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("HTML updated successfully.")


def update_css():
    css_path = 'mi_proyecto/static/css/trapstar.css'
    with open(css_path, 'r', encoding='utf-8') as f:
        css = f.read()

    # 1. Update Palette to Chrome & Crimson
    css = css.replace('--color-bg: #060608;', '--color-bg: #050505;')
    css = css.replace('--color-bg-card: #0d0d12;', '--color-bg-card: #0e0e0e;')
    css = css.replace('--color-bg-elevated: #13131a;', '--color-bg-elevated: #1a1a1a;')
    css = css.replace('--color-text-main: #f8fafc;', '--color-text-main: #eaeaea;')
    
    # Swap Cyan with Crimson Red, and Red with Chrome Silver
    css = css.replace('--color-cyan: #00f0ff;', '--color-cyan: #e60000;')
    css = css.replace('--color-cyan-glow: rgba(0, 240, 255, 0.35);', '--color-cyan-glow: rgba(230, 0, 0, 0.4);')
    css = css.replace('--color-red: #ff1a2a;', '--color-red: #c0c0c0;')
    css = css.replace('--color-red-glow: rgba(255, 26, 42, 0.4);', '--color-red-glow: rgba(192, 192, 192, 0.4);')

    # Update Typography definitions
    css = css.replace("--font-sans: 'Inter', 'Helvetica Neue', 'Montserrat'", "--font-sans: 'Helvetica Neue', Arial, sans-serif")
    css = css.replace("--font-display: 'Syne', sans-serif;", "--font-display: 'Oswald', sans-serif;")
    css = css.replace("--font-mono: 'Space Mono', monospace;", "--font-mono: 'Roboto Mono', monospace;")

    # Add blur class for animation
    blur_css = """
.scroll-blur-overlay {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  backdrop-filter: blur(0px);
  -webkit-backdrop-filter: blur(0px);
  pointer-events: none;
  z-index: 2;
  transition: backdrop-filter 0.1s linear;
}

body::before {
  content: '';
  position: fixed;
  top: 0; left: 0; width: 100vw; height: 100vh;
  backdrop-filter: blur(4px);
  pointer-events: none;
  z-index: -1; 
}
"""
    if '.scroll-blur-overlay' not in css:
        css = css + '\n' + blur_css

    # Update backgrounds to reflect the new palette
    css = css.replace('rgba(0, 240, 255', 'rgba(230, 0, 0')
    
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css)
    print("CSS updated successfully.")

def update_js():
    js_path = 'mi_proyecto/static/js/trapstar.js'
    with open(js_path, 'r', encoding='utf-8') as f:
        js = f.read()

    # Add dynamic blur to the scroll sequence
    if 'const scrollBlurOverlay = document.getElementById(\'scrollBlurOverlay\');' not in js:
        js = js.replace(
            "const bgDarkOverlay = document.getElementById('bgDarkOverlay');",
            "const bgDarkOverlay = document.getElementById('bgDarkOverlay');\n  const scrollBlurOverlay = document.getElementById('scrollBlurOverlay');"
        )

    # In Phase 1, increase blur as we scroll
    phase1_blur = """
      if (scrollBlurOverlay) {
        const blurVal = (progress / 0.30) * 15; // Max 15px blur
        scrollBlurOverlay.style.backdropFilter = `blur(${blurVal}px)`;
        scrollBlurOverlay.style.webkitBackdropFilter = `blur(${blurVal}px)`;
      }
"""
    if 'blurVal' not in js:
        js = js.replace(
            "if (bgDarkOverlay) {",
            phase1_blur + "\n      if (bgDarkOverlay) {"
        )

    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js)
    print("JS updated successfully.")

if __name__ == '__main__':
    update_html()
    update_css()
    update_js()
