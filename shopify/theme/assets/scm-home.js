/* SCM Startseite – Interaktionen. Wird von mehreren Sections eingebunden,
   startet aber nur einmal und initialisiert Sections, die im Theme-Editor
   nachgeladen werden, erneut. */
(() => {
  if (window.ScmHome) return;

  const root = document.documentElement;
  root.classList.add('scm-js');

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const canHover = window.matchMedia('(hover: hover) and (pointer: fine)');

  /* ---------- Scroll-Reveal ---------- */
  // Zeilen-Reveals liegen in einem Container mit overflow: hidden und sind
  // anfangs komplett herausgeschoben – beobachtet wird deshalb die Zeile selbst.
  const revealTargets = new WeakMap();
  const revealObserver = 'IntersectionObserver' in window
    ? new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          (revealTargets.get(entry.target) || [entry.target]).forEach((el) => el.classList.add('is-in'));
          revealObserver.unobserve(entry.target);
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 })
    : null;

  const initReveal = (scope) => {
    scope.querySelectorAll('[data-scm-reveal]:not(.is-in)').forEach((el) => {
      if (!revealObserver || reducedMotion.matches) {
        el.classList.add('is-in');
        return;
      }
      const watched = el.closest('.scm-line') || el;
      revealTargets.set(watched, [...(revealTargets.get(watched) || []), el]);
      revealObserver.observe(watched);
    });
  };

  /* ---------- Hero ---------- */
  const initHero = (scope) => {
    scope.querySelectorAll('[data-scm-hero]').forEach((hero) => {
      if (hero.dataset.scmReady) return;
      hero.dataset.scmReady = 'true';
      requestAnimationFrame(() => requestAnimationFrame(() => hero.classList.add('is-ready')));

      const video = hero.querySelector('[data-scm-hero-video]');
      const toggle = hero.querySelector('[data-scm-hero-toggle]');
      if (!video) return;

      const setPaused = (paused) => {
        if (paused) video.pause();
        else video.play().catch(() => setPaused(true));
        if (!toggle) return;
        toggle.setAttribute('aria-pressed', String(paused));
        toggle.setAttribute('aria-label', paused ? toggle.dataset.labelPlay : toggle.dataset.labelPause);
      };

      if (reducedMotion.matches) setPaused(true);
      if (toggle) toggle.addEventListener('click', () => setPaused(!video.paused));

      // Video außerhalb des Sichtfelds anhalten (Akku, Datenvolumen)
      if ('IntersectionObserver' in window) {
        new IntersectionObserver(([entry]) => {
          if (toggle && toggle.getAttribute('aria-pressed') === 'true') return;
          if (entry.isIntersecting) video.play().catch(() => {});
          else video.pause();
        }, { threshold: 0.05 }).observe(hero);
      }
    });
  };

  /* ---------- Reiter (Neu / Second Hand) ---------- */
  const initTabs = (scope) => {
    scope.querySelectorAll('[data-scm-tabs]').forEach((group) => {
      if (group.dataset.scmReady) return;
      group.dataset.scmReady = 'true';
      const tabs = [...group.querySelectorAll('[data-scm-tab]')];

      const select = (tab, focus) => {
        tabs.forEach((other) => {
          const active = other === tab;
          other.setAttribute('aria-selected', String(active));
          other.tabIndex = active ? 0 : -1;
          const panel = document.getElementById(other.getAttribute('aria-controls'));
          if (!panel) return;
          panel.hidden = !active;
          if (active) {
            panel.classList.remove('is-entering');
            void panel.offsetWidth;
            panel.classList.add('is-entering');
            panel.querySelectorAll('[data-scm-reveal]').forEach((el) => el.classList.add('is-in'));
            panel.dispatchEvent(new CustomEvent('scm:shown'));
          }
        });
        if (focus) tab.focus();
      };

      tabs.forEach((tab, index) => {
        tab.addEventListener('click', () => select(tab));
        tab.addEventListener('keydown', (event) => {
          const keys = { ArrowRight: 1, ArrowLeft: -1, Home: -index, End: tabs.length - 1 - index };
          if (!(event.key in keys)) return;
          event.preventDefault();
          select(tabs[(index + keys[event.key] + tabs.length) % tabs.length], true);
        });
      });
    });
  };

  /* ---------- Produkt-Rail: Pfeile, Fortschritt, Ziehen mit der Maus ---------- */
  const initRails = (scope) => {
    scope.querySelectorAll('[data-scm-rail]').forEach((rail) => {
      if (rail.dataset.scmReady) return;
      rail.dataset.scmReady = 'true';
      const track = rail.querySelector('[data-scm-rail-track]');
      const prev = rail.querySelector('[data-scm-rail-prev]');
      const next = rail.querySelector('[data-scm-rail-next]');
      const bar = rail.querySelector('[data-scm-rail-progress]');
      if (!track) return;

      const update = () => {
        const max = track.scrollWidth - track.clientWidth;
        const visible = track.scrollWidth ? track.clientWidth / track.scrollWidth : 1;
        const progress = max > 0 ? track.scrollLeft / max : 1;
        if (bar) bar.style.setProperty('--p', Math.min(1, visible + (1 - visible) * progress).toFixed(3));
        if (prev) prev.disabled = track.scrollLeft <= 2;
        if (next) next.disabled = track.scrollLeft >= max - 2;
      };

      const step = (direction) => {
        const card = track.querySelector('.scm-card');
        const gap = parseFloat(getComputedStyle(track).columnGap) || 0;
        const width = card ? card.getBoundingClientRect().width + gap : track.clientWidth * 0.8;
        const perPage = Math.max(1, Math.floor(track.clientWidth / width));
        track.scrollBy({ left: direction * width * perPage, behavior: reducedMotion.matches ? 'auto' : 'smooth' });
      };

      if (prev) prev.addEventListener('click', () => step(-1));
      if (next) next.addEventListener('click', () => step(1));
      track.addEventListener('scroll', update, { passive: true });
      window.addEventListener('resize', update);
      rail.addEventListener('scm:shown', () => { track.scrollLeft = 0; update(); });
      update();

      // Ziehen mit der Maus (Touch scrollt nativ)
      let startX = 0;
      let startScroll = 0;
      let dragging = false;
      let moved = false;
      track.addEventListener('pointerdown', (event) => {
        if (event.pointerType !== 'mouse' || event.button !== 0) return;
        dragging = true;
        moved = false;
        startX = event.clientX;
        startScroll = track.scrollLeft;
      });
      window.addEventListener('pointermove', (event) => {
        if (!dragging) return;
        const delta = event.clientX - startX;
        if (!moved && Math.abs(delta) > 6) {
          moved = true;
          track.classList.add('is-dragging');
        }
        if (moved) track.scrollLeft = startScroll - delta;
      });
      window.addEventListener('pointerup', () => {
        if (!dragging) return;
        dragging = false;
        if (!moved) return;
        // Klick nach dem Ziehen unterdrücken, dann am nächsten Artikel einrasten
        track.addEventListener('click', (event) => { event.preventDefault(); event.stopPropagation(); }, { capture: true, once: true });
        setTimeout(() => track.classList.remove('is-dragging'), 0);
      });
    });
  };

  /* ---------- Looks: Reel beim Darüberfahren bzw. mobil im Blickfeld ---------- */
  const initLooks = (scope) => {
    scope.querySelectorAll('[data-scm-look]').forEach((look) => {
      if (look.dataset.scmReady) return;
      look.dataset.scmReady = 'true';
      const video = look.querySelector('[data-scm-look-video]');
      if (!video || reducedMotion.matches) return;

      const play = () => {
        if (!video.src) video.src = video.dataset.src;
        const attempt = video.play();
        if (attempt) attempt.then(() => look.classList.add('is-playing')).catch(() => {});
        else look.classList.add('is-playing');
      };
      const stop = () => {
        look.classList.remove('is-playing');
        video.pause();
      };

      if (canHover.matches) {
        look.addEventListener('pointerenter', play);
        look.addEventListener('pointerleave', stop);
        look.addEventListener('focusin', play);
        look.addEventListener('focusout', stop);
      } else if ('IntersectionObserver' in window) {
        new IntersectionObserver(([entry]) => {
          if (entry.intersectionRatio >= 0.6) play();
          else stop();
        }, { threshold: [0, 0.6] }).observe(look);
      }
    });
  };

  const init = (scope = document) => {
    initHero(scope);
    initTabs(scope);
    initRails(scope);
    initLooks(scope);
    initReveal(scope);
  };

  window.ScmHome = { init };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => init());
  else init();

  document.addEventListener('shopify:section:load', (event) => init(event.target));
})();
