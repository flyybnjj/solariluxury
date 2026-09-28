import re

def apple_design_css():
    css_path = 'mi_proyecto/static/css/trapstar.css'
    with open(css_path, 'r', encoding='utf-8') as f:
        css = f.read()

    # 1. Update Header to Apple Style (Sleek, minimalist, high blur)
    apple_header = """
.luxury-header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  z-index: 1000;
  padding: 0 3rem;
  height: 52px;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(25px) saturate(180%);
  -webkit-backdrop-filter: blur(25px) saturate(180%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 0.4s cubic-bezier(0.25, 1, 0.5, 1);
}

.header-inner {
  max-width: 1720px;
  height: 100%;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-nav {
  display: flex;
  gap: 2.5rem;
  align-items: center;
}

.nav-link {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 0.75rem;
  font-weight: 400;
  letter-spacing: 0.02em;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  transition: color 0.3s ease, opacity 0.3s ease;
}
.nav-link:hover, .nav-link.active {
  color: #fff;
  opacity: 1;
}
.nav-link::after { display: none; } /* Remove old underlines */
"""
    # Use regex to replace the old .luxury-header and related blocks up to .header-actions
    css = re.sub(r'\.luxury-header \{[\s\S]*?\.header-actions \{', apple_header + '\n.header-actions {', css)

    # Make the cart drawer look like an Apple Sheet
    css = css.replace(
        '.cart-drawer {\n  position: fixed;',
        '.cart-drawer {\n  position: fixed;\n  border-radius: 24px 0 0 24px;'
    )

    # Add Apple Transition Overlay CSS
    transition_css = """
/* Apple Style Page Transition Overlay */
.apple-transition-overlay {
  position: fixed;
  top: 0; left: 0; width: 100vw; height: 100vh;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(40px) saturate(200%);
  -webkit-backdrop-filter: blur(40px) saturate(200%);
  z-index: 99999;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.45s cubic-bezier(0.32, 0.72, 0, 1);
  display: flex;
  justify-content: center;
  align-items: center;
}
.apple-transition-overlay.active {
  opacity: 1;
  pointer-events: auto;
}
.apple-transition-spinner {
  width: 44px; height: 44px;
  border: 3px solid rgba(255,255,255,0.1);
  border-top-color: #fff;
  border-radius: 50%;
  animation: appleSpin 1s infinite linear;
}
@keyframes appleSpin { 100% { transform: rotate(360deg); } }
"""
    if '.apple-transition-overlay' not in css:
        css = css + '\n' + transition_css
        
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css)

def apple_design_js():
    js_path = 'mi_proyecto/static/js/trapstar.js'
    with open(js_path, 'r', encoding='utf-8') as f:
        js = f.read()

    # Add the Apple transition logic for product clicks
    transition_logic = """
    // Apple Style Product Selection Animation
    const productCards = document.querySelectorAll('.streetwear-card');
    
    // Create transition overlay dynamically if not exists
    let overlay = document.getElementById('appleTransitionOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'appleTransitionOverlay';
        overlay.className = 'apple-transition-overlay';
        overlay.innerHTML = '<div class="apple-transition-spinner"></div>';
        document.body.appendChild(overlay);
    }

    productCards.forEach(card => {
        // Remove direct inline onclick if exists to avoid immediate jump
        card.removeAttribute('onclick');
        const quickViewBtn = card.querySelector('.btn-card-quickview');
        if (quickViewBtn) quickViewBtn.removeAttribute('onclick');
        
        const goUrl = card.getAttribute('data-url'); // We will inject this via HTML

        const triggerAnimation = (e) => {
            e.stopPropagation();
            if(!goUrl) return;
            playUiClickSound();
            
            // 1. Pop the card slightly like an iOS icon
            card.style.transform = 'scale(1.08)';
            card.style.zIndex = '50';
            
            // 2. Fade in the Apple-style glass overlay
            overlay.classList.add('active');
            
            // 3. Navigate after animation
            setTimeout(() => {
                window.location.href = goUrl;
            }, 450);
        };

        card.addEventListener('click', triggerAnimation);
        if (quickViewBtn) quickViewBtn.addEventListener('click', triggerAnimation);
    });
"""
    if 'Apple Style Product Selection Animation' not in js:
        # Insert at the end of init()
        js = js.replace('handleScroll();\n  }', transition_logic + '\n    handleScroll();\n  }')
        
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js)

def apple_design_html():
    html_path = 'mi_proyecto/catalogo/templates/catalogo/inicio.html'
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Inject data-url into cards so our JS handles the animation instead of inline onclick
    html = re.sub(
        r'onclick="window\.location\.href=\'\{% url \'detalle_producto\' prod\.id %\}\'"',
        r'data-url="{% url \'detalle_producto\' prod.id %}"',
        html
    )
    html = re.sub(
        r'onclick="event\.stopPropagation\(\); window\.location\.href=\'\{% url \'detalle_producto\' prod\.id %\}\'"',
        r'',
        html
    )
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)


if __name__ == '__main__':
    apple_design_css()
    apple_design_js()
    apple_design_html()
    print("Apple UI updates applied.")
