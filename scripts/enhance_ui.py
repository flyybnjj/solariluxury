import re
import os

def enhance_css():
    css_path = 'mi_proyecto/static/css/trapstar.css'
    with open(css_path, 'r', encoding='utf-8') as f:
        css = f.read()

    # 1. Update Typography and Colors for a more premium feel
    css = css.replace("--font-sans: 'Montserrat'", "--font-sans: 'Inter', 'Helvetica Neue', 'Montserrat'")
    css = css.replace("--color-border: rgba(255, 255, 255, 0.12);", "--color-border: rgba(255, 255, 255, 0.04);")
    css = css.replace("--color-border-light: rgba(255, 255, 255, 0.2);", "--color-border-light: rgba(255, 255, 255, 0.1);")

    # 2. Add Grain/Noise Overlay to body
    grain_css = """
body::after {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  pointer-events: none;
  z-index: 9999;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
  opacity: 0.04;
  mix-blend-mode: overlay;
}
"""
    if 'body::after' not in css:
        css = css.replace('body {\n', grain_css + '\nbody {\n')

    # 3. Enhance backdrop-filters to luxury glassmorphism (saturate + blur)
    css = re.sub(r'backdrop-filter:\s*blur\((.*?)\);', r'backdrop-filter: blur(\1) saturate(180%);', css)

    # 4. Enhance buttons and shadows
    css = css.replace('box-shadow: 0 0 25px rgba(0, 240, 255, 0.2);', 'box-shadow: 0 0 25px rgba(0, 240, 255, 0.15), inset 0 0 10px rgba(0, 240, 255, 0.1);')
    css = css.replace('border: 1px solid rgba(0, 240, 255, 0.4);', 'border: 1px solid rgba(0, 240, 255, 0.2); background: linear-gradient(135deg, rgba(13,13,18,0.9) 0%, rgba(6,6,8,0.95) 100%);')
    css = css.replace('box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8), 0 0 20px rgba(0, 240, 255, 0.15);', 'box-shadow: 0 20px 40px rgba(0, 0, 0, 0.95), 0 0 25px rgba(0, 240, 255, 0.08);')

    # 5. Fix overlapping text on hotspots by adding better contrast backdrops
    css = css.replace('.hotspot-card {\n  position: absolute;', '.hotspot-card {\n  position: absolute;\n  backdrop-filter: blur(25px) saturate(200%);\n  background: rgba(10, 10, 12, 0.7);\n  border: 1px solid rgba(255,255,255,0.08);')

    # 6. Ultra-thin elegant typography for headers
    css = css.replace('font-weight: 800;', 'font-weight: 700; letter-spacing: 0.03em;')
    css = css.replace('letter-spacing: 0.1em;', 'letter-spacing: 0.15em;')

    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css)
    print('CSS enhanced successfully.')

def enhance_js():
    js_path = 'mi_proyecto/static/js/trapstar.js'
    with open(js_path, 'r', encoding='utf-8') as f:
        js = f.read()

    # Add a smoothing lerp to the frame updates to remove scroll jitter
    lerp_code = """
  // Smoothing variables for Frame Interpolation
  let targetFrameIdx = 0;
  let currentFrameIdx = 0;

  function updateCcFrame(index) {
    targetFrameIdx = index;
  }

  function renderLoop() {
    // Lerp logic for buttery smooth scrolling
    currentFrameIdx += (targetFrameIdx - currentFrameIdx) * 0.12;
    
    const safeIndex = Math.max(0, Math.min(Math.round(currentFrameIdx), TOTAL_CC_FRAMES - 1));
    if (safeIndex !== lastCcFrame && ccFrames.length) {
      const frameObj = ccFrames[safeIndex];
      if (frameObj && frameObj.src) {
        if(ccImg) ccImg.src = frameObj.src;
        lastCcFrame = safeIndex;
      }
    }
    
    // Magnetic Effect for UI buttons
    document.querySelectorAll('.cc-backstage-trigger, .hotspot-pin, .bag-trigger').forEach(btn => {
      if(btn.dataset.magneticX) {
        btn.style.transform = `translate(${btn.dataset.magneticX}px, ${btn.dataset.magneticY}px) scale(1.05)`;
      } else {
        btn.style.transform = '';
      }
    });

    requestAnimationFrame(renderLoop);
  }
  
  // Start the render loop
  requestAnimationFrame(renderLoop);
"""

    if 'function updateCcFrame(index) {' in js and 'requestAnimationFrame(renderLoop)' not in js:
        # Regex to replace updateCcFrame block safely
        js = re.sub(r'function updateCcFrame\(index\) \{[\s\S]*?lastCcFrame = safeIndex;\n\s*\}\n\s*\}\n\s*\}', lerp_code, js)

    magnetic_listeners = """
    // Magnetic Hover Effect Setup
    document.querySelectorAll('.cc-backstage-trigger, .hotspot-pin, .bag-trigger').forEach(btn => {
      btn.addEventListener('mousemove', (e) => {
        const rect = btn.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        btn.dataset.magneticX = x * 0.4;
        btn.dataset.magneticY = y * 0.4;
      });
      btn.addEventListener('mouseleave', () => {
        btn.dataset.magneticX = 0;
        btn.dataset.magneticY = 0;
      });
    });
"""
    if 'setupHeroCommerce();' in js and 'Magnetic Hover Effect' not in js:
        js = js.replace('setupHeroCommerce();', 'setupHeroCommerce();\n' + magnetic_listeners)

    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js)
    print('JS enhanced successfully.')

if __name__ == '__main__':
    enhance_css()
    enhance_js()
