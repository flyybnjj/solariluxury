import re

# 1. Update mi_proyecto/catalogo/templates/catalogo/inicio.html
path_inicio = 'mi_proyecto/catalogo/templates/catalogo/inicio.html'
with open(path_inicio, 'r', encoding='utf-8') as f:
    html = f.read()

# Add CSS for Apple Dynamic Controls
apple_css = '''
    /* ======================================================
       APPLE DYNAMIC PILL CONTROLS (EXPANDABLE)
    ====================================================== */
    .apple-control-wrap {
      display: flex;
      flex-direction: column;
      gap: 14px;
      margin-bottom: 36px;
    }
    .apple-pill-btn {
      display: inline-flex;
      align-items: center;
      gap: 12px;
      padding: 12px 26px;
      border-radius: 100px;
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(30px) saturate(190%);
      -webkit-backdrop-filter: blur(30px) saturate(190%);
      border: 1px solid rgba(255, 255, 255, 0.14);
      color: #fff;
      font-family: 'Space Mono', monospace;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      cursor: pointer;
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
      transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
      width: fit-content;
      user-select: none;
    }
    .apple-pill-btn:hover {
      background: rgba(255, 255, 255, 0.1);
      border-color: rgba(255, 255, 255, 0.32);
      transform: translateY(-2px);
      box-shadow: 0 12px 36px rgba(0, 0, 0, 0.7);
    }
    .apple-pill-btn:active {
      transform: scale(0.97);
    }
    .apple-pill-icon {
      font-size: 13px;
      color: #e60000;
    }
    .apple-chevron {
      font-size: 9px;
      color: rgba(255, 255, 255, 0.45);
      transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .apple-pill-btn.open .apple-chevron {
      transform: rotate(180deg);
      color: #fff;
    }
    .apple-expandable-tray {
      max-height: 0;
      opacity: 0;
      overflow: hidden;
      transform: translateY(-8px) scale(0.98);
      transform-origin: top left;
      transition: max-height 0.45s cubic-bezier(0.16, 1, 0.3, 1),
                  opacity 0.35s ease,
                  transform 0.45s cubic-bezier(0.16, 1, 0.3, 1);
      pointer-events: none;
      margin-top: 8px;
    }
    .apple-expandable-tray.open {
      max-height: 400px;
      opacity: 1;
      transform: translateY(0) scale(1);
      pointer-events: auto;
    }
    .apple-tray-inner {
      padding: 16px 20px;
      border-radius: 20px;
      background: rgba(18, 18, 22, 0.9);
      backdrop-filter: blur(40px) saturate(200%);
      -webkit-backdrop-filter: blur(40px) saturate(200%);
      border: 1px solid rgba(255, 255, 255, 0.14);
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(255, 255, 255, 0.05);
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      width: fit-content;
      max-width: 100%;
    }
    .apple-crud-item {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 18px;
      border-radius: 12px;
      font-family: 'Space Mono', monospace;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      text-decoration: none;
      border: 1px solid;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .apple-crud-item:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
    }
    .apple-crud-add {
      background: rgba(34, 197, 94, 0.12);
      border-color: rgba(34, 197, 94, 0.35);
      color: #4ade80;
    }
    .apple-crud-add:hover {
      background: rgba(34, 197, 94, 0.22);
    }
    .apple-crud-edit {
      background: rgba(59, 130, 246, 0.12);
      border-color: rgba(59, 130, 246, 0.35);
      color: #60a5fa;
    }
    .apple-crud-edit:hover {
      background: rgba(59, 130, 246, 0.22);
    }
    .apple-crud-del {
      background: rgba(239, 68, 68, 0.12);
      border-color: rgba(239, 68, 68, 0.35);
      color: #f87171;
    }
    .apple-crud-del:hover {
      background: rgba(239, 68, 68, 0.22);
    }
    .apple-crud-search {
      background: rgba(168, 85, 247, 0.12);
      border-color: rgba(168, 85, 247, 0.35);
      color: #c084fc;
    }
    .apple-crud-search:hover {
      background: rgba(168, 85, 247, 0.22);
    }
    .apple-cat-chip {
      padding: 9px 20px;
      border-radius: 100px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.09);
      color: rgba(255, 255, 255, 0.65);
      font-family: 'Space Mono', monospace;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      cursor: pointer;
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .apple-cat-chip:hover {
      color: #fff;
      background: rgba(255, 255, 255, 0.1);
      border-color: rgba(255, 255, 255, 0.25);
    }
    .apple-cat-chip.active {
      color: #000;
      background: #fff;
      border-color: #fff;
      box-shadow: 0 4px 16px rgba(255, 255, 255, 0.25);
    }
'''
if '.apple-control-wrap' not in html:
    html = html.replace('.catalog-header {', apple_css + '\n    .catalog-header {')

# Replace Old Catalog CRUD & Filter in Section 6
old_catalog_controls = re.search(r'<!-- CRUD Actions -->.*?<!-- Grid -->', html, re.DOTALL)
if old_catalog_controls:
    new_catalog_controls = '''<!-- Apple-Style Dynamic Controls (CRUD & Category Filter) -->
    <div class="apple-control-wrap sr">
      
      <!-- Botón Didáctico 1: Gestión CRUD Admin -->
      <div style="position: relative;">
        <button type="button" class="apple-pill-btn" id="crudPillBtn" onclick="toggleAppleTray('crudTray', this)">
          <span class="apple-pill-icon">⚡</span>
          <span>GESTIÓN ADMIN (CRUD)</span>
          <span class="apple-chevron">▼</span>
        </button>

        <div class="apple-expandable-tray" id="crudTray">
          <div class="apple-tray-inner">
            <a href="{% url 'admin:catalogo_producto_add' %}" class="apple-crud-item apple-crud-add" target="_blank">
              <span>＋</span> AGREGAR PRODUCTO
            </a>
            <a href="{% url 'admin:catalogo_producto_changelist' %}" class="apple-crud-item apple-crud-edit" target="_blank">
              <span>✏</span> MODIFICAR REGISTRO
            </a>
            <a href="{% url 'admin:catalogo_producto_changelist' %}" class="apple-crud-item apple-crud-del" target="_blank">
              <span>✕</span> ELIMINAR REGISTRO
            </a>
            <a href="{% url 'admin:catalogo_producto_changelist' %}" class="apple-crud-item apple-crud-search" target="_blank">
              <span>⌕</span> BUSCAR EN BD
            </a>
          </div>
        </div>
      </div>

      <!-- Botón Didáctico 2: Filtro de Categorías Tipo Apple -->
      <div style="position: relative;">
        <button type="button" class="apple-pill-btn" id="filterPillBtn" onclick="toggleAppleTray('filterTray', this)">
          <span class="apple-pill-icon">✦</span>
          <span id="currentCatLabel">FILTRAR CATEGORÍA: TODOS</span>
          <span class="apple-chevron">▼</span>
        </button>

        <div class="apple-expandable-tray" id="filterTray">
          <div class="apple-tray-inner">
            <button type="button" class="apple-cat-chip active" data-cat="TODOS" onclick="selectAppleCategory('TODOS', this)">
              TODOS
            </button>
            {% for cat in categorias %}
              {% if cat != "TODOS" %}
              <button type="button" class="apple-cat-chip" data-cat="{{ cat }}" onclick="selectAppleCategory('{{ cat }}', this)">
                {{ cat }}
              </button>
              {% endif %}
            {% endfor %}
          </div>
        </div>
      </div>

    </div>

    <!-- Grid -->'''
    html = html[:old_catalog_controls.start()] + new_catalog_controls + html[old_catalog_controls.end()-len('<!-- Grid -->'):]

# Replace Old Stores CRUD in Section 7
old_stores_crud = re.search(r'<div class="stores-crud sr">.*?</div>', html, re.DOTALL)
if old_stores_crud:
    new_stores_crud = '''<!-- Botón Didáctico CRUD Locales Tipo Apple -->
    <div class="apple-control-wrap sr" style="margin-bottom: 32px;">
      <div style="position: relative;">
        <button type="button" class="apple-pill-btn" id="storesCrudPillBtn" onclick="toggleAppleTray('storesCrudTray', this)">
          <span class="apple-pill-icon">⚡</span>
          <span>ADMIN LOCALES (CRUD)</span>
          <span class="apple-chevron">▼</span>
        </button>

        <div class="apple-expandable-tray" id="storesCrudTray">
          <div class="apple-tray-inner">
            <a href="{% url 'admin:locales_local_add' %}" class="apple-crud-item apple-crud-add" target="_blank">
              <span>＋</span> AGREGAR SUCURSAL
            </a>
            <a href="{% url 'admin:locales_local_changelist' %}" class="apple-crud-item apple-crud-edit" target="_blank">
              <span>✏</span> MODIFICAR LOCAL
            </a>
            <a href="{% url 'admin:locales_local_changelist' %}" class="apple-crud-item apple-crud-del" target="_blank">
              <span>✕</span> ELIMINAR LOCAL
            </a>
            <a href="{% url 'admin:locales_local_changelist' %}" class="apple-crud-item apple-crud-search" target="_blank">
              <span>⌕</span> BUSCAR EN BD
            </a>
          </div>
        </div>
      </div>
    </div>'''
    html = html[:old_stores_crud.start()] + new_stores_crud + html[old_stores_crud.end():]

# Add JavaScript for Apple controls
apple_js = '''
// ── APPLE DYNAMIC ISLAND CONTROLS ─────────────────────────────
function toggleAppleTray(trayId, btn) {
  const tray = document.getElementById(trayId);
  if (!tray) return;
  const isOpen = tray.classList.contains('open');
  tray.classList.toggle('open');
  btn.classList.toggle('open');
}

function selectAppleCategory(cat, btn) {
  document.querySelectorAll('.apple-cat-chip').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
  const label = document.getElementById('currentCatLabel');
  if (label) {
    label.textContent = cat === 'TODOS' ? 'FILTRAR CATEGORÍA: TODOS' : `FILTRAR CATEGORÍA: ${cat}`;
  }
  
  // Filter product grid
  document.querySelectorAll('.prod-card').forEach(card => {
    const match = cat === 'TODOS' || card.dataset.cat === cat;
    card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    if (match) {
      card.style.display = '';
      setTimeout(() => { card.style.opacity = '1'; card.style.transform = ''; }, 10);
    } else {
      card.style.opacity = '0';
      card.style.transform = 'scale(0.95)';
      setTimeout(() => { if (card.style.opacity === '0') card.style.display = 'none'; }, 300);
    }
  });
}
'''
if 'function toggleAppleTray' not in html:
    html = html.replace('// ── LOADER', apple_js + '\n// ── LOADER')

with open(path_inicio, 'w', encoding='utf-8') as f:
    f.write(html)
print('Updated inicio.html with Apple dynamic expandable controls!')
