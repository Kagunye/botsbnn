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

    # ---- metrics ----
    from django.db.models import Count
    quotes = list(docs.filter(doc_type='quotation'))
    converted_ids = set(Quotation.objects.filter(source__isnull=False).values_list('source_id', flat=True))
    won = [q for q in quotes if q.status == 'accepted' or q.pk in converted_ids]
    decided = [q for q in quotes if q.status in ('accepted', 'rejected', 'expired') or q.pk in converted_ids]
    conversion = round(100 * len(won) / len(decided)) if decided else None
    avg_quote = (total(quotes) / len(quotes)) if quotes else Decimal('0')

    def month_add(d, n):
        y, m = divmod(d.month - 1 + n, 12)
        return d.replace(year=d.year + y, month=m + 1, day=1)

    last_month_start = month_add(month_start, -1)
    quotes_this_month = sum(1 for q in quotes if q.issue_date >= month_start)
    quotes_last_month = sum(1 for q in quotes if last_month_start <= q.issue_date < month_start)

    # invoiced per month, last 6 months (oldest first)
    invoices = list(docs.filter(doc_type='invoice', issue_date__gte=month_add(month_start, -5)))
    trend = []
    for i in range(-5, 1):
        start, end = month_add(month_start, i), month_add(month_start, i + 1)
        trend.append({'label': start.strftime('%b'), 'value': total(q for q in invoices if start <= q.issue_date < end)})
    peak = max((m['value'] for m in trend), default=Decimal('0')) or Decimal('1')
    for m in trend:
        m['pct'] = int(m['value'] / peak * 100) if m['value'] else 0
    # smooth area chart (SVG 600 x 170): x evenly spaced, y from the share of the best month
    W, H, PAD = 600, 170, 14
    pts = [(round(i * W / (len(trend) - 1), 1), round(H - PAD - (m['pct'] / 100) * (H - 2 * PAD), 1))
           for i, m in enumerate(trend)]
    path = f'M{pts[0][0]},{pts[0][1]}'
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        cx = round((x0 + x1) / 2, 1)
        path += f' C{cx},{y0} {cx},{y1} {x1},{y1}'
    for m, (x, y) in zip(trend, pts):
        m['x'], m['y'] = x, y
        m['xpct'] = round(100 * x / W, 2)
    chart = {'line': path, 'area': f'{path} L{W},{H} L0,{H} Z', 'w': W, 'h': H,
             'best': max(trend, key=lambda m: m['value'])}

    status_labels = dict(Quotation.STATUS)
    status_counts = {s: 0 for s in ('draft', 'sent', 'accepted', 'rejected', 'expired')}
    for q in quotes:
        if q.status in status_counts:
            status_counts[q.status] += 1
    n_quotes = len(quotes) or 1
    statuses = [{'key': k, 'label': status_labels[k], 'count': v, 'pct': round(100 * v / n_quotes)}
                for k, v in status_counts.items()]

    top_services = list(QuoteRequest.objects.exclude(service=None).values('service__name')
                        .annotate(n=Count('id')).order_by('-n')[:5])
    top_max = top_services[0]['n'] if top_services else 1
    for s in top_services:
        s['pct'] = round(100 * s['n'] / top_max)

    return {
        'conversion': conversion, 'quotes_total': len(quotes), 'avg_quote': avg_quote,
        'quotes_this_month': quotes_this_month, 'quotes_last_month': quotes_last_month,
        'quotes_delta': quotes_this_month - quotes_last_month,
        'trend': trend, 'trend_total': total(invoices), 'chart': chart,
        'statuses': statuses, 'top_services': top_services,
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
