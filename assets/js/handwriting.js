/**
 * KnowYourSponsor — Vanilla Handwriting SVG Contour Animator
 * Converts raw TTF glyphs into dynamic SVG contour paths with staggered pen-stroke
 * transitions and fluid inking, cycling through statutory assurance keywords.
 */
(function(global) {
  'use strict';

  const OPENTYPE_CDN = 'https://cdn.jsdelivr.net/npm/opentype.js@1.3.4/dist/opentype.min.js';
  const DEFAULT_FONT_URL = 'assets/fonts/handwriting.ttf';
  const FALLBACK_FONT_URL = 'https://cdn.21st.dev/assets/mirror/13/1347863151acdc00fa281daaba1a3543dbce5870b55f9cf7479a15bb84007681.ttf';

  let libPromise = null;

  function loadOpentype() {
    if (typeof window === 'undefined') return Promise.reject(new Error('no window'));
    if (window.opentype) return Promise.resolve(window.opentype);
    if (!libPromise) {
      libPromise = new Promise((resolve, reject) => {
        const localScript = document.createElement('script');
        localScript.src = 'assets/js/opentype.min.js';
        localScript.async = true;
        localScript.onload = () => {
          if (window.opentype) resolve(window.opentype);
          else reject(new Error('opentype failed to initialize'));
        };
        localScript.onerror = () => {
          // Fallback to CDN if local asset fails
          const cdnScript = document.createElement('script');
          cdnScript.src = OPENTYPE_CDN;
          cdnScript.async = true;
          cdnScript.onload = () => {
            if (window.opentype) resolve(window.opentype);
            else reject(new Error('CDN opentype failed'));
          };
          cdnScript.onerror = () => reject(new Error('opentype library could not be loaded'));
          document.head.appendChild(cdnScript);
        };
        document.head.appendChild(localScript);
      });
    }
    return libPromise;
  }

  const fontCache = new Map();

  function loadFont(url) {
    let pending = fontCache.get(url);
    if (!pending) {
      pending = Promise.all([
        loadOpentype(),
        fetch(url)
          .then(res => {
            if (!res.ok) throw new Error('Font request failed: ' + res.status);
            return res.arrayBuffer();
          })
          .catch(() => {
            return fetch(FALLBACK_FONT_URL).then(r => r.arrayBuffer());
          })
      ]).then(([lib, buffer]) => lib.parse(buffer));
      fontCache.set(url, pending);
    }
    return pending;
  }

  const EM = 100;

  function initHandwritingText(container, options) {
    if (!container) return;
    const opts = options || {};
    const words = (opts.words && opts.words.length) ? opts.words : ['Verified.', 'Solvent.', 'Monitored.', 'Audit-Ready.'];
    const interval = opts.interval || 3500;
    const fontUrl = opts.fontUrl || DEFAULT_FONT_URL;
    const duration = opts.duration || 1.35;
    const delay = opts.delay || 0.05;
    const strokeWidth = opts.strokeWidth || 1.8;
    const fill = opts.fill !== undefined ? opts.fill : true;
    const height = opts.height || '1.2em';

    let currentIndex = 0;
    let timerId = null;
    let font = null;
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Set initial fallback text immediately
    container.textContent = words[0];

    loadFont(fontUrl).then(parsedFont => {
      font = parsedFont;
      renderCurrent();

      if (words.length > 1 && !prefersReducedMotion) {
        timerId = setInterval(() => {
          currentIndex = (currentIndex + 1) % words.length;
          renderCurrent();
        }, interval);
      }
    }).catch(() => {
      // Degrade gracefully to standard text cycling
      if (words.length > 1 && !prefersReducedMotion) {
        timerId = setInterval(() => {
          currentIndex = (currentIndex + 1) % words.length;
          container.textContent = words[currentIndex];
        }, interval);
      }
    });

    function renderCurrent() {
      if (!font) {
        container.textContent = words[currentIndex];
        return;
      }

      const currentWord = words[currentIndex];
      const path = font.getPath(currentWord, 0, EM, EM);
      const box = path.getBoundingBox();
      const pad = EM * 0.12;
      const full = path.toPathData(2);
      const contours = full.split(/(?=M)/).filter(d => d.trim().length > 1);

      const x = box.x1 - pad;
      const y = box.y1 - pad;
      const w = box.x2 - box.x1 + pad * 2;
      const h = box.y2 - box.y1 + pad * 2;

      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('viewBox', `${x} ${y} ${w} ${h}`);
      svg.setAttribute('role', 'img');
      svg.setAttribute('aria-label', currentWord);
      svg.style.height = height;
      svg.style.width = `calc(${height} * ${(w / h).toFixed(4)})`;
      svg.style.overflow = 'visible';
      svg.style.display = 'inline-block';
      svg.style.verticalAlign = 'middle';

      let fillPath = null;
      if (fill) {
        fillPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        fillPath.setAttribute('d', full);
        fillPath.setAttribute('fill', 'currentColor');
        fillPath.setAttribute('stroke', 'none');
        fillPath.style.opacity = '0';
        fillPath.style.transition = 'none';
        svg.appendChild(fillPath);
      }

      const pathEls = [];
      const count = Math.max(1, contours.length);

      contours.forEach((d) => {
        const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        p.setAttribute('d', d);
        p.setAttribute('fill', 'none');
        p.setAttribute('stroke', 'currentColor');
        p.setAttribute('stroke-width', strokeWidth);
        p.setAttribute('stroke-linecap', 'round');
        p.setAttribute('stroke-linejoin', 'round');
        p.style.transition = 'none';
        svg.appendChild(p);
        pathEls.push(p);
      });

      container.innerHTML = '';
      container.appendChild(svg);

      const lengths = pathEls.map(el => {
        try {
          return el.getTotalLength() || 1;
        } catch (e) {
          return 1;
        }
      });

      lengths.forEach((len, i) => {
        pathEls[i].style.strokeDasharray = `${len}`;
        pathEls[i].style.strokeDashoffset = `${len}`;
      });

      // Staggered pen stroke animation commit
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          if (fillPath) {
            fillPath.style.transition = `opacity 0.45s ease-out ${(delay + duration * 0.72).toFixed(3)}s`;
            fillPath.style.opacity = '1';
          }

          pathEls.forEach((el, i) => {
            const len = lengths[i];
            const each = (duration / count) * 2.4;
            const start = delay + (i / count) * duration;
            el.style.transition = `stroke-dashoffset ${each.toFixed(3)}s ease-out ${start.toFixed(3)}s`;
            el.style.strokeDashoffset = '0';
          });
        });
      });
    }

    return {
      destroy: function() {
        if (timerId) clearInterval(timerId);
      }
    };
  }

  global.initHandwritingText = initHandwritingText;

  if (typeof document !== 'undefined') {
    const autoInit = () => {
      const el = document.getElementById('brandHandwriting');
      if (el && !el.dataset.hwInit) {
        el.dataset.hwInit = 'true';
        initHandwritingText(el, {
          words: ['Verified.', 'Solvent.', 'Monitored.', 'Audit-Ready.'],
          interval: 3500,
          duration: 1.35,
          height: '1.25em'
        });
      }
    };
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', autoInit);
    } else {
      autoInit();
    }
  }
})(typeof window !== 'undefined' ? window : this);
