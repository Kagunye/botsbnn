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

  document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('#quotation_form');
    if (!form) return;
    form.addEventListener('input', recalc);
    form.addEventListener('change', recalc);
    document.addEventListener('formset:added', recalc);
    document.addEventListener('formset:removed', recalc);
    recalc();
  });
})();
