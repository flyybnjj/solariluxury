/**
 * TRAPSTAR LONDON x CENTRAL CEE — Interactive Campaign & Store Engine
 * Layered 3-Phase Scroll Timeline Engine + Streetwear E-Commerce Subsystems:
 * - Phase 1 (0% - 30%): Central Cee Scroll Scrubbing Sequence (30 Frames)
 * - Phase 2 (30% - 50%): Cinematographic Model Exit into London Midnight Depth
 * - Phase 3 (50% - 100%): Decoded Puffer Emergence, In-Stage Action HUD & 3M Hotspots
 * - Slide-Over Luxury Cart Drawer with Dynamic Free Shipping Meter & Promo Codes
 * - Web Audio API London Drill Ambient Sound Engine & UI Sound Effects
 * - Streetwear Catalog Category Filter & Quick View Engine
 */

(function () {
  'use strict';

  // Configuration
  const TOTAL_CC_FRAMES = 30;
  const CC_FRAME_BASE = 'static/img/central_cee_sequence/cc_';
  const FREE_SHIPPING_THRESHOLD = 150.00;

  // DOM Elements - Hero Stage
  const experienceContainer = document.getElementById('experiencePin');
  const bgModelLayer = document.getElementById('bgModelLayer');
  const modelVideoWrapper = document.getElementById('modelVideoWrapper');
  const ccImg = document.getElementById('ccImg');
  const bgDarkOverlay = document.getElementById('bgDarkOverlay');
  const scrollBlurOverlay = document.getElementById('scrollBlurOverlay');
  const flankLeft = document.getElementById('flankLeft');
  const flankRight = document.getElementById('flankRight');
  const scrollCue = document.getElementById('scrollCue');
  const heroCcInteractive = document.getElementById('heroCcInteractive');

  // Product Stage & HUD
  const productCanvasLayer = document.getElementById('productCanvasLayer');
  const heroProductImg = document.getElementById('heroProductImg');
  const productStageHud = document.getElementById('productStageHud');
  const productHotspots = document.getElementById('productHotspots');
  const railBar = document.getElementById('railBar');

  // Milestones
  const m1 = document.getElementById('m1');
  const m2 = document.getElementById('m2');
  const m3 = document.getElementById('m3');

  // Cart Elements
  const bagBtn = document.getElementById('bagBtn');
  const headerBagCount = document.getElementById('headerBagCount');
  const cartBackdrop = document.getElementById('cartBackdrop');
  const cartDrawer = document.getElementById('cartDrawer');
  const cartCloseBtn = document.getElementById('cartCloseBtn');
  const cartCountLabel = document.getElementById('cartCountLabel');
  const shippingMeterText = document.getElementById('shippingMeterText');
  const shippingRemainVal = document.getElementById('shippingRemainVal');
  const shippingMeterFill = document.getElementById('shippingMeterFill');
  const cartItemsList = document.getElementById('cartItemsList');
  const cartEmptyState = document.getElementById('cartEmptyState');
  const cartFooter = document.getElementById('cartFooter');
  const promoInput = document.getElementById('promoInput');
  const promoApplyBtn = document.getElementById('promoApplyBtn');
  const promoDiscountMsg = document.getElementById('promoDiscountMsg');
  const cartSubtotalVal = document.getElementById('cartSubtotalVal');
  const discountLine = document.getElementById('discountLine');
  const cartDiscountVal = document.getElementById('cartDiscountVal');
  const cartTotalVal = document.getElementById('cartTotalVal');
  const checkoutBtn = document.getElementById('checkoutBtn');

  // Central Cee Archive Quote Modal
  const ccQuoteBtn = document.getElementById('ccQuoteBtn');
  const quoteModalBackdrop = document.getElementById('quoteModalBackdrop');
  const quoteCloseBtn = document.getElementById('quoteCloseBtn');

  // Audio Engine Elements
  const audioToggleBtn = document.getElementById('audioToggleBtn');

  // Frame Cache & State
  const ccFrames = [];
  let lastCcFrame = -1;
  let currentScrollProgress = 0;

  // Shopping Bag State
  let cartState = {
    items: [
      {
        id: 1,
        title: "DECODED 2.0 PUFFER 'HYPERDRIVE'",
        price: 395.00,
        priceCLP: 379990,
        size: "L",
        color: "PITCH BLACK / 3M",
        qty: 1,
        img: "static/img/trapstar_puffer_hero.jpg"
      }
    ],
    discountPercent: 0,
    promoCodeApplied: null
  };

  // Web Audio Synth Variables
  let audioCtx = null;
  let isAudioPlaying = false;
  let drillOsc1 = null;
  let drillOsc2 = null;
  let drillGain = null;
  let drillNoise = null;

  function getStaticBase() {
    const link = document.querySelector('link[href*="trapstar.css"]');
    if (link && link.getAttribute('href')) {
      const href = link.getAttribute('href');
      const idx = href.indexOf('static/');
      if (idx !== -1) {
        return href.substring(0, idx + 7);
      }
    }
    return window.location.pathname.includes('/solariluxury') ? '/solariluxury/static/' : 'static/';
  }

  function resolveAssetUrl(src) {
    if (!src) return '';
    if (src.startsWith('http://') || src.startsWith('https://')) return src;
    const base = getStaticBase();
    if (src.startsWith('static/')) {
      return base + src.substring(7);
    }
    if (src.startsWith('/static/')) {
      return base + src.substring(8);
    }
    if (src.includes('/static/')) {
      const idx = src.indexOf('/static/');
      return base + src.substring(idx + 8);
    }
    return base + src;
  }

  /**
   * Initialize and preload Central Cee 30 frames
   */
  function preloadCentralCeeFrames() {
    const staticBase = getStaticBase();
    for (let i = 1; i <= TOTAL_CC_FRAMES; i++) {
      const img = new Image();
      const numStr = String(i).padStart(2, '0');
      img.src = `${staticBase}img/central_cee_sequence/cc_${numStr}.webp`;
      ccFrames.push(img);
    }
  }

  /**
   * Update Central Cee frame based on scroll scrub
   */
  
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


  /**
   * Master 3-Phase Scroll Computation
   */
  function handleScroll() {
    if (!experienceContainer) return;

    const rect = experienceContainer.getBoundingClientRect();
    const containerTop = window.scrollY + rect.top;
    const containerHeight = experienceContainer.offsetHeight - window.innerHeight;
    
    if (containerHeight <= 0) return;

    const progress = Math.max(0, Math.min(1, (window.scrollY - containerTop) / containerHeight));
    currentScrollProgress = progress;

    // Update Progress Rail
    if (railBar) {
      railBar.style.height = `${(progress * 100).toFixed(1)}%`;
    }

    // =========================================================================
    // PHASE 1: Central Cee Attitude & Scroll Sequence (0% to 30%)
    // =========================================================================
    if (progress <= 0.30) {
      const tTilt = progress / 0.30;
      const frameIdx = tTilt * (TOTAL_CC_FRAMES - 1);
      updateCcFrame(frameIdx);

      // Flank text & quote trigger fade out smoothly
      const flankOp = Math.max(0, 1.0 - (progress / 0.15));
      if (flankLeft) flankLeft.style.opacity = flankOp.toFixed(3);
      if (flankRight) flankRight.style.opacity = flankOp.toFixed(3);
      if (scrollCue) scrollCue.style.opacity = flankOp.toFixed(3);
      if (heroCcInteractive) heroCcInteractive.style.opacity = flankOp.toFixed(3);

      // Model layer visible
      if (bgModelLayer) {
        bgModelLayer.style.display = 'flex';
        bgModelLayer.style.opacity = '1';
        bgModelLayer.style.visibility = 'visible';
      }
      if (modelVideoWrapper) {
        modelVideoWrapper.style.transform = 'scale(1.0)';
      }
      
      if (scrollBlurOverlay) {
        const blurVal = (progress / 0.30) * 15; // Max 15px blur
        scrollBlurOverlay.style.backdropFilter = `blur(${blurVal}px)`;
        scrollBlurOverlay.style.webkitBackdropFilter = `blur(${blurVal}px)`;
      }

      if (bgDarkOverlay) {
        bgDarkOverlay.style.opacity = '0';
      }

      // Product stage hidden
      if (productCanvasLayer) {
        productCanvasLayer.classList.remove('active');
      }

      // Milestones hidden
      if (m1) m1.classList.remove('active');
      if (m2) m2.classList.remove('active');
      if (m3) m3.classList.remove('active');
    }
    // =========================================================================
    // PHASE 2: Cinematographic Model Exit (30% to 50%)
    // =========================================================================
    else if (progress > 0.30 && progress < 0.50) {
      updateCcFrame(TOTAL_CC_FRAMES - 1);

      const tExit = (progress - 0.30) / 0.20; // 0.0 to 1.0
      const modelScale = 1.0 - (0.08 * tExit);
      const modelOp = 1.0 - tExit;
      const darkOp = tExit;

      if (bgModelLayer) {
        bgModelLayer.style.display = 'flex';
        bgModelLayer.style.opacity = modelOp.toFixed(3);
        bgModelLayer.style.visibility = 'visible';
      }
      if (modelVideoWrapper) {
        modelVideoWrapper.style.transform = `scale(${modelScale.toFixed(4)})`;
      }
      
      if (scrollBlurOverlay) {
        const blurVal = (progress / 0.30) * 15; // Max 15px blur
        scrollBlurOverlay.style.backdropFilter = `blur(${blurVal}px)`;
        scrollBlurOverlay.style.webkitBackdropFilter = `blur(${blurVal}px)`;
      }

      if (bgDarkOverlay) {
        bgDarkOverlay.style.opacity = darkOp.toFixed(3);
      }

      if (flankLeft) flankLeft.style.opacity = '0';
      if (flankRight) flankRight.style.opacity = '0';
      if (scrollCue) scrollCue.style.opacity = '0';
      if (heroCcInteractive) heroCcInteractive.style.opacity = '0';

      if (productCanvasLayer) {
        productCanvasLayer.classList.remove('active');
      }
      if (m1) m1.classList.remove('active');
      if (m2) m2.classList.remove('active');
      if (m3) m3.classList.remove('active');
    }
    // =========================================================================
    // PHASE 3: Emergence of Decoded Puffer & Interactive Stage (50% to 100%)
    // =========================================================================
    else {
      // Model completely gone
      if (bgModelLayer) {
        bgModelLayer.style.opacity = '0';
        bgModelLayer.style.visibility = 'hidden';
        bgModelLayer.style.display = 'none';
      }

      // Product layer active
      if (productCanvasLayer) {
        productCanvasLayer.classList.add('active');
      }

      // Synchronized Editorial Milestones
      if (progress >= 0.50 && progress < 0.68) {
        if (m1) m1.classList.add('active');
        if (m2) m2.classList.remove('active');
        if (m3) m3.classList.remove('active');
      } else if (progress >= 0.68 && progress < 0.85) {
        if (m1) m1.classList.remove('active');
        if (m2) m2.classList.add('active');
        if (m3) m3.classList.remove('active');
      } else {
        if (m1) m1.classList.remove('active');
        if (m2) m2.classList.remove('active');
        if (m3) m3.classList.add('active');
      }
    }
  }

  /**
   * HUD Action Switcher for Product Stage
   */
  function setupStageHud() {
    const hudButtons = document.querySelectorAll('.hud-btn');
    if (!hudButtons.length || !heroProductImg) return;

    const viewImages = {
      puffer: resolveAssetUrl('img/trapstar_puffer_hero.jpg'),
      reflective: resolveAssetUrl('img/trapstar_3m_flash.jpg'),
      chenille: resolveAssetUrl('img/trapstar_chenille_texture.jpg'),
      interior: resolveAssetUrl('img/trapstar_puffer_open.jpg')
    };

    hudButtons.forEach(btn => {
      btn.addEventListener('click', function () {
        playUiClickSound();
        hudButtons.forEach(b => b.classList.remove('active'));
        this.classList.add('active');

        const mode = this.getAttribute('data-action');
        if (viewImages[mode]) {
          heroProductImg.style.opacity = '0.3';
          setTimeout(() => {
            heroProductImg.src = viewImages[mode];
            heroProductImg.style.opacity = '1';
          }, 150);
        }
      });
    });
  }

  /**
   * Hotspot Telemetry Pins Interaction
   */
  function setupHotspots() {
    const pins = document.querySelectorAll('.hotspot-item');
    pins.forEach(pin => {
      pin.addEventListener('click', function (e) {
        e.stopPropagation();
        playUiClickSound();
        const wasActive = this.classList.contains('active');
        pins.forEach(p => p.classList.remove('active'));
        if (!wasActive) this.classList.add('active');
      });
    });

    document.addEventListener('click', () => {
      pins.forEach(p => p.classList.remove('active'));
    });
  }

  /**
   * Luxury Shopping Bag System
   */
  function updateCartUI() {
    if (!cartItemsList) return;

    const totalCount = cartState.items.reduce((sum, item) => sum + item.qty, 0);
    const subtotal = cartState.items.reduce((sum, item) => sum + (item.price * item.qty), 0);
    
    // Update Badge
    if (headerBagCount) headerBagCount.textContent = `(${totalCount})`;
    if (cartCountLabel) cartCountLabel.textContent = `(${totalCount})`;

    // Free Shipping Meter
    if (shippingMeterText && shippingMeterFill) {
      if (subtotal >= FREE_SHIPPING_THRESHOLD) {
        shippingMeterText.innerHTML = `🎉 <span class="highlight">COMPLIMENTARY WORLDWIDE EXPRESS SHIPPING UNLOCKED</span>`;
        shippingMeterFill.style.width = '100%';
      } else {
        const remaining = (FREE_SHIPPING_THRESHOLD - subtotal).toFixed(2);
        const percent = Math.min(100, (subtotal / FREE_SHIPPING_THRESHOLD) * 100);
        shippingMeterText.innerHTML = `Add <span class="highlight">$${remaining} USD</span> more for Free Worldwide Courier Shipping`;
        shippingMeterFill.style.width = `${percent.toFixed(0)}%`;
      }
    }

    // Render Items
    if (totalCount === 0) {
      if (cartItemsList) cartItemsList.style.display = 'none';
      if (cartEmptyState) cartEmptyState.style.display = 'flex';
      if (cartFooter) cartFooter.style.display = 'none';
    } else {
      if (cartItemsList) cartItemsList.style.display = 'flex';
      if (cartEmptyState) cartEmptyState.style.display = 'none';
      if (cartFooter) cartFooter.style.display = 'flex';

      cartItemsList.innerHTML = cartState.items.map((item, idx) => `
        <div class="cart-item" data-id="${item.id}">
          <div class="cart-item-img-wrap">
            <img src="${resolveAssetUrl(item.img)}" alt="${item.title}" class="cart-item-img">
          </div>
          <div class="cart-item-info">
            <div class="cart-item-header">
              <h3 class="cart-item-title">${item.title}</h3>
              <span class="cart-item-price">$${(item.price * item.qty).toFixed(2)}</span>
            </div>
            <span class="cart-item-shade">Size: ${item.size} • ${item.color || 'Authentic'}</span>
            <div class="cart-item-controls">
              <div class="cart-qty-stepper">
                <button class="qty-btn btn-minus" data-idx="${idx}" aria-label="Decrease quantity">−</button>
                <span class="qty-val">${item.qty}</span>
                <button class="qty-btn btn-plus" data-idx="${idx}" aria-label="Increase quantity">+</button>
              </div>
              <button class="cart-item-remove btn-remove" data-idx="${idx}" aria-label="Remove item">REMOVE</button>
            </div>
          </div>
        </div>
      `).join('');

      // Add event listeners to stepper buttons
      cartItemsList.querySelectorAll('.btn-minus').forEach(btn => {
        btn.addEventListener('click', function () {
          const idx = parseInt(this.getAttribute('data-idx'));
          if (cartState.items[idx].qty > 1) {
            cartState.items[idx].qty -= 1;
          } else {
            cartState.items.splice(idx, 1);
          }
          playUiClickSound();
          updateCartUI();
        });
      });

      cartItemsList.querySelectorAll('.btn-plus').forEach(btn => {
        btn.addEventListener('click', function () {
          const idx = parseInt(this.getAttribute('data-idx'));
          cartState.items[idx].qty += 1;
          playUiClickSound();
          updateCartUI();
        });
      });

      cartItemsList.querySelectorAll('.btn-remove').forEach(btn => {
        btn.addEventListener('click', function () {
          const idx = parseInt(this.getAttribute('data-idx'));
          cartState.items.splice(idx, 1);
          playUiClickSound();
          updateCartUI();
        });
      });
    }

    // Totals
    const discountAmount = subtotal * cartState.discountPercent;
    const finalTotal = subtotal - discountAmount;

    if (cartSubtotalVal) cartSubtotalVal.textContent = `$${subtotal.toFixed(2)} USD`;
    if (discountLine && cartDiscountVal) {
      if (cartState.discountPercent > 0) {
        discountLine.style.display = 'flex';
        cartDiscountVal.textContent = `-$${discountAmount.toFixed(2)} USD`;
      } else {
        discountLine.style.display = 'none';
      }
    }
    if (cartTotalVal) cartTotalVal.textContent = `$${finalTotal.toFixed(2)} USD`;
  }

  function openCart() {
    if (cartDrawer && cartBackdrop) {
      cartDrawer.classList.add('open');
      cartBackdrop.classList.add('open');
      document.body.style.overflow = 'hidden';
      playUiClickSound();
    }
  }

  function closeCart() {
    if (cartDrawer && cartBackdrop) {
      cartDrawer.classList.remove('open');
      cartBackdrop.classList.remove('open');
      document.body.style.overflow = '';
      playUiClickSound();
    }
  }

  function addItemToCart(product) {
    const existing = cartState.items.find(i => i.id === product.id && i.size === product.size);
    if (existing) {
      existing.qty += 1;
    } else {
      cartState.items.push({
        id: product.id,
        title: product.title,
        price: product.price,
        size: product.size || "L",
        color: product.color || "SOLARILUXURY ARCHIVE",
        qty: 1,
        img: product.img
      });
    }
    updateCartUI();
    openCart();
  }

  /**
   * Promo Codes Engine
   */
  function setupPromoCodes() {
    if (!promoApplyBtn || !promoInput || !promoDiscountMsg) return;

    promoApplyBtn.addEventListener('click', () => {
      const code = promoInput.value.trim().toUpperCase();
      playUiClickSound();

      if (code === 'CCEE' || code === 'CENTRALCEE') {
        cartState.discountPercent = 0.15;
        cartState.promoCodeApplied = 'CCEE';
        promoDiscountMsg.textContent = '✓ 15% CENTRAL CEE CAMPAIGN DISCOUNT APPLIED';
        promoDiscountMsg.style.color = '#00f0ff';
      } else if (code === 'SOLARI' || code === 'SOLARILUXURY' || code === 'VIP10' || code === 'TRAPSTAR') {
        cartState.discountPercent = 0.10;
        cartState.promoCodeApplied = 'SOLARILUXURY';
        promoDiscountMsg.textContent = '✓ 10% SOLARILUXURY VIP ACCESS DISCOUNT APPLIED';
        promoDiscountMsg.style.color = '#00f0ff';
      } else if (code === 'SYNA10') {
        cartState.discountPercent = 0.10;
        cartState.promoCodeApplied = 'SYNA10';
        promoDiscountMsg.textContent = '✓ 10% SYNA WORLD PARTNERSHIP DISCOUNT APPLIED';
        promoDiscountMsg.style.color = '#00f0ff';
      } else {
        promoDiscountMsg.textContent = '✕ INVALID VOUCHER CODE. TRY "CCEE" OR "SOLARILUXURY"';
        promoDiscountMsg.style.color = '#ff1a2a';
      }
      updateCartUI();
    });
  }

  /**
   * Central Cee Backstage Quote Modal
   */
  function setupQuoteModal() {
    if (ccQuoteBtn && quoteModalBackdrop && quoteCloseBtn) {
      ccQuoteBtn.addEventListener('click', () => {
        quoteModalBackdrop.classList.add('open');
        document.body.style.overflow = 'hidden';
        playUiClickSound();
      });

      quoteCloseBtn.addEventListener('click', () => {
        quoteModalBackdrop.classList.remove('open');
        document.body.style.overflow = '';
        playUiClickSound();
      });

      quoteModalBackdrop.addEventListener('click', (e) => {
        if (e.target === quoteModalBackdrop) {
          quoteModalBackdrop.classList.remove('open');
          document.body.style.overflow = '';
        }
      });
    }
  }

  /**
   * Category Filter System for Streetwear Catalog
   */
  function setupCategoryFilters() {
    const filterTabs = document.querySelectorAll('.filter-tab');
    const cards = document.querySelectorAll('.streetwear-card');

    if (!filterTabs.length || !cards.length) return;

    filterTabs.forEach(tab => {
      tab.addEventListener('click', function () {
        playUiClickSound();
        filterTabs.forEach(t => t.classList.remove('active'));
        this.classList.add('active');

        const cat = this.getAttribute('data-category').toUpperCase();

        cards.forEach(card => {
          const cardCat = (card.getAttribute('data-category') || '').toUpperCase();
          if (cat === 'TODOS' || cat === 'ALL' || cardCat.includes(cat) || cat.includes(cardCat)) {
            card.style.display = 'flex';
            card.style.opacity = '1';
          } else {
            card.style.display = 'none';
          }
        });
      });
    });
  }

  /**
   * Web Audio API: London Drill Ambient Sound Generator
   */
  function initAudioEngine() {
    if (audioCtx) return;
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      audioCtx = new AudioContext();
    } catch (e) {
      console.warn("Web Audio API not supported:", e);
    }
  }

  function startDrillAtmosphere() {
    if (!audioCtx) initAudioEngine();
    if (!audioCtx) return;

    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }

    drillGain = audioCtx.createGain();
    drillGain.gain.setValueAtTime(0.08, audioCtx.currentTime);
    drillGain.connect(audioCtx.destination);

    // Deep 808 Sub-Bass Pad (55Hz root note)
    drillOsc1 = audioCtx.createOscillator();
    drillOsc1.type = 'sine';
    drillOsc1.frequency.setValueAtTime(55, audioCtx.currentTime);

    // Ambient cold overtone
    drillOsc2 = audioCtx.createOscillator();
    drillOsc2.type = 'triangle';
    drillOsc2.frequency.setValueAtTime(110, audioCtx.currentTime);
    const filter = audioCtx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(180, audioCtx.currentTime);

    drillOsc1.connect(drillGain);
    drillOsc2.connect(filter);
    filter.connect(drillGain);

    drillOsc1.start();
    drillOsc2.start();

    isAudioPlaying = true;
    if (audioToggleBtn) {
      audioToggleBtn.classList.add('playing');
      const label = audioToggleBtn.querySelector('.audio-label');
      if (label) label.textContent = 'DRILL VIBE: ON';
    }
  }

  function stopDrillAtmosphere() {
    if (drillGain && audioCtx) {
      drillGain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.5);
      setTimeout(() => {
        if (drillOsc1) { drillOsc1.stop(); drillOsc1.disconnect(); }
        if (drillOsc2) { drillOsc2.stop(); drillOsc2.disconnect(); }
        isAudioPlaying = false;
        if (audioToggleBtn) {
          audioToggleBtn.classList.remove('playing');
          const label = audioToggleBtn.querySelector('.audio-label');
          if (label) label.textContent = 'DRILL VIBE: OFF';
        }
      }, 500);
    }
  }

  function toggleAudio() {
    if (isAudioPlaying) {
      stopDrillAtmosphere();
    } else {
      startDrillAtmosphere();
    }
  }

  function playUiClickSound() {
    if (!audioCtx) return;
    try {
      const clickOsc = audioCtx.createOscillator();
      const clickGain = audioCtx.createGain();
      clickOsc.type = 'sine';
      clickOsc.frequency.setValueAtTime(1200, audioCtx.currentTime);
      clickOsc.frequency.exponentialRampToValueAtTime(300, audioCtx.currentTime + 0.05);

      clickGain.gain.setValueAtTime(0.04, audioCtx.currentTime);
      clickGain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.05);

      clickOsc.connect(clickGain);
      clickGain.connect(audioCtx.destination);

      clickOsc.start();
      clickOsc.stop(audioCtx.currentTime + 0.05);
    } catch (e) {}
  }

  /**
   * Hero Add to Bag & Interactive Controls
   */
  function setupHeroCommerce() {
    const heroAddBtn = document.getElementById('addToBagBtn');
    const sizeButtons = document.querySelectorAll('.size-btn');
    let selectedSize = 'L';

    sizeButtons.forEach(btn => {
      btn.addEventListener('click', function () {
        playUiClickSound();
        sizeButtons.forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        selectedSize = this.getAttribute('data-size') || this.textContent.trim();
      });
    });

    if (heroAddBtn) {
      heroAddBtn.addEventListener('click', () => {
        addItemToCart({
          id: 1,
          title: "DECODED 2.0 PUFFER 'HYPERDRIVE'",
          price: 395.00,
          size: selectedSize,
          color: "PITCH BLACK / 3M",
          img: "static/img/trapstar_puffer_hero.jpg"
        });
      });
    }

    // Streetwear Cards "Add to Bag" Buttons
    const cardAddButtons = document.querySelectorAll('.btn-card-add');
    cardAddButtons.forEach(btn => {
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        const id = parseInt(this.getAttribute('data-id')) || 1;
        const title = this.getAttribute('data-title') || 'SOLARILUXURY GARMENT';
        const price = parseFloat(this.getAttribute('data-price')) || 120.00;
        const img = this.getAttribute('data-img') || 'static/img/trapstar_puffer_hero.jpg';

        addItemToCart({
          id: id,
          title: title,
          price: price,
          size: "L",
          color: "BLACK",
          img: img
        });
      });
    });
  }

  /**
   * Master Boot Routine
   */
  function init() {
    preloadCentralCeeFrames();
    setupStageHud();
    setupHotspots();
    updateCartUI();
    setupPromoCodes();
    setupQuoteModal();
    setupCategoryFilters();
    setupHeroCommerce();

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


    // Event Listeners
    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('resize', handleScroll);

    if (bagBtn) bagBtn.addEventListener('click', openCart);
    if (cartCloseBtn) cartCloseBtn.addEventListener('click', closeCart);
    if (cartBackdrop) cartBackdrop.addEventListener('click', closeCart);

    if (audioToggleBtn) {
      if(audioToggleBtn) audioToggleBtn.addEventListener('click', () => {
        initAudioEngine();
        toggleAudio();
      });
    }

    if (checkoutBtn) {
      checkoutBtn.addEventListener('click', () => {
        playUiClickSound();
        alert('Solariluxury x Central Cee Checkout Gateway:\nOrder confirmed for instant dispatch / Express worldwide.');
      });
    }

    // Initial Trigger
    
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

    handleScroll();
  }

  // Fire on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
