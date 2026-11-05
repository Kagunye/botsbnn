from django.db.models import Prefetch

from pages.models import SiteSettings

from .models import Category, Product


def site_context(request):
    """Site-wide settings (editable in admin) and shop categories that currently have products."""
    used = set(Product.objects.active().values_list('category_id', flat=True))
    children = Prefetch('children', queryset=Category.objects.filter(id__in=used))
    parents = (Category.objects.filter(parent__isnull=True, show_in_nav=True)
               .prefetch_related(children))
    nav = [c for c in parents if c.id in used or c.children.all()]
    return {
        'shop': SiteSettings.load(),
        'nav_categories': nav,
    }
