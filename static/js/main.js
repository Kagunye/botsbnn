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
    // gentle auto-advance; pauses on hover/focus/touch and for reduced-motion users
    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      let paused = false;
      ['mouseenter', 'focusin', 'touchstart'].forEach(ev => section.addEventListener(ev, () => { paused = true; }, { passive: true }));
      ['mouseleave', 'focusout'].forEach(ev => section.addEventListener(ev, () => { paused = false; }));
      setInterval(() => {
        if (paused || document.hidden) return;
        if (track.scrollLeft + track.clientWidth >= track.scrollWidth - 2) track.scrollTo({ left: 0 });
        else track.scrollBy({ left: step() });
      }, 5000);
    }
  });
});
