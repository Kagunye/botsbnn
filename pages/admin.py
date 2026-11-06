from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import redirect
from django.urls import reverse

from .models import (FAQ, Advert, ContactMessage, FeatureBanner, HomePanel, Industry, ProcessStep, SiteSettings,
                     Testimonial, WhyChooseItem)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'subject', 'created', 'handled']
    list_editable = ['handled']
    list_filter = ['handled', 'created']
    search_fields = ['name', 'email', 'subject', 'message']


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Company details', {'fields': ['name', 'tagline', 'email', ('phone1', 'phone2'), 'whatsapp',
                                        'address', 'postal_address', 'hours', ('kra_pin', 'reg_no')]}),
        ('Payment details', {'fields': ['bank_name', 'account_name', 'account_no', 'paybill']}),
        ('Social media links', {'fields': ['facebook', 'instagram', 'linkedin', 'twitter']}),
        ('Homepage', {'fields': ['hero_badge', 'hero_title', 'hero_highlight', 'hero_text',
                                 ('stat1_value', 'stat1_label'), ('stat2_value', 'stat2_label'),
                                 ('stat3_value', 'stat3_label'), 'services_intro', 'cta_title', 'cta_text',
                                 'show_shop_on_home']}),
        ('Homepage company section', {'fields': ['company_kicker', 'company_title', 'company_image',
                                                 ('badge_value', 'badge_label')]}),
        ('About page & footer', {'fields': ['about_title', 'about_body', 'footer_about']}),
        ('Quotations', {'fields': ['default_tax_rate', 'quotation_validity_days', 'quotation_terms']}),
    ]

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        return redirect(reverse('admin:pages_sitesettings_change', args=[SiteSettings.load().pk]))


@admin.register(ProcessStep)
class ProcessStepAdmin(admin.ModelAdmin):
    list_display = ['order', 'icon', 'title', 'text']
    list_display_links = ['title']
    list_editable = ['order']


@admin.register(WhyChooseItem)
class WhyChooseItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'place', 'icon', 'order']
    list_editable = ['order']
    list_filter = ['place']


@admin.register(Advert)
class AdvertAdmin(admin.ModelAdmin):
    list_display = ['thumb', 'title', 'link', 'is_active', 'show_in_shop_slider', 'show_in_shop_promos', 'order']
    list_display_links = ['thumb', 'title']
    list_editable = ['is_active', 'show_in_shop_slider', 'show_in_shop_promos', 'order']
    list_filter = ['is_active', 'show_in_shop_slider', 'show_in_shop_promos']
    readonly_fields = ['preview']
    fields = ['title', 'image', 'preview', 'caption', 'link', 'is_active',
              ('show_in_shop_slider', 'show_in_shop_promos'), 'order']

    @admin.display(description='')
    def thumb(self, obj):
        return format_html('<img src="{}" style="height:70px;border-radius:4px">', obj.image.url) if obj.image else '—'

    @admin.display(description='Preview')
    def preview(self, obj):
        if obj and obj.image:
            return format_html('<a href="{0}" target="_blank" download><img src="{0}" style="max-height:340px;border-radius:6px"></a>'
                               '<br><a href="{0}" download>⬇ Download image for social media</a>', obj.image.url)
        return 'Upload an image and save to see it here.'


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ['title', 'icon', 'text', 'is_active', 'order']
    list_editable = ['is_active', 'order']


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'rating', 'service', 'is_published', 'order']
    list_editable = ['is_published', 'order']
    list_filter = ['is_published', 'rating']
    search_fields = ['name', 'role', 'quote']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'is_published', 'order']
    list_editable = ['is_published', 'order']
    search_fields = ['question', 'answer']


@admin.register(HomePanel)
class HomePanelAdmin(admin.ModelAdmin):
    list_display = ['thumb', 'title', 'link_text', 'link', 'is_active', 'order']
    list_display_links = ['thumb', 'title']
    list_editable = ['is_active', 'order']

    @admin.display(description='')
    def thumb(self, obj):
        return format_html('<img src="{}" style="height:56px;width:84px;object-fit:cover;border-radius:4px">', obj.image.url) if obj.image else '—'


@admin.register(FeatureBanner)
class FeatureBannerAdmin(admin.ModelAdmin):
    list_display = ['thumb', 'title', 'button_text', 'link', 'is_active', 'order']
    list_display_links = ['thumb', 'title']
    list_editable = ['is_active', 'order']

    @admin.display(description='')
    def thumb(self, obj):
        return format_html('<img src="{}" style="height:56px;width:110px;object-fit:cover;border-radius:4px">', obj.image.url) if obj.image else 'No photo yet'
