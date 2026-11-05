from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from .models import Project, ProjectImage, QuoteRequest, Service, ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'has_photo', 'order']
    list_editable = ['order']
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(description='Own photo', boolean=True)
    def has_photo(self, obj):
        return bool(obj.image)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_featured', 'is_active', 'order']
    list_editable = ['is_featured', 'is_active', 'order']
    list_filter = ['category', 'is_featured', 'is_active']
    search_fields = ['name', 'summary', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'service', 'location', 'status', 'created', 'quotation_links']
    list_editable = ['status']
    list_filter = ['status', 'service__category', 'created']
    search_fields = ['name', 'phone', 'email', 'location', 'message']
    readonly_fields = ['created']
    actions = ['create_quotation']

    @admin.display(description='Quotations')
    def quotation_links(self, obj):
        qs = obj.quotations.all()
        if not qs:
            return '—'
        return format_html_join(', ', '<a href="{}">{}</a>',
                                ((reverse('admin:quotations_quotation_change', args=[q.pk]), q.number) for q in qs))

    @admin.action(description='Create a quotation from selected request')
    def create_quotation(self, request, queryset):
        from quotations.models import Quotation, QuotationItem
        created = []
        for qr in queryset:
            q = Quotation.objects.create(
                quote_request=qr, client_name=qr.name, client_phone=qr.phone, client_email=qr.email,
                client_address=qr.location, title=str(qr.service) if qr.service else 'Electrical works',
                internal_notes=qr.message)
            QuotationItem.objects.create(quotation=q, description=str(qr.service or 'Labour & materials'),
                                         quantity=1, unit='job', unit_price=0)
            if qr.status == 'new':
                qr.status = 'contacted'
                qr.save(update_fields=['status'])
            created.append(q)
        if len(created) == 1:
            messages.success(request, f'Quotation {created[0].number} created — add items and prices.')
            return redirect('admin:quotations_quotation_change', created[0].pk)
        messages.success(request, f'{len(created)} quotations created.')


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 3
    fields = ['preview', 'image', 'caption', 'order']
    readonly_fields = ['preview']

    @admin.display(description='')
    def preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:4px">', obj.image.url)
        return ''


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['thumb', 'title', 'service', 'location', 'completed_on', 'show_on_home', 'is_published', 'order']
    list_display_links = ['thumb', 'title']
    list_editable = ['show_on_home', 'is_published', 'order']
    list_filter = ['is_published', 'show_on_home', 'service__category', 'service']
    search_fields = ['title', 'location', 'client', 'summary', 'description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['cover_preview']
    inlines = [ProjectImageInline]
    fieldsets = [
        (None, {'fields': ['title', 'slug', 'service', ('location', 'client'), 'completed_on']}),
        ('Text', {'fields': ['summary', 'description']}),
        ('Main photo', {'fields': ['cover_image', 'cover_preview'],
                        'description': 'This photo appears on the homepage. Add more photos in the gallery below.'}),
        ('Visibility', {'fields': [('is_published', 'show_on_home'), 'order']}),
    ]

    @admin.display(description='')
    def thumb(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" style="height:48px;width:72px;object-fit:cover;border-radius:4px">',
                               obj.cover_image.url)
        return '—'

    @admin.display(description='Preview')
    def cover_preview(self, obj):
        if obj and obj.cover_image:
            return format_html('<img src="{}" style="max-height:220px;border-radius:6px">', obj.cover_image.url)
        return 'Upload a photo and save to see a preview.'
