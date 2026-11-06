"""Numbers and recent activity for the admin dashboard (templates/admin/index.html)."""
from decimal import Decimal

from django import template
from django.utils import timezone

register = template.Library()


@register.simple_tag
def admin_dashboard():
    from pages.models import ContactMessage
    from quotations.models import Quotation
    from services.models import QuoteRequest, Service
    from store.models import Order, Product

    today = timezone.localdate()
    month_start = today.replace(day=1)
    docs = Quotation.objects.prefetch_related('items')

    open_quotes = [q for q in docs.filter(doc_type='quotation', status__in=['draft', 'sent'])]
    unpaid = [q for q in docs.filter(doc_type__in=['invoice', 'proforma']).exclude(status__in=['paid', 'rejected'])
              if q.doc_type == 'invoice']
    month_invoices = [q for q in docs.filter(doc_type='invoice', issue_date__gte=month_start)]

    def total(qs):
        return sum((q.total for q in qs), Decimal('0'))

    return {
        'today': today,
        'open_quotes': len(open_quotes), 'open_quotes_value': total(open_quotes),
        'unpaid': len(unpaid), 'unpaid_value': total(unpaid),
        'month_invoiced': total(month_invoices), 'month_invoice_count': len(month_invoices),
        'new_requests': QuoteRequest.objects.filter(status='new').count(),
        'unread_messages': ContactMessage.objects.filter(handled=False).count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
        'products': Product.objects.filter(is_active=True).count(),
        'services': Service.objects.filter(is_active=True).count(),
        'recent_docs': list(docs.order_by('-created')[:6]),
        'recent_requests': list(QuoteRequest.objects.select_related('service').order_by('-created')[:5]),
        'recent_messages': list(ContactMessage.objects.order_by('-created')[:5]),
        'recent_orders': list(Order.objects.order_by('-created')[:5]),
    }
