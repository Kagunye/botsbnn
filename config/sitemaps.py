"""sitemap.xml for Google / Bing: every public page the site wants indexed."""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class BaseSitemap(Sitemap):
    protocol = 'https'


class StaticPagesSitemap(BaseSitemap):
    changefreq = 'weekly'

    def items(self):
        return ['services:home', 'services:list', 'services:projects', 'services:quote',
                'pages:about', 'pages:contact', 'pages:how_to_pay', 'store:home', 'store:shop']

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return {'services:home': 1.0, 'services:list': 0.9, 'services:quote': 0.8}.get(item, 0.6)


class ServiceSitemap(BaseSitemap):
    changefreq = 'monthly'
    priority = 0.8

    def items(self):
        from services.models import Service
        return Service.objects.filter(is_active=True).order_by('pk')


class ProjectSitemap(BaseSitemap):
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        from services.models import Project
        return Project.objects.filter(is_published=True).order_by('pk')


class ProductSitemap(BaseSitemap):
    changefreq = 'weekly'
    priority = 0.5

    def items(self):
        from store.models import Product
        return Product.objects.filter(is_active=True).order_by('pk')

    def lastmod(self, obj):
        return obj.updated


class ShopCategorySitemap(BaseSitemap):
    changefreq = 'weekly'
    priority = 0.5

    def items(self):
        from store.models import Category
        return Category.objects.filter(products__is_active=True).distinct().order_by('pk')


class BrandSitemap(BaseSitemap):
    changefreq = 'monthly'
    priority = 0.4

    def items(self):
        from store.models import Brand
        return Brand.objects.filter(products__is_active=True).distinct().order_by('pk')


SITEMAPS = {
    'pages': StaticPagesSitemap, 'services': ServiceSitemap, 'projects': ProjectSitemap,
    'products': ProductSitemap, 'shop-categories': ShopCategorySitemap, 'brands': BrandSitemap,
}
