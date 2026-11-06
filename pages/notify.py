"""Email notifications through Zoho (settings.EMAIL_*).

Every send is wrapped so a mail problem never breaks a form: the customer's request is already saved.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse

log = logging.getLogger(__name__)


def _send(subject, body, to, reply_to=None):
    if not to:
        return False
    try:
        msg = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [to] if isinstance(to, str) else list(to),
                           reply_to=[reply_to] if reply_to else None)
        msg.send(fail_silently=False)
        return True
    except Exception:  # SMTP down, wrong password, timeout... never break the page
        log.exception('Email "%s" to %s could not be sent', subject, to)
        return False


def _admin_link(request, viewname, pk):
    try:
        return request.build_absolute_uri(reverse(viewname, args=[pk]))
    except Exception:
        return ''


def _company():
    from pages.models import SiteSettings
    return SiteSettings.load()


def quote_request(request, qr):
    s = _company()
    lines = [
        f'New quote request from the website',
        '',
        f'Name:      {qr.name}',
        f'Phone:     {qr.phone}',
        f'Email:     {qr.email or "-"}',
        f'Service:   {qr.service or "General enquiry"}',
        f'Location:  {qr.location}',
        '',
        'Job details:',
        qr.message or '-',
        '',
        f'Open in admin: {_admin_link(request, "admin:services_quoterequest_change", qr.pk)}',
    ]
    _send(f'New quote request: {qr.name} – {qr.service or "General enquiry"}', '\n'.join(lines),
          settings.NOTIFY_EMAIL, reply_to=qr.email or None)
    if qr.email:
        _send(f'We received your quote request – {s.name}', '\n'.join([
            f'Hello {qr.name},',
            '',
            f'Thank you for contacting {s.name}. We have received your request for '
            f'"{qr.service or "a quotation"}" at {qr.location}.',
            f'One of our engineers will call you on {qr.phone} shortly to arrange a site survey.',
            '',
            f'Need us sooner? Call {", ".join(s.phones) or s.email} or reply to this email.',
            '',
            f'{s.name}',
            s.tagline,
        ]), qr.email, reply_to=settings.NOTIFY_EMAIL)


def contact_message(request, m):
    s = _company()
    _send(f'Website message: {m.subject}', '\n'.join([
        'New message from the website contact form',
        '',
        f'Name:   {m.name}',
        f'Email:  {m.email}',
        f'Phone:  {m.phone or "-"}',
        f'Subject: {m.subject}',
        '',
        m.message,
        '',
        f'Open in admin: {_admin_link(request, "admin:pages_contactmessage_change", m.pk)}',
    ]), settings.NOTIFY_EMAIL, reply_to=m.email)
    _send(f'Thanks for contacting {s.name}', '\n'.join([
        f'Hello {m.name},',
        '',
        f'Thank you for your message ("{m.subject}"). Our team will get back to you shortly.',
        '',
        f'{s.name}',
        f'{", ".join(s.phones)}',
    ]), m.email, reply_to=settings.NOTIFY_EMAIL)


def new_order(request, order):
    s = _company()
    items = '\n'.join(f'  {i.quantity} x {i.product_name} @ KSh {i.price:,.2f}' for i in order.items.all())
    total = getattr(order, 'total', None)
    total_line = f'Total: KSh {total:,.2f}' if total is not None else ''
    _send(f'New shop order #{order.pk} – {order.full_name}', '\n'.join([
        f'New order #{order.pk} from the online shop',
        '',
        f'Customer: {order.full_name}',
        f'Phone:    {order.phone}',
        f'Email:    {order.email}',
        f'Delivery: {order.address}, {order.town}',
        f'Payment:  {order.get_payment_method_display()}',
        '',
        'Items:',
        items or '  -',
        f'Delivery fee: KSh {order.delivery_fee:,.2f}',
        total_line,
        '',
        f'Notes: {order.notes or "-"}',
        '',
        f'Open in admin: {_admin_link(request, "admin:store_order_change", order.pk)}',
    ]), settings.NOTIFY_EMAIL, reply_to=order.email)
    p = s.payment
    _send(f'Order #{order.pk} received – {s.name}', '\n'.join([
        f'Hello {order.full_name},',
        '',
        f'Thank you for your order #{order.pk}. We will call you on {order.phone} to confirm delivery.',
        '',
        items,
        total_line,
        '',
        'How to pay:',
        f'  M-PESA Paybill {p["paybill"]}, Account {p["account_no"]}',
        f'  {p["bank"]} – {p["account_name"]}, Acc. {p["account_no"]}',
        f'  Use order #{order.pk} as the reference.',
        '',
        f'{s.name}',
    ]), order.email, reply_to=settings.NOTIFY_EMAIL)
