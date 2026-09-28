import re

path_prod = 'mi_proyecto/catalogo/templates/catalogo/productos.html'
with open(path_prod, 'r', encoding='utf-8') as f:
    html = f.read()

# Add Apple CSS to productos.html
apple_prod_css = '''
  /* ======================================================
     APPLE DYNAMIC CONTROLS (EXPANDABLE)
  ====================================================== */
  .apple-control-wrap {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    align-items: center;
    margin-bottom: 32px;
  }
  .apple-pill-btn {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    padding: 12px 24px;
    border-radius: 100px;
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(30px) saturate(190%);
    -webkit-backdrop-filter: blur(30px) saturate(190%);
    border: 1px solid rgba(255, 255, 255, 0.14);
    color: #fff;
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    cursor: pointer;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
    transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    user-select: none;
  }
  .apple-pill-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.3);
    transform: translateY(-2px);
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.7);
  }
  .apple-pill-btn:active {
    transform: scale(0.97);
  }
  .apple-pill-icon {
    font-size: 13px;
    color: var(--accent);
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
    position: relative;
    z-index: 50;
  }
  .apple-expandable-tray.open {
    max-height: 500px;
    opacity: 1;
    transform: translateY(0) scale(1);
    pointer-events: auto;
  }
  .apple-tray-inner {
    padding: 16px 20px;
    border-radius: 20px;
    background: rgba(18, 18, 22, 0.92);
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
    font-family: var(--font-mono);
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
  .apple-crud-add:hover { background: rgba(34, 197, 94, 0.22); }
  .apple-crud-edit {
    background: rgba(59, 130, 246, 0.12);
    border-color: rgba(59, 130, 246, 0.35);
    color: #60a5fa;
  }
  .apple-crud-edit:hover { background: rgba(59, 130, 246, 0.22); }
  .apple-crud-del {
    background: rgba(239, 68, 68, 0.12);
    border-color: rgba(239, 68, 68, 0.35);
    color: #f87171;
  }
  .apple-crud-del:hover { background: rgba(239, 68, 68, 0.22); }
  .apple-crud-search {
    background: rgba(168, 85, 247, 0.12);
    border-color: rgba(168, 85, 247, 0.35);
    color: #c084fc;
  }
  .apple-crud-search:hover { background: rgba(168, 85, 247, 0.22); }
'''

if '.apple-control-wrap' not in html:
    html = html.replace('.vault-hero {', apple_prod_css + '\n  .vault-hero {')

# Replace the CRUD toolbar and category filters in productos.html
old_block_match = re.search(r'<!-- Barra de Controles CRUD.*?<!-- Grid de Productos -->', html, re.DOTALL)
if old_block_match:
    new_block = '''<!-- Apple-Style Dynamic Controls (CRUD & Category Filter) -->
    <div class="apple-control-wrap">
      
      <!-- Botón Didáctico 1: Gestión CRUD Admin -->
      <div style="position: relative;">
        <button type="button" class="apple-pill-btn" id="prodCrudBtn" onclick="toggleAppleTray('prodCrudTray', this)">
          <span class="apple-pill-icon">⚡</span>
          <span>GESTIÓN ADMIN (CRUD)</span>
          <span class="apple-chevron">▼</span>
        </button>

        <div class="apple-expandable-tray" id="prodCrudTray">
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
        <button type="button" class="apple-pill-btn" id="prodCatBtn" onclick="toggleAppleTray('prodCatTray', this)">
          <span class="apple-pill-icon">✦</span>
          <span>CATEGORÍA: {{ categoria_actual }}</span>
          <span class="apple-chevron">▼</span>
        </button>

        <div class="apple-expandable-tray" id="prodCatTray">
          <div class="apple-tray-inner">
            <a href="{% url 'lista_productos' %}" class="cat-pill {% if categoria_actual == 'TODOS' %}active{% endif %}">
              TODOS ({{ total_productos }})
            </a>
            {% for cat in categorias %}
              {% if cat != 'TODOS' %}
              <a href="{% url 'lista_productos' %}?categoria={{ cat }}" class="cat-pill {% if categoria_actual == cat %}active{% endif %}">
                {{ cat }}
              </a>
              {% endif %}
            {% endfor %}
          </div>
        </div>
      </div>

      <!-- Barra de Búsqueda -->
      <form method="GET" action="{% url 'lista_productos' %}" class="search-form" style="margin-left: auto;">
        {% if categoria_actual != 'TODOS' %}
          <input type="hidden" name="categoria" value="{{ categoria_actual }}">
        {% endif %}
        <input type="text" name="q" value="{{ busqueda }}" placeholder="BUSCAR DROP O MODELO..." class="search-input">
        <button type="submit" class="search-btn" title="Buscar">⌕</button>
      </form>

    </div>

    <!-- Grid de Productos -->'''
    html = html[:old_block_match.start()] + new_block + html[old_block_match.end()-len('<!-- Grid de Productos -->'):]

# Add toggle script in productos.html
toggle_js = '''
<script>
function toggleAppleTray(trayId, btn) {
  const tray = document.getElementById(trayId);
  if (!tray) return;
  tray.classList.toggle('open');
  btn.classList.toggle('open');
}
</script>
'''
if 'function toggleAppleTray' not in html:
    html += toggle_js

with open(path_prod, 'w', encoding='utf-8') as f:
    f.write(html)
print('Updated productos.html with Apple dynamic expandable controls!')
