from django.core.paginator import Paginator
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, render

from pages.models import Advert

from .models import Banner, Brand, Category, Product

SORT_OPTIONS = {
    'newest': ('-created', 'Newest'),
    'price_asc': ('price', 'Price: low to high'),
    'price_desc': ('-price', 'Price: high to low'),
    'name': ('name', 'Name A–Z'),
}


def home(request):
    banners = Banner.objects.filter(is_active=True)
    products = Product.objects.active().select_related('brand', 'category')
    context = {
        'hero_main': banners.filter(position='hero_main'),
        'hero_side': banners.filter(position='hero_side')[:2],
        'promos': banners.filter(position='promo')[:2],
        'promos_alt': banners.filter(position='promo_alt')[:2],
        'top_deals': products.filter(is_top_deal=True)[:12],
        'recommended': products.filter(is_recommended=True)[:12],
        'partners': Brand.objects.filter(is_partner=True),
        'shop_ads': Advert.objects.filter(is_active=True, show_in_shop_slider=True)[:12],
        'promo_ads': list(Advert.objects.filter(is_active=True, show_in_shop_promos=True)[:8]),
        'home_categories': Category.objects.filter(parent__isnull=True).filter(
            Q(products__is_active=True) | Q(children__products__is_active=True)).distinct()[:6],
    }
    return render(request, 'store/home.html', context)


def _product_list(request, queryset, title, extra=None):
    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(name__icontains=q) | Q(short_description__icontains=q) |
            Q(brand__name__icontains=q) | Q(category__name__icontains=q) | Q(sku__iexact=q)
        )
    available_brands = Brand.objects.filter(id__in=queryset.values('brand')).order_by('name')
    brand_slugs = request.GET.getlist('brand')
    if brand_slugs:
        queryset = queryset.filter(brand__slug__in=brand_slugs)
    min_price, max_price = request.GET.get('min'), request.GET.get('max')
    if min_price and min_price.isdigit():
        queryset = queryset.filter(price__gte=min_price)
    if max_price and max_price.isdigit():
        queryset = queryset.filter(price__lte=max_price)
    if request.GET.get('sale'):
        queryset = queryset.filter(old_price__isnull=False)

    sort = request.GET.get('sort', 'newest')
    field = SORT_OPTIONS.get(sort, SORT_OPTIONS['newest'])[0]
    if 'price' in field:  # priced-on-request items always go last
        expr = F('price').desc(nulls_last=True) if field.startswith('-') else F('price').asc(nulls_last=True)
        queryset = queryset.order_by(expr)
    else:
        queryset = queryset.order_by(field)

    page = Paginator(queryset.select_related('brand', 'category'), 24).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)

    context = {
        'title': title,
        'page_obj': page,
        'products': page.object_list,
        'q': q,
        'sort': sort,
        'sort_options': [(k, v[1]) for k, v in SORT_OPTIONS.items()],
        'brands': available_brands,
        'selected_brands': brand_slugs,
        'querystring': params.urlencode(),
        'all_categories': Category.objects.filter(parent__isnull=True).prefetch_related('children'),
    }
    if extra:
        context.update(extra)
    return render(request, 'store/product_list.html', context)


def shop(request):
    q = request.GET.get('q', '').strip()
    title = f'Search results for “{q}”' if q else 'Shop'
    return _product_list(request, Product.objects.active(), title)


def category(request, slug):
    cat = get_object_or_404(Category, slug=slug)
    qs = Product.objects.active().filter(category_id__in=cat.descendant_ids())
    return _product_list(request, qs, cat.name, {'category': cat})


def brand(request, slug):
    b = get_object_or_404(Brand, slug=slug)
    return _product_list(request, Product.objects.active().filter(brand=b), b.name, {'brand': b})


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related('brand', 'category').prefetch_related('gallery'),
                                slug=slug, is_active=True)
    related = (Product.objects.active().filter(category=product.category)
               .exclude(pk=product.pk).select_related('brand')[:6])
    return render(request, 'store/product_detail.html', {'product': product, 'related': related})
