from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Quotation, QuotationItem


class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 3
    fields = ['order', 'product', 'item_code', 'description', 'quantity', 'unit', 'unit_price', 'discount',
              'taxable', 'vat_display', 'line_total_display']
    readonly_fields = ['vat_display', 'line_total_display']
    autocomplete_fields = ['product']

    @admin.display(description='VAT (KSh)')
    def vat_display(self, obj):
        return f'{obj.vat_amount:,.2f}' if obj and obj.pk else '0.00'

    @admin.display(description='Total (KSh)')
    def line_total_display(self, obj):
        return f'{obj.line_total:,.2f}' if obj and obj.pk else '0.00'


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ['number', 'doc_type', 'client_name', 'title', 'issue_date', 'status',
                    'vat_flag', 'total_display', 'print_link']
    list_filter = ['doc_type', 'status', 'apply_tax', 'issue_date']
    list_editable = ['status']
    search_fields = ['number', 'client_name', 'client_company', 'client_phone', 'client_email', 'title']
    date_hierarchy = 'issue_date'
    inlines = [QuotationItemInline]
    readonly_fields = ['number', 'totals_box', 'print_button', 'source']
    autocomplete_fields = ['quote_request']
    actions = ['make_invoice', 'make_proforma', 'mark_sent', 'mark_accepted', 'mark_paid', 'duplicate']
    save_on_top = True
    fieldsets = [
        (None, {'fields': [('doc_type', 'number', 'status'), 'title', ('issue_date', 'valid_until', 'required_date'),
                           ('sales_person', 'sales_phone'), 'quote_request', 'source', 'print_button']}),
        ('Sold to (client)', {'fields': [('client_name', 'client_company'), ('client_phone', 'client_email'),
                                         'client_address', ('client_kra_pin', 'account_no')]}),
        ('Ship to (site)', {'fields': ['ship_to_name', 'ship_to_address'], 'classes': ['collapse'],
                            'description': 'Leave blank to use the client details.'}),
        ('Discount, delivery & VAT', {
            'fields': [('discount_type', 'discount_value'), 'delivery_fee', ('apply_tax', 'tax_rate'), 'totals_box'],
            'description': 'Totals update live as you edit the items below. Tick "Charge VAT" to add VAT on items '
                           'marked VAT; untick to quote without VAT. Each item can also have its own discount.'}),
        ('Notes & terms', {'fields': ['notes', 'terms', 'internal_notes'], 'classes': ['collapse']}),
    ]

    class Media:
        js = ['admin/quotation.js']
        css = {'all': ['admin/quotation.css']}

    @admin.display(description='VAT', boolean=True)
    def vat_flag(self, obj):
        return obj.apply_tax

    @admin.display(description='Total (KSh)')
    def total_display(self, obj):
        return f'{obj.total:,.2f}'

    @admin.display(description='')
    def print_link(self, obj):
        return format_html('<a href="{}" target="_blank">🖨 View / print</a>', obj.get_print_url())

    @admin.display(description='Document')
    def print_button(self, obj):
        if not obj or not obj.pk:
            return 'Save first, then you can view, print, save as PDF or convert to an invoice.'
        buttons = [format_html('<a class="button" href="{}" target="_blank" style="padding:6px 14px">'
                               '🖨 View / Print / Save as PDF</a>', obj.get_print_url())]
        if obj.doc_type != 'invoice':
            buttons.append(format_html(
                '<a class="button q-convert" href="{}" style="padding:6px 14px">🧾 Convert to Invoice</a>',
                reverse('admin:quotations_quotation_convert', args=[obj.pk, 'invoice'])))
        if obj.doc_type == 'quotation':
            buttons.append(format_html(
                '<a class="button" href="{}" style="padding:6px 14px">Convert to Proforma</a>',
                reverse('admin:quotations_quotation_convert', args=[obj.pk, 'proforma'])))
        derived = obj.derived.all()
        if derived:
            buttons.append(format_html('<span style="margin-left:8px">Already converted: {}</span>', ', '.join(
                d.number for d in derived)))
        if obj.source_id:
            buttons.append(format_html('<span style="margin-left:8px">Created from {}</span>', obj.source.number))
        return format_html(' '.join(['{}'] * len(buttons)), *buttons)

    def get_urls(self):
        custom = [path('<int:pk>/convert/<str:doc_type>/', self.admin_site.admin_view(self.convert_view),
                       name='quotations_quotation_convert')]
        return custom + super().get_urls()

    def convert_view(self, request, pk, doc_type):
        obj = get_object_or_404(Quotation, pk=pk)
        if doc_type not in dict(Quotation.DOC_TYPES) or not self.has_add_permission(request):
            messages.error(request, 'Not allowed.')
            return redirect('admin:quotations_quotation_change', pk)
        label = dict(Quotation.DOC_TYPES)[doc_type]
        if request.method == 'POST':
            new = obj.convert_to(doc_type)
            messages.success(request, f'{obj.number} converted to {label} {new.number}. '
                                      f'Check the details, then print or send it.')
            return redirect('admin:quotations_quotation_change', new.pk)
        context = {**self.admin_site.each_context(request), 'opts': self.model._meta, 'obj': obj,
                   'label': label, 'title': f'Convert {obj.number} to {label}'}
        return TemplateResponse(request, 'admin/quotations/convert_confirm.html', context)

    @admin.display(description='Totals')
    def totals_box(self, obj):
        def v(attr):
            return f'{getattr(obj, attr):,.2f}' if obj and obj.pk else '0.00'
        delivery = f'{obj.delivery_fee:,.2f}' if obj and obj.pk else '0.00'
        return format_html(
            '<table class="q-totals">'
            '<tr><th>Subtotal</th><td>KSh <span id="q-subtotal">{}</span></td></tr>'
            '<tr><th>Discount</th><td>− KSh <span id="q-discount">{}</span></td></tr>'
            '<tr><th>Delivery</th><td>KSh <span id="q-delivery">{}</span></td></tr>'
            '<tr><th>VAT <span id="q-rate"></span></th><td>KSh <span id="q-tax">{}</span></td></tr>'
            '<tr class="q-grand"><th>TOTAL</th><td>KSh <span id="q-total">{}</span></td></tr>'
            '</table>',
            v('subtotal'), v('discount_amount'), delivery, v('tax_amount'), v('total'))

    def _copy_as(self, request, queryset, doc_type):
        made = [q.convert_to(doc_type) for q in queryset]
        label = dict(Quotation.DOC_TYPES)[doc_type]
        if len(made) == 1:
            messages.success(request, f'{label} {made[0].number} created.')
            return redirect('admin:quotations_quotation_change', made[0].pk)
        messages.success(request, f'{len(made)} {label.lower()}s created.')

    @admin.action(description='Convert selected to INVOICE')
    def make_invoice(self, request, queryset):
        return self._copy_as(request, queryset, 'invoice')

    @admin.action(description='Convert selected to PROFORMA INVOICE')
    def make_proforma(self, request, queryset):
        return self._copy_as(request, queryset, 'proforma')

    @admin.action(description='Duplicate selected (same type, as draft)')
    def duplicate(self, request, queryset):
        made = [q.convert_to(q.doc_type) for q in queryset]
        messages.success(request, f'Duplicated {len(made)} document(s) as drafts.')

    @admin.action(description='Mark selected as sent to client')
    def mark_sent(self, request, queryset):
        queryset.update(status='sent')

    @admin.action(description='Mark selected as accepted')
    def mark_accepted(self, request, queryset):
        queryset.update(status='accepted')

    @admin.action(description='Mark selected as paid')
    def mark_paid(self, request, queryset):
        queryset.update(status='paid')
