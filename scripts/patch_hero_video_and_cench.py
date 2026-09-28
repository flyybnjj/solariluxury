import re

path_inicio = 'mi_proyecto/catalogo/templates/catalogo/inicio.html'
with open(path_inicio, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update CSS for Video and CENCH Letters
video_cench_css = '''
    /* ======================================================
       HERO 1080P/8K VIDEO & CENCH ANIMATED LETTERS
    ====================================================== */
    .hero-bg-video {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center 30%;
      filter: contrast(1.18) brightness(0.55) saturate(1.2);
      z-index: 1;
      pointer-events: none;
      transition: transform 0.1s linear;
      will-change: transform;
    }
    .hero-vignette {
      position: absolute;
      inset: 0;
      background:
        radial-gradient(ellipse 70% 80% at 50% 100%, rgba(230,0,0,0.25) 0%, transparent 70%),
        radial-gradient(ellipse 100% 60% at 50% 0%, rgba(0,0,0,0.85) 0%, transparent 65%),
        linear-gradient(to bottom, rgba(0,0,0,0.5) 0%, transparent 35%, rgba(0,0,0,0.95) 100%);
      pointer-events: none;
      z-index: 2;
    }

    /* Hero Brand & CENCH letters */
    .hero-brand-solar {
      display: block;
      font-family: 'Bebas Neue', sans-serif;
      font-size: clamp(68px, 15vw, 190px);
      line-height: 0.88;
      letter-spacing: 0.03em;
      color: #fff;
      text-shadow: 0 4px 40px rgba(0, 0, 0, 0.9), 0 0 80px rgba(255, 255, 255, 0.15);
    }
    .cench-animated-box {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-top: 10px;
    }
    .cench-letters-row {
      display: inline-flex;
      font-family: 'Bebas Neue', sans-serif;
      font-size: clamp(52px, 11vw, 130px);
      line-height: 0.85;
      letter-spacing: 0.2em;
    }
    .cench-char {
      display: inline-block;
      color: #fff;
      animation: cenchBreath 3.4s cubic-bezier(0.4, 0, 0.2, 1) infinite;
      animation-delay: calc(var(--i) * 0.2s);
      will-change: transform, opacity, filter;
    }
    @keyframes cenchBreath {
      0%, 100% {
        opacity: 0.04;
        transform: translateY(14px) scale(0.92);
        filter: blur(8px);
        color: rgba(255, 255, 255, 0.1);
        text-shadow: none;
      }
      25%, 70% {
        opacity: 1;
        transform: translateY(0) scale(1);
        filter: blur(0px);
        color: #fff;
        text-shadow: 0 0 25px rgba(230, 0, 0, 0.9),
                     0 0 50px rgba(255, 107, 53, 0.7),
                     0 0 90px rgba(255, 255, 255, 0.5);
      }
      45% {
        color: #ff6b35;
        text-shadow: 0 0 35px #e60000, 0 0 70px #ffd700;
        transform: translateY(-3px) scale(1.06);
      }
      85% {
        opacity: 0.15;
        transform: translateY(-6px) scale(0.96);
        filter: blur(4px);
        color: rgba(230, 0, 0, 0.3);
      }
    }
    .cench-tagline {
      font-family: 'Space Mono', monospace;
      font-size: 11px;
      letter-spacing: 0.4em;
      color: #e60000;
      text-transform: uppercase;
      margin-top: 14px;
      opacity: 0.9;
    }

    /* Loader CENCH */
    .loader-cench-pulse {
      display: inline-flex;
      gap: 8px;
      font-family: 'Bebas Neue', sans-serif;
      font-size: 32px;
      letter-spacing: 0.25em;
      margin-top: 8px;
    }
    .loader-cench-pulse span {
      display: inline-block;
      animation: cenchBreath 2.8s ease-in-out infinite;
      animation-delay: calc(var(--i) * 0.15s);
    }
'''

if '.hero-bg-video' not in html:
    html = html.replace('.hero-bg-img {', video_cench_css + '\n    .hero-bg-img {')

# 2. Update Loader HTML
old_loader_re = re.search(r'<div class="loader-logo">.*?</div>\s*<div class="loader-bar-wrap">', html, re.DOTALL)
if old_loader_re:
    new_loader_html = '''<div class="loader-logo" style="text-align: center;">
    <div style="font-family: 'Bebas Neue', sans-serif; font-size: clamp(40px, 7vw, 76px); letter-spacing: 0.12em; color: #fff;">SOLARILUXURY</div>
    <div class="loader-cench-pulse">
      <span style="--i:0">C</span>
      <span style="--i:1">E</span>
      <span style="--i:2">N</span>
      <span style="--i:3">C</span>
      <span style="--i:4">H</span>
    </div>
  </div>
  <div class="loader-bar-wrap">'''
    html = html[:old_loader_re.start()] + new_loader_html + html[old_loader_re.end() - len('<div class="loader-bar-wrap">'):]

# 3. Update Section 1 (Hero Pin & Sticky)
old_hero_re = re.search(r'<section class="hero-pin" id="heroPin">.*?</section>\s*<!-- ══════════════════════════════════════════════════════════\s*STATEMENT', html, re.DOTALL)
if old_hero_re:
    new_hero_html = '''<section class="hero-pin" id="heroPin">
  <div class="hero-sticky" id="heroSticky">
    
    <!-- Central Cee 1080p High-Quality Video Clip -->
    <video class="hero-bg-video" autoplay muted loop playsinline poster="{% static 'img/central_cee_front.jpg' %}" id="heroVideo">
      <source src="{% static 'video/central_cee_hero.mp4' %}" type="video/mp4">
    </video>
    
    <div class="hero-vignette"></div>

    <!-- Tape -->
    <div class="hero-tape">
      <div class="tape-track" id="tapeTrack">
        <div class="tape-item">SOLARILUXURY</div>
        <div class="tape-item">CENCH</div>
        <div class="tape-item">DECODED 2.0</div>
        <div class="tape-item">OFFICIAL COLLABORATION</div>
        <div class="tape-item">W12 SHEPHERD'S BUSH</div>
        <div class="tape-item">LIMITED DROP 2026</div>
        <div class="tape-item">DIAMOND VAULT</div>
        <!-- Dup -->
        <div class="tape-item">SOLARILUXURY</div>
        <div class="tape-item">CENCH</div>
        <div class="tape-item">DECODED 2.0</div>
        <div class="tape-item">OFFICIAL COLLABORATION</div>
        <div class="tape-item">W12 SHEPHERD'S BUSH</div>
        <div class="tape-item">LIMITED DROP 2026</div>
        <div class="tape-item">DIAMOND VAULT</div>
      </div>
    </div>

    <!-- Side text -->
    <span class="hero-side-text hero-side-left">OFFICIAL COLLABORATION 2026</span>
    <span class="hero-side-text hero-side-right">SOLARILUXURY × CENTRAL CEE</span>

    <!-- Main title: SOLARILUXURY + Animated CENCH Letters that appear and disappear -->
    <div class="hero-content" id="heroContent">
      <div class="hero-eyebrow">Autumn / Winter 2026 Campaign Archive</div>
      <h1 class="hero-title">
        <span class="hero-brand-solar">SOLARILUXURY</span>
        <div class="cench-animated-box" title="CENCH">
          <div class="cench-letters-row" aria-label="CENCH">
            <span class="cench-char" style="--i:0">C</span>
            <span class="cench-char" style="--i:1">E</span>
            <span class="cench-char" style="--i:2">N</span>
            <span class="cench-char" style="--i:3">C</span>
            <span class="cench-char" style="--i:4">H</span>
          </div>
          <span class="cench-tagline">OFFICIAL COLLABORATION EDITION</span>
        </div>
      </h1>
    </div>

    <div class="hero-glow" id="heroGlow"></div>

    <!-- Progress bar -->
    <div class="hero-progress-bar" id="heroBar"></div>

    <!-- Scroll cue -->
    <div class="hero-scroll-cue">
      <div class="scroll-cue-line"></div>
      <span class="scroll-cue-text">Scroll</span>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════════════════════
     STATEMENT'''
    html = html[:old_hero_re.start()] + new_hero_html + html[old_hero_re.end() - len('<!-- ══════════════════════════════════════════════════════════\n     STATEMENT'):]

# 4. Update JS Scroll Parallax for Video
old_js_hero = re.search(r'// ── HERO SCROLL PARALLAX PIN ──.*?// ── FEATURED 3D CHAIN SWITCHER', html, re.DOTALL)
if old_js_hero:
    new_js_hero = '''// ── HERO SCROLL PARALLAX PIN ──────────────────────────────────
const heroPin = document.getElementById('heroPin');
const heroVideo = document.getElementById('heroVideo');
const heroBar = document.getElementById('heroBar');

window.addEventListener('scroll', () => {
  if (!heroPin) return;
  const pinTop = heroPin.getBoundingClientRect().top;
  const pinHeight = heroPin.offsetHeight - window.innerHeight;
  const scrolled = Math.max(0, -pinTop);
  const progress = Math.min(1, scrolled / pinHeight);

  // Progress bar
  if (heroBar) heroBar.style.width = (progress * 100) + '%';

  // Video subtle scale on scroll
  if (heroVideo) {
    const vScale = 1.0 + progress * 0.12;
    heroVideo.style.transform = `scale(${vScale})`;
  }

  // Title scale out on scroll
  const heroContent = document.getElementById('heroContent');
  if (heroContent) {
    const titleScale = 1 - progress * 0.18;
    const titleO = 1 - progress * 1.5;
    heroContent.style.transform = `scale(${titleScale})`;
    heroContent.style.opacity = Math.max(0, titleO);
  }
}, { passive: true });

// ── FEATURED 3D CHAIN SWITCHER'''
    html = html[:old_js_hero.start()] + new_js_hero + html[old_js_hero.end() - len('// ── FEATURED 3D CHAIN SWITCHER'):]

with open(path_inicio, 'w', encoding='utf-8') as f:
    f.write(html)

print('Successfully updated inicio.html with Central Cee video clip and animated CENCH letters!')
