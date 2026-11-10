from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.urls import include, path, re_path
from django.views.static import serve

from .sitemaps import SITEMAPS


def robots_txt(request):
    """Tell search engines what to index and where the sitemap is."""
    lines = [
        'User-agent: *',
        'Disallow: /admin/',
        'Disallow: /cart/',
        'Disallow: /accounts/',
        'Disallow: /quotations/',
        'Allow: /',
        '',
        f'Sitemap: https://{request.get_host()}/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines) + '\n', content_type='text/plain')


urlpatterns = [
    path('sitemap.xml', sitemap, {'sitemaps': SITEMAPS}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('admin/', admin.site.urls),
    path('cart/', include('cart.urls')),
    path('accounts/', include('accounts.urls')),
    path('quotations/', include('quotations.urls')),
    path('', include('services.urls')),
    path('', include('pages.urls')),
    path('', include('store.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif settings.SERVE_MEDIA:
    # DEBUG is off: serve uploaded images directly (fine for a small site; a web server can take over later)
    urlpatterns += [re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})]
