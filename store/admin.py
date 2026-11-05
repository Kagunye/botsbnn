from django.contrib import admin
from django.utils.html import format_html

from .models import Banner, Brand, Category, Order, OrderItem, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'icon', 'show_in_nav', 'order']
    list_editable = ['show_in_nav', 'order']
    list_filter = ['parent']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_partner', 'color']
    list_editable = ['is_partner']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['thumb', 'name', 'category', 'brand', 'price', 'old_price', 'stock',
                    'is_active', 'is_top_deal', 'is_recommended']
    list_display_links = ['thumb', 'name']
    list_editable = ['price', 'old_price', 'stock', 'is_active', 'is_top_deal', 'is_recommended']
    list_filter = ['is_active', 'is_top_deal', 'is_recommended', 'category', 'brand']
    search_fields = ['name', 'sku', 'short_description']
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['category', 'brand']
    inlines = [ProductImageInline]

    @admin.display(description='')
    def thumb(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;width:40px;object-fit:contain">', obj.image.url)
        return '—'


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'position', 'theme', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['position', 'is_active']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'price', 'quantity']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'phone', 'town', 'payment_method', 'status', 'order_total', 'created']
    list_editable = ['status']
    list_filter = ['status', 'payment_method', 'created']
    search_fields = ['full_name', 'email', 'phone']
    inlines = [OrderItemInline]

    @admin.display(description='Total (KSh)')
    def order_total(self, obj):
        return f'{obj.total:,.2f}'


admin.site.site_header = 'BNN Engineering Admin'
admin.site.site_title = 'BNN Engineering'
admin.site.index_title = 'Website management'
