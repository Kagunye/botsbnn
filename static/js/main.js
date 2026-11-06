document.addEventListener('DOMContentLoaded', () => {
  // Quantity +/- buttons
  document.querySelectorAll('[data-qty]').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = btn.parentElement.querySelector('input[name="quantity"]');
      const min = parseInt(input.min || '1', 10);
      const max = input.max ? parseInt(input.max, 10) : Infinity;
      const next = Math.min(max, Math.max(min, (parseInt(input.value, 10) || 1) + parseInt(btn.dataset.qty, 10)));
      if (next === parseInt(input.value, 10)) return;
      input.value = next;
      if (btn.hasAttribute('data-autosubmit')) btn.closest('form').submit();
    });
  });

  // Copy-to-clipboard buttons (payment details)
  document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(btn.dataset.copy);
        btn.innerHTML = '<i class="bi bi-check2"></i>';
        setTimeout(() => (btn.innerHTML = '<i class="bi bi-copy"></i>'), 1500);
      } catch (e) { /* clipboard unavailable */ }
    });
  });

  // Product gallery thumbnails
  const mainImage = document.getElementById('mainImage');
  document.querySelectorAll('.gallery-thumbs button').forEach(btn => {
    btn.addEventListener('click', () => {
      mainImage.src = btn.dataset.src;
      document.querySelectorAll('.gallery-thumbs button').forEach(b => b.classList.toggle('active', b === btn));
    });
  });

  // AJAX add-to-cart (falls back to normal POST without JS)
  const toastEl = document.getElementById('cartToast');
  const toast = toastEl ? bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 3000 }) : null;

  document.querySelectorAll('.add-to-cart-form').forEach(form => {
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const button = form.querySelector('button[type="submit"]');
      button.disabled = true;
      try {
        const res = await fetch(form.action, {
          method: 'POST',
          body: new FormData(form),
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!res.ok) throw new Error(res.statusText);
        const data = await res.json();
        document.querySelectorAll('[data-cart-count]').forEach(el => (el.textContent = data.count));
        if (toast) {
          toastEl.querySelector('.toast-body span').textContent = data.message;
          toast.show();
        }
      } catch (err) {
        form.submit();
      } finally {
        button.disabled = false;
      }
    });
  });

  // News-style slider ("What we do")
  document.querySelectorAll('[data-news-track]').forEach(track => {
    const section = track.closest('section');
    const prev = section.querySelector('[data-news-prev]');
    const next = section.querySelector('[data-news-next]');
    const dotsWrap = section.querySelector('[data-news-dots]');
    const cards = [...track.children];
    const gap = () => parseFloat(getComputedStyle(track).columnGap) || 0;
    const step = () => (cards[0] ? cards[0].getBoundingClientRect().width + gap() : track.clientWidth);
    const perView = () => Math.max(1, Math.round((track.clientWidth + gap()) / step()));
    const pages = () => Math.max(1, cards.length - perView() + 1);
    let dots = [];
    function update() {
      const i = Math.round(track.scrollLeft / step());
      dots.forEach((d, k) => d.classList.toggle('active', k === i));
      prev.disabled = track.scrollLeft <= 2;
      next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 2;
    }
    function buildDots() {
      dotsWrap.innerHTML = '';
      dots = [...Array(pages())].map((_, i) => {
        const b = document.createElement('button');
        b.type = 'button';
        b.addEventListener('click', () => track.scrollTo({ left: i * step() }));
        dotsWrap.appendChild(b);
        return b;
      });
      update();
    }
    prev.addEventListener('click', () => track.scrollBy({ left: -step() }));
    next.addEventListener('click', () => track.scrollBy({ left: step() }));
    track.addEventListener('scroll', () => requestAnimationFrame(update), { passive: true });
    track.addEventListener('keydown', e => {
      if (e.key === 'ArrowRight') { e.preventDefault(); next.click(); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); prev.click(); }
    });
    window.addEventListener('resize', buildDots);
    buildDots();
    // auto-advance every 5s; pauses while hovered, resumes 6s after a touch.
    // Visitors with "reduce motion" still get auto-advance, but without the smooth glide.
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) track.style.scrollBehavior = 'auto';
    let paused = false, touchTimer = null;
    section.addEventListener('mouseenter', () => { paused = true; });
    section.addEventListener('mouseleave', () => { paused = false; });
    section.addEventListener('touchstart', () => { paused = true; clearTimeout(touchTimer); }, { passive: true });
    section.addEventListener('touchend', () => { clearTimeout(touchTimer); touchTimer = setTimeout(() => { paused = false; }, 6000); }, { passive: true });
    setInterval(() => {
      if (paused || document.hidden) return;
      if (track.scrollLeft + track.clientWidth >= track.scrollWidth - 2) track.scrollTo({ left: 0 });
      else track.scrollBy({ left: step() });
    }, 5000);
  });

  // Header: slimmer with a soft shadow once the page is scrolled
  const header = document.querySelector('.site-header');
  if (header) {
    const onScroll = () => header.classList.toggle('is-scrolled', window.scrollY > 10);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // CTA strip background videos: download only when scrolled near, play while visible
  const ctaVideos = document.querySelectorAll('.cta-video');
  const conn = navigator.connection || {};
  const skipVideo = window.matchMedia('(prefers-reduced-motion: reduce)').matches || conn.saveData || /(^|-)2g$/.test(conn.effectiveType || '');
  if (ctaVideos.length && !skipVideo && 'IntersectionObserver' in window) {
    const vio = new IntersectionObserver(entries => {
      entries.forEach(e => {
        const v = e.target;
        if (e.isIntersecting) {
          if (!v.dataset.loaded) {
            [['webm', 'video/webm'], ['mp4', 'video/mp4']].forEach(([k, type]) => {
              if (!v.dataset[k]) return;
              const s = document.createElement('source'); s.src = v.dataset[k]; s.type = type; v.appendChild(s);
            });
            v.dataset.loaded = '1'; v.load();
          }
          v.play().catch(() => {});
        } else if (v.dataset.loaded) {
          v.pause();
        }
      });
    }, { rootMargin: '200px 0px' });
    ctaVideos.forEach(v => vio.observe(v));
  }

  // Advert promo grids: rise in one after another when scrolled into view
  const adCards = document.querySelectorAll('.ad-grid .offer-card');
  if (adCards.length && 'IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    adCards.forEach(c => c.classList.add('ad-pre'));
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (!e.isIntersecting) return;
        const i = [...e.target.parentElement.children].indexOf(e.target);
        e.target.style.animationDelay = (i * 0.12) + 's';
        e.target.classList.remove('ad-pre'); e.target.classList.add('ad-in');
        io.unobserve(e.target);
      });
    }, { threshold: 0.15 });
    adCards.forEach(c => io.observe(c));
    // safety net: never leave a poster hidden
    setTimeout(() => adCards.forEach(c => { if (c.classList.contains('ad-pre')) { c.classList.remove('ad-pre'); c.classList.add('ad-in'); } }), 4000);
  }
});
