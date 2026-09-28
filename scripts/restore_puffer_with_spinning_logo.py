import os

path = 'mi_proyecto/catalogo/templates/catalogo/inicio.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# Add CSS for floating spinning emblem and chain badge
css_emblem = '''
    /* Floating Spinning Emblem and Chain Badge */
    .floating-spin-emblem {
      position: absolute;
      top: 24px; right: 24px;
      z-index: 10;
      width: 110px; height: 110px;
      border-radius: 50%;
      background: rgba(0, 0, 0, 0.65);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.18);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      box-shadow: 0 12px 36px rgba(0, 0, 0, 0.8), 0 0 25px rgba(230, 0, 0, 0.2);
      animation: floatBadge 4s ease-in-out infinite;
      pointer-events: none;
    }
    .floating-spin-emblem img.spin-gif {
      width: 76px; height: 76px;
      object-fit: contain;
      filter: drop-shadow(0 0 10px rgba(255, 255, 255, 0.35));
    }
    .spin-label {
      font-family: 'Space Mono', monospace;
      font-size: 7px;
      letter-spacing: 0.18em;
      color: rgba(255, 255, 255, 0.7);
      text-transform: uppercase;
      margin-top: -2px;
    }
    @keyframes floatBadge {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-8px); }
    }

    .floating-chain-badge {
      position: absolute;
      bottom: 24px; left: 24px;
      z-index: 10;
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 8px 18px 8px 8px;
      border-radius: 100px;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.15);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
    }
    .floating-chain-badge img {
      width: 44px; height: 44px;
      border-radius: 50%;
      object-fit: cover;
      border: 1px solid rgba(255, 255, 255, 0.25);
      box-shadow: 0 0 12px rgba(230, 0, 0, 0.3);
    }
    .chain-badge-text {
      display: flex;
      flex-direction: column;
    }
    .chain-badge-sub {
      font-family: 'Space Mono', monospace;
      font-size: 8px;
      letter-spacing: 0.15em;
      color: #ff6b6b;
      text-transform: uppercase;
    }
    .chain-badge-title {
      font-family: 'Space Mono', monospace;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.1em;
      color: #fff;
    }
'''

# Replace the section 5 CSS if already modified or insert it
if '.floating-spin-emblem' not in html:
    html = html.replace('.featured-info-col {', css_emblem + '\n    .featured-info-col {')

# Find and replace the whole featured section (Section 5)
# Target from <section class="featured-section to </section>
import re
pattern = r'<section class="featured-section.*?</section>'

new_section = '''<section class="featured-section sr" id="featured">
  <div class="featured-inner">
    <!-- Columna Izquierda: Chaqueta Puffer Oficial con Logo Girando y Cadena Flotante -->
    <div class="featured-img-col" id="featuredCol">

      <!-- GIF del Logo Girando (Rescatado y Flotando) -->
      <div class="floating-spin-emblem" title="Solariluxury Authentic Emblem">
        <img src="{% static 'img/logo_spin.gif' %}" alt="Solariluxury Spinning 3D Logo" class="spin-gif">
        <span class="spin-label">SOLARILUXURY</span>
      </div>

      <!-- Badge Flotante con la Cadena de Central Cee -->
      <div class="floating-chain-badge" title="Central Cee Signature Chain">
        <img src="{% static 'img/central_cee_chain_3d.gif' %}" alt="Central Cee Chain">
        <div class="chain-badge-text">
          <span class="chain-badge-sub">CENTRAL CEE CAMPAIGN</span>
          <span class="chain-badge-title">SIGNATURE VVS CHAIN</span>
        </div>
      </div>

      <!-- Imagen Principal: Chaqueta Puffer Hyperdrive -->
      <img src="{% static hero_prod.imagen %}" alt="{{ hero_prod.nombre }}">
      <div class="featured-img-overlay"></div>
    </div>

    <!-- Columna Derecha: Información del Producto (Puffer Hyperdrive) -->
    <div class="featured-info-col">
      <div class="fi-tag">HERO DROP — CAMPERAS Y PUFFERS</div>
      <h2 class="fi-title">SOLARILUXURY × CENTRAL CEE — DECODED 2.0 PUFFER 'HYPERDRIVE'</h2>
      <p class="fi-subtitle">PIEZA MAESTRA CAMPAÑA OFICIAL 2026</p>
      <p class="fi-desc">
        Chaqueta acolchada de plumón 700-fill con ribetes reflectantes 3M Scotchlite y bordado arqueado Solariluxury en chenille de alta densidad sobre el pecho. Usada por Central Cee en la campaña oficial.
      </p>
      <ul class="fi-specs">
        <li>RELLENO 700-FILL RDS GOOSE DOWN TÉRMICO</li>
        <li>BORDADO ARQUEADO GÓTICO SOLARILUXURY EN CHENILLE 3D</li>
        <li>RIBETES REFLECTANTES 3M SCOTCHLITE DE ALTA VISIBILIDAD</li>
        <li>FORRO INTERIOR DE SATÉN ACOLCHADO CON BOLSILLO SECRETO</li>
        <li>CIERRE CROMADO BIDIRECCIONAL CON TIRADOR 'T' STAR</li>
      </ul>
      <div class="fi-price">${{ hero_prod.precio|floatformat:"0" }} CLP</div>
      <div class="fi-price-usd">≈ ${{ hero_prod.precio_usd }} USD</div>
      <a href="{% url 'detalle_producto' hero_prod.id %}" class="fi-cta">
        VER PRODUCTO <span class="fi-cta-arrow">→</span>
      </a>
    </div>
  </div>
</section>'''

html = re.sub(pattern, new_section, html, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print('Section 5 successfully restored with Puffer product + Spinning Logo GIF + Floating Chain badge!')
