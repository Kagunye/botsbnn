// Live totals for the Quotation / Invoice admin form (mirrors quotations/models.py)
(function () {
  function num(v) { const n = parseFloat(String(v || '').replace(/,/g, '')); return isNaN(n) ? 0 : n; }
  function fmt(n) { return n.toLocaleString('en-KE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function el(id) { return document.getElementById(id); }
  function round2(n) { return Math.round((n + Number.EPSILON) * 100) / 100; }

  function recalc() {
    const rows = [];
    document.querySelectorAll('tr.form-row').forEach(row => {
      const q = row.querySelector('input[name$="-quantity"]');
      const p = row.querySelector('input[name$="-unit_price"]');
      if (!q || !p) return;
      const del = row.querySelector('input[name$="-DELETE"]');
      const d = row.querySelector('input[name$="-discount"]');
      const t = row.querySelector('input[name$="-taxable"]');
      const gross = (del && del.checked) ? 0 : round2(num(q.value) * num(p.value));
      const disc = Math.min(num(d && d.value), gross);
      rows.push({ row, gross, disc, net: gross - disc, taxable: t ? t.checked : true });
    });

    const subtotal = rows.reduce((s, r) => s + r.gross, 0);
    const lineDisc = rows.reduce((s, r) => s + r.disc, 0);
    const base = subtotal - lineDisc;
    const dType = el('id_discount_type') ? el('id_discount_type').value : 'percent';
    const dVal = num(el('id_discount_value') && el('id_discount_value').value);
    let extra = base > 0 ? (dType === 'percent' ? base * dVal / 100 : dVal) : 0;
    extra = Math.min(Math.max(extra, 0), Math.max(base, 0));
    const factor = base > 0 ? (base - extra) / base : 1;
    const applyTax = el('id_apply_tax') && el('id_apply_tax').checked;
    const rate = num(el('id_tax_rate') && el('id_tax_rate').value);
    const delivery = num(el('id_delivery_fee') && el('id_delivery_fee').value);

    let tax = 0;
    rows.forEach(r => {
      const vat = (applyTax && r.taxable) ? round2(r.net * factor * rate / 100) : 0;
      tax += vat;
      const vCell = r.row.querySelector('td.field-vat_display');
      const tCell = r.row.querySelector('td.field-line_total_display');
      if (vCell) (vCell.querySelector('p') || vCell).textContent = fmt(vat);
      if (tCell) (tCell.querySelector('p') || tCell).textContent = fmt(r.net);
    });

    const discount = lineDisc + extra;
    const set = (id, v) => { if (el(id)) el(id).textContent = fmt(v); };
    set('q-subtotal', subtotal); set('q-discount', discount); set('q-delivery', delivery);
    set('q-tax', tax); set('q-total', subtotal - discount + delivery + tax);
    if (el('q-rate')) el('q-rate').textContent = applyTax ? '(' + rate + '%)' : '(not charged)';
  }

  // Line numbers: 1, 2, 3 ... on every visible item row (also after adding/removing rows)
  // Only rows with something in them get a number; blank spare rows keep their default so Django ignores them.
  function hasContent(row) {
    return ['-item_code', '-description', '-product'].some(s => {
      const f = row.querySelector(`[name$="${s}"]`); return f && String(f.value || '').trim() !== '';
    });
  }
  function renumber() {
    let i = 0;
    document.querySelectorAll('tr.form-row').forEach(row => {
      const o = row.querySelector('input[name$="-order"]');
      if (!o || row.classList.contains('empty-form') || /__prefix__/.test(o.name)) return;
      const del = row.querySelector('input[name$="-DELETE"]');
      if ((del && del.checked) || !hasContent(row)) { o.value = o.defaultValue; return; }
      o.value = ++i;
    });
  }

  // New document: show the number it will get for the chosen type
  function showNumber() {
    const n = el('q-number'), t = el('id_doc_type');
    if (n && t && n.dataset['next' + t.value.charAt(0).toUpperCase() + t.value.slice(1)]) {
      n.textContent = n.dataset['next' + t.value.charAt(0).toUpperCase() + t.value.slice(1)];
    }
  }

  // Picking an inventory product fills in item code, description and price straight away (only empty boxes)
  function fillFromProduct(select) {
    const row = select.closest('tr'); const id = select.value;
    if (!row || !id) return;
    const base = location.pathname.split('/quotation/')[0] + '/quotation/';
    fetch(base + 'product-info/' + id + '/', { credentials: 'same-origin' })
      .then(r => r.ok ? r.json() : null)
      .then(p => {
        if (!p) return;
        const set = (sel, v) => { const f = row.querySelector(sel); if (f && v && !f.value.trim()) f.value = v; };
        set('input[name$="-description"]', p.name);
        set('input[name$="-item_code"]', p.sku);
        const price = row.querySelector('input[name$="-unit_price"]');
        if (price && p.price && (!price.value || num(price.value) === 0)) price.value = p.price;
        renumber(); recalc();
      })
      .catch(() => {});
  }

  document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('#quotation_form');
    if (!form) return;
    form.addEventListener('input', e => {
      recalc();
      if (e.target.matches('input[name$="-item_code"], input[name$="-description"]')) renumber();
    });
    form.addEventListener('change', e => {
      recalc();
      if (e.target.matches('select[name$="-product"]')) fillFromProduct(e.target);
      if (e.target.matches('input[name$="-DELETE"]')) renumber();
      if (e.target.id === 'id_doc_type') showNumber();
    });
    // the inventory picker is a select2 autocomplete: it signals through jQuery
    if (window.django && django.jQuery) {
      django.jQuery(document).on('select2:select', 'select[name$="-product"]', function () { fillFromProduct(this); });
    }
    document.addEventListener('formset:added', () => { renumber(); recalc(); });
    document.addEventListener('formset:removed', () => { renumber(); recalc(); });
    renumber(); showNumber(); recalc();
  });
})();

// Preview the printable document in a pop-up, with Print and Download PDF buttons
(function () {
  function openPreview(url, title, printUrl) {
    const wrap = document.createElement('div');
    wrap.className = 'q-modal';
    wrap.innerHTML = `
      <div class="q-modal-box" role="dialog" aria-modal="true" aria-label="Preview">
        <div class="q-modal-bar">
          <strong></strong>
          <span class="q-modal-actions">
            <button type="button" class="q-m-print">🖨 Print</button>
            <button type="button" class="q-m-pdf">⬇ Download PDF</button>
            <a class="q-m-open" target="_blank">Open in new tab ↗</a>
            <button type="button" class="q-m-close" aria-label="Close">✕</button>
          </span>
        </div>
        <iframe title="Document preview"></iframe>
      </div>`;
    wrap.querySelector('strong').textContent = title;
    wrap.querySelector('.q-m-open').href = printUrl;
    const frame = wrap.querySelector('iframe');
    frame.src = url;
    const close = () => { wrap.remove(); document.removeEventListener('keydown', onKey); };
    const onKey = e => { if (e.key === 'Escape') close(); };
    wrap.addEventListener('click', e => { if (e.target === wrap) close(); });
    wrap.querySelector('.q-m-close').addEventListener('click', close);
    wrap.querySelector('.q-m-print').addEventListener('click', () => frame.contentWindow.print());
    wrap.querySelector('.q-m-pdf').addEventListener('click', () => {
      const w = frame.contentWindow;
      if (w && w.bnnDownloadPdf) w.bnnDownloadPdf(); else window.open(printUrl + '?pdf=1', '_blank');
    });
    document.addEventListener('keydown', onKey);
    document.body.appendChild(wrap);
  }
  document.addEventListener('click', e => {
    const a = e.target.closest('a.q-tool-preview');
    if (!a) return;
    e.preventDefault();
    openPreview(a.dataset.preview, a.dataset.title, a.getAttribute('href'));
  });
})();
