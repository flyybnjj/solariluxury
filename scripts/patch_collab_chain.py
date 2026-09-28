import os

path = 'mi_proyecto/catalogo/templates/catalogo/inicio.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Title
html = html.replace('<title>TRAPSTAR × CENTRAL CEE — DECODED 2026</title>', '<title>SOLARILUXURY × CENTRAL CEE — OFFICIAL COLLABORATION 2026</title>')

# 2. Add CSS for 3D Chain and Switcher
css_addition = '''
    /* 3D Asset & Switcher styling in Featured */
    .collab-badge-top {
      position: absolute;
      top: 20px; left: 20px;
      z-index: 10;
      padding: 6px 14px;
      border-radius: 100px;
      background: rgba(0,0,0,0.75);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255,255,255,0.15);
      font-family: 'Space Mono', monospace;
      font-size: 10px;
      letter-spacing: 0.15em;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .pulse-dot {
      width: 7px; height: 7px;
      border-radius: 50%;
      background: #e60000;
      box-shadow: 0 0 10px #e60000;
      animation: pulseDot 2s ease infinite;
    }
    @keyframes pulseDot {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(0.8); }
    }
    .featured-3d-asset {
      transition: opacity 0.3s ease, transform 0.8s cubic-bezier(0.16,1,0.3,1);
    }
    .featured-switch-bar {
      position: absolute;
      bottom: 24px; left: 50%;
      transform: translateX(-50%);
      z-index: 10;
      display: flex;
      gap: 6px;
      padding: 6px;
      border-radius: 100px;
      background: rgba(0,0,0,0.85);
      backdrop-filter: blur(24px);
      border: 1px solid rgba(255,255,255,0.15);
    }
    .switch-btn {
      padding: 8px 16px;
      border-radius: 100px;
      background: transparent;
      border: 1px solid transparent;
      color: rgba(255,255,255,0.5);
      font-family: 'Space Mono', monospace;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.08em;
      cursor: pointer;
      transition: all 0.25s ease;
      white-space: nowrap;
    }
    .switch-btn:hover {
      color: #fff;
    }
    .switch-btn.active {
      background: rgba(255,255,255,0.15);
      border-color: rgba(255,255,255,0.3);
      color: #fff;
      box-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }
'''
if '.collab-badge-top' not in html:
    html = html.replace('.featured-info-col {', css_addition + '\n    .featured-info-col {')

# 3. Update Loader Logo
old_loader = '''  <div class="loader-logo">
    <span style="animation-delay:0.0s">T</span><span style="animation-delay:0.05s">R</span><span style="animation-delay:0.10s">A</span><span style="animation-delay:0.15s">P</span><span style="animation-delay:0.20s">S</span><span style="animation-delay:0.25s">T</span><span style="animation-delay:0.30s">A</span><span style="animation-delay:0.35s">R</span><span style="animation-delay:0.45s"> </span><span style="animation-delay:0.50s">×</span><span style="animation-delay:0.55s"> </span><span style="animation-delay:0.60s">C</span><span style="animation-delay:0.65s">C</span>
  </div>'''

new_loader = '''  <div class="loader-logo">
    <span style="animation-delay:0.0s">S</span><span style="animation-delay:0.04s">O</span><span style="animation-delay:0.08s">L</span><span style="animation-delay:0.12s">A</span><span style="animation-delay:0.16s">R</span><span style="animation-delay:0.20s">I</span><span style="animation-delay:0.24s">L</span><span style="animation-delay:0.28s">U</span><span style="animation-delay:0.32s">X</span><span style="animation-delay:0.36s">U</span><span style="animation-delay:0.40s">R</span><span style="animation-delay:0.44s">Y</span><span style="animation-delay:0.50s"> </span><span style="animation-delay:0.54s">×</span><span style="animation-delay:0.58s"> </span><span style="animation-delay:0.62s">C</span><span style="animation-delay:0.66s">C</span>
  </div>'''
html = html.replace(old_loader, new_loader)

# 4. Update Header Logo Alt
html = html.replace('alt="Trapstar"', 'alt="Solariluxury"')

# 5. Update Tape Track
html = html.replace('<div class="tape-item">TRAPSTAR LONDON</div>', '<div class="tape-item">SOLARILUXURY</div>')

# 6. Update Hero side-text and title
html = html.replace('TRAPSTAR × CENTRAL CEE × W12', 'SOLARILUXURY × CENTRAL CEE')
html = html.replace('<h1 class="hero-title">\n        <span class="line"><span>TRAPSTAR</span></span>', '<h1 class="hero-title">\n        <span class="line"><span>SOLARILUXURY</span></span>')

# 7. Update Campaign Photo Section
html = html.replace('TRAPSTAR × CENTRAL CEE — W12', 'SOLARILUXURY × CENTRAL CEE — OFFICIAL COLLAB')
html = html.replace('Central Cee lidera la campaña más brutal de Trapstar London — prendas nacidas en las calles, diseñadas para durar una era.', 'Central Cee lidera la colaboración más exclusiva junto a Solariluxury — alta costura streetwear, piezas de edición limitada y joyería icónica diseñadas para marcar época.')

# 8. Update Section 5 (Featured Hero Product with 3D Chain Animation and switcher)
old_featured = '''{% if hero_prod %}
<section class="featured-section sr" id="featured">
  <div class="featured-inner">
    <div class="featured-img-col">
      <img src="{% static hero_prod.imagen %}" alt="{{ hero_prod.nombre }}">
      <div class="featured-img-overlay"></div>
    </div>
    <div class="featured-info-col">
      <div class="fi-tag">HERO DROP — {{ hero_prod.categoria.nombre|default:"PUFFERS" }}</div>
      <h2 class="fi-title">{{ hero_prod.nombre }}</h2>
      <p class="fi-subtitle">{{ hero_prod.subtitulo }}</p>
      <p class="fi-desc">{{ hero_prod.descripcion }}</p>
      <ul class="fi-specs">
        {% for d in hero_prod.detalles.all %}
        <li>{{ d.texto }}</li>
        {% endfor %}
      </ul>
      <div class="fi-price">${{ hero_prod.precio|floatformat:"0" }} CLP</div>
      <div class="fi-price-usd">≈ ${{ hero_prod.precio_usd }} USD</div>
      <a href="{% url 'detalle_producto' hero_prod.id %}" class="fi-cta">
        VER PRODUCTO <span class="fi-cta-arrow">→</span>
      </a>
    </div>
  </div>
</section>
{% endif %}'''

new_featured = '''{% if hero_prod %}
<section class="featured-section sr" id="featured">
  <div class="featured-inner">
    <div class="featured-img-col" id="featuredCol">
      <div class="collab-badge-top">
        <span class="pulse-dot"></span>
        <span>CENTRAL CEE SIGNATURE 3D CHAIN • VVS DIAMONDS</span>
      </div>

      <!-- 3D Chain Animated Asset (Active by Default) -->
      <img src="{% static 'img/central_cee_chain_3d.gif' %}" alt="Central Cee Signature 3D Diamond Chain" id="featuredMainMedia" class="featured-3d-asset">
      <div class="featured-img-overlay"></div>

      <!-- Interactive 3-way Media Switcher -->
      <div class="featured-switch-bar">
        <button type="button" class="switch-btn active" onclick="switchFeaturedMedia('chain_3d', this)">
          💎 3D CHAIN
        </button>
        <button type="button" class="switch-btn" onclick="switchFeaturedMedia('central_cee', this)">
          📸 CENTRAL CEE
        </button>
        <button type="button" class="switch-btn" onclick="switchFeaturedMedia('puffer', this)">
          🧥 COLLAB PUFFER
        </button>
      </div>
    </div>

    <div class="featured-info-col">
      <div class="fi-tag">PIEZA CENTRAL DE CAMPAÑA — SOLARILUXURY × CENTRAL CEE</div>
      <h2 class="fi-title">SOLARILUXURY × CENTRAL CEE — THE SIGNATURE ICED CHAIN & DECODED 2.0</h2>
      <p class="fi-subtitle">COLABORACIÓN OFICIAL 2026 • EDICIÓN DIAMOND VAULT</p>
      <p class="fi-desc">
        La colaboración oficial que une a Solariluxury con el ícono británico Central Cee. Esta entrega estelar presenta su cadena insignia en oro rosa de 18k engastada con pavé de diamantes VVS junto a la chaqueta de plumón Decoded 2.0 confeccionada en alta densidad para la campaña exclusiva.
      </p>
      <ul class="fi-specs">
        <li>CADENA CUBAN LINK 18K ROSE GOLD CON VVS DIAMOND PAVÉ 3D</li>
        <li>MEDALLÓN EMBLEMÁTICO CENTRAL CEE CON CORONA Y RELIEVES</li>
        <li>CHAQUETA DE PLUMÓN RDS 700-FILL CON BORDADO SOLARILUXURY</li>
        <li>RIBETES REFLECTANTES SCOTCHLITE 3M DE ALTA VISIBILIDAD</li>
        <li>CERTIFICADO NUMERADO DE AUTENTICIDAD SOLARILUXURY × CC</li>
      </ul>
      <div class="fi-price">${{ hero_prod.precio|floatformat:"0" }} CLP</div>
      <div class="fi-price-usd">≈ ${{ hero_prod.precio_usd }} USD</div>
      <a href="{% url 'detalle_producto' hero_prod.id %}" class="fi-cta">
        EXPLORAR PIEZA MAESTRA <span class="fi-cta-arrow">→</span>
      </a>
    </div>
  </div>
</section>
{% endif %}'''

html = html.replace(old_featured, new_featured)

# 9. Update Stores and Footer
html = html.replace('<div class="sc-type">TRAPSTAR {{ loc.tipo }}</div>', '<div class="sc-type">SOLARILUXURY {{ loc.tipo }}</div>')
html = html.replace('Trapstar London × Central Cee. Official streetwear campaign 2026. Prendas de edición limitada con autenticidad garantizada.', 'Solariluxury × Central Cee. Official streetwear collaboration 2026. Prendas de edición limitada con autenticidad garantizada.')
html = html.replace('© 2026 TRAPSTAR LONDON × CENTRAL CEE. ALL RIGHTS RESERVED.', '© 2026 SOLARILUXURY × CENTRAL CEE. ALL RIGHTS RESERVED.')

# 10. Add JavaScript for the switcher
js_switcher = '''
// ── FEATURED 3D CHAIN SWITCHER ─────────────────────────────────
function switchFeaturedMedia(type, btn) {
  const media = document.getElementById('featuredMainMedia');
  if (!media) return;
  document.querySelectorAll('.switch-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  
  media.style.opacity = '0';
  setTimeout(() => {
    if (type === 'chain_3d') {
      media.src = "{% static 'img/central_cee_chain_3d.gif' %}";
    } else if (type === 'central_cee') {
      media.src = "{% static 'img/central_cee_chain.jpg' %}";
    } else if (type === 'puffer') {
      media.src = "{% static 'img/trapstar_puffer_hero.jpg' %}";
    }
    media.style.opacity = '1';
  }, 200);
}
'''
if 'function switchFeaturedMedia' not in html:
    html = html.replace('// ── CAMPAIGN PHOTO PARALLAX', js_switcher + '\n// ── CAMPAIGN PHOTO PARALLAX')

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)
print('Successfully patched inicio.html with 3D chain and Solariluxury!')
