from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import models
from django.urls import reverse
from django.utils import timezone

TWO = Decimal('0.01')


def money(value):
    return Decimal(value or 0).quantize(TWO, rounding=ROUND_HALF_UP)


def default_tax_rate():
    from pages.models import SiteSettings
    return SiteSettings.load().default_tax_rate


def default_valid_until():
    from pages.models import SiteSettings
    return timezone.localdate() + timedelta(days=SiteSettings.load().quotation_validity_days)


def default_terms():
    from pages.models import SiteSettings
    return SiteSettings.load().quotation_terms


class Quotation(models.Model):
    """A quotation, proforma invoice or invoice (same layout, different title and numbering)."""
    DOC_TYPES = [('quotation', 'Quotation'), ('proforma', 'Proforma Invoice'), ('invoice', 'Invoice')]
    PREFIX = {'quotation': 'QU', 'proforma': 'PI', 'invoice': 'INV'}
    STATUS = [
        ('draft', 'Draft'), ('sent', 'Sent to client'), ('accepted', 'Accepted'),
        ('rejected', 'Rejected'), ('expired', 'Expired'), ('paid', 'Paid'),
    ]
    DISCOUNT_TYPES = [('percent', 'Percentage (%)'), ('amount', 'Fixed amount (KSh)')]

    doc_type = models.CharField('Document type', max_length=10, choices=DOC_TYPES, default='quotation')
    number = models.CharField(max_length=30, unique=True, blank=True, editable=False)
    title = models.CharField('Reference / project', max_length=200, blank=True,
                             help_text='e.g. "Additional solar panels installation"')
    quote_request = models.ForeignKey('services.QuoteRequest', null=True, blank=True, related_name='quotations',
                                      on_delete=models.SET_NULL, help_text='Website quote request this answers (optional)')
    source = models.ForeignKey('self', null=True, blank=True, related_name='derived', on_delete=models.SET_NULL,
                               editable=False, help_text='Quotation this invoice was created from')

    # Client (Sold to)
    client_name = models.CharField('Client name', max_length=150)
    client_company = models.CharField('Company', max_length=150, blank=True)
    client_phone = models.CharField('Phone', max_length=30, blank=True)
    client_email = models.EmailField('Email', blank=True)
    client_address = models.CharField('Address', max_length=250, blank=True)
    client_kra_pin = models.CharField('Client KRA / VAT PIN', max_length=20, blank=True)
    account_no = models.CharField('Client account no.', max_length=30, blank=True)

    # Ship to (site)
    ship_to_name = models.CharField('Ship to / site name', max_length=150, blank=True,
                                    help_text='Leave blank to use the client name')
    ship_to_address = models.CharField('Ship to / site address', max_length=250, blank=True,
                                       help_text='Leave blank to use the client address')

    # Dates, people & status
    issue_date = models.DateField('Date', default=timezone.localdate)
    valid_until = models.DateField(default=default_valid_until)
    required_date = models.DateField('Required by', null=True, blank=True)
    sales_person = models.CharField(max_length=100, blank=True)
    sales_phone = models.CharField('Sales person phone', max_length=30, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')

    # Money
    discount_type = models.CharField('Extra discount type', max_length=10, choices=DISCOUNT_TYPES, default='percent')
    discount_value = models.DecimalField('Extra discount', max_digits=12, decimal_places=2, default=0,
                                         help_text='Discount on the whole document (on top of any line discounts). '
                                                   'Leave 0 for none.')
    delivery_fee = models.DecimalField('Delivery (KSh)', max_digits=12, decimal_places=2, default=0)
    apply_tax = models.BooleanField('Charge VAT', default=True,
                                    help_text='Tick to charge VAT on items marked "VAT". Untick for no VAT at all.')
    tax_rate = models.DecimalField('VAT rate (%)', max_digits=5, decimal_places=2, default=default_tax_rate)

    notes = models.TextField('Notes to client', blank=True)
    terms = models.TextField('Terms & conditions', blank=True, default=default_terms)
    internal_notes = models.TextField(blank=True, help_text='Not shown on the document')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created']
        verbose_name = 'quotation / invoice'
        verbose_name_plural = 'quotations & invoices'

    def __str__(self):
        return f'{self.number or "New " + self.get_doc_type_display().lower()} – {self.client_name}'

    def save(self, *args, **kwargs):
        if not self.number:
            prefix = f'BNN-{self.PREFIX[self.doc_type]}{self.issue_date:%Y}-'
            n = Quotation.objects.filter(number__startswith=prefix).count() + 1
            while Quotation.objects.filter(number=f'{prefix}{n:04d}').exists():
                n += 1
            self.number = f'{prefix}{n:04d}'
        super().save(*args, **kwargs)

    def get_print_url(self):
        return reverse('quotations:print', args=[self.pk])

    def convert_to(self, doc_type):
        """Copy this document (with all items) as a new draft of another type, e.g. quotation -> invoice."""
        items = list(self.items.all())
        new = Quotation.objects.get(pk=self.pk)
        new.pk, new.number, new.status, new.doc_type, new.source_id = None, '', 'draft', doc_type, self.pk
        new.issue_date = timezone.localdate()
        new._state.adding = True
        new.save()
        for it in items:
            it.pk, it.quotation = None, new
            it.save()
        if self.doc_type == 'quotation' and doc_type in ('invoice', 'proforma') and self.status in ('draft', 'sent'):
            self.status = 'accepted'
            self.save(update_fields=['status'])
        return new

    @property
    def title_upper(self):
        return self.get_doc_type_display().upper()

    @property
    def ship_name(self):
        return self.ship_to_name or self.client_company or self.client_name

    @property
    def ship_address(self):
        return self.ship_to_address or self.client_address

    # ---- totals ----
    def _items(self):
        if not hasattr(self, '_items_cache'):
            self._items_cache = list(self.items.all())
        return self._items_cache

    @property
    def subtotal(self):
        """Sum of quantity × unit price, before any discounts."""
        return money(sum((i.gross for i in self._items()), Decimal('0')))

    @property
    def line_discounts(self):
        return money(sum((i.line_discount for i in self._items()), Decimal('0')))

    @property
    def extra_discount(self):
        base = self.subtotal - self.line_discounts
        if not self.discount_value or base <= 0:
            return money(0)
        amt = base * Decimal(self.discount_value) / 100 if self.discount_type == 'percent' else Decimal(self.discount_value)
        return money(min(amt, base))

    @property
    def discount_amount(self):
        return money(self.line_discounts + self.extra_discount)

    @property
    def discount_factor(self):
        """Share of each line left after the extra (document-level) discount."""
        base = self.subtotal - self.line_discounts
        if base <= 0:
            return Decimal('1')
        return (base - self.extra_discount) / base

    @property
    def taxable_amount(self):
        return money(self.subtotal - self.discount_amount)

    @property
    def tax_amount(self):
        if not self.apply_tax:
            return money(0)
        return money(sum((i.vat_amount for i in self._items()), Decimal('0')))

    @property
    def total(self):
        return money(self.subtotal - self.discount_amount + Decimal(self.delivery_fee or 0) + self.tax_amount)

    @property
    def is_expired(self):
        return self.valid_until < timezone.localdate()


class QuotationItem(models.Model):
    UNITS = [('ea', 'EA'), ('pcs', 'PCS'), ('set', 'SET'), ('lot', 'LOT'), ('m', 'M'), ('roll', 'ROLL'),
             ('hrs', 'HRS'), ('days', 'DAYS'), ('job', 'JOB'), ('kit', 'KIT')]
    quotation = models.ForeignKey(Quotation, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('store.Product', null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='Optional – pick a shop product to fill in name and price')
    item_code = models.CharField('Item', max_length=60, blank=True, help_text='Item code or short name')
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit = models.CharField(max_length=10, choices=UNITS, default='ea')
    unit_price = models.DecimalField('Unit price', max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField('Discount (KSh)', max_digits=12, decimal_places=2, default=0)
    taxable = models.BooleanField('VAT', default=True, help_text='Untick for VAT-exempt lines')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.description or self.item_code

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.description and not self.product and not self.item_code:
            raise ValidationError('Enter a description or pick a product.')

    def save(self, *args, **kwargs):
        if self.product:
            if not self.description:
                self.description = self.product.name
            if not self.item_code and self.product.sku:
                self.item_code = self.product.sku
            if not self.unit_price and self.product.price:
                self.unit_price = self.product.price
        super().save(*args, **kwargs)

    @property
    def gross(self):
        return money(Decimal(self.quantity or 0) * Decimal(self.unit_price or 0))

    @property
    def line_discount(self):
        return money(min(Decimal(self.discount or 0), self.gross))

    @property
    def line_total(self):
        """Amount for the line excluding VAT (after its own discount)."""
        return money(self.gross - self.line_discount)

    @property
    def vat_amount(self):
        q = self.quotation
        if not (q.apply_tax and self.taxable):
            return money(0)
        return money(self.line_total * q.discount_factor * Decimal(q.tax_rate) / 100)
