"""Structured data (JSON-LD) so Google shows the business name and logo."""
import json

from django import template
from django.templatetags.static import static
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def seo_jsonld(context):
    request = context.get('request')
    shop = context.get('shop')
    if not request or not shop:
        return ''
    base = f'{request.scheme}://{request.get_host()}'
    logo = base + static('img/icons/icon-512.png')
    same_as = [u for u in (shop.facebook, shop.instagram, shop.linkedin, shop.twitter) if u]
    website = {
        '@context': 'https://schema.org', '@type': 'WebSite',
        'name': shop.name, 'alternateName': ['BNN', 'BNN Engineering Limited'], 'url': base + '/',
    }
    business = {
        '@context': 'https://schema.org', '@type': 'Electrician',
        '@id': base + '/#business', 'name': shop.name, 'legalName': shop.account_name or shop.name,
        'url': base + '/', 'logo': logo, 'image': base + static('img/logo-full.png'),
        'description': 'Electrical engineering contractor in Nairobi: backup power, UPS, generators, wiring, '
                       'switchgear, control panels, electric fencing, automatic gates and solar.',
        'telephone': (shop.phones[0] if shop.phones else ''), 'email': shop.email,
        'address': {'@type': 'PostalAddress', 'streetAddress': shop.address, 'addressLocality': 'Nairobi',
                    'addressCountry': 'KE'},
        'areaServed': [{'@type': 'Country', 'name': 'Kenya'}, {'@type': 'Place', 'name': 'East Africa'}],
        'priceRange': 'KSh',
    }
    if same_as:
        business['sameAs'] = same_as
    def block(d):  # escape '<' inside the JSON so no value can close the <script> tag early
        return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False).replace('<', '\\u003c') + '</script>'
    return mark_safe(''.join(block(d) for d in (website, business)))
