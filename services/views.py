from django import forms
from django.contrib import messages
from django.db.models import Case, Count, IntegerField, When
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from pages.models import Advert, ProcessStep, WhyChooseItem
from store.models import Brand, Product

from .models import Project, QuoteRequest, Service, ServiceCategory


class QuoteForm(forms.ModelForm):
    class Meta:
        model = QuoteRequest
        fields = ['service', 'name', 'phone', 'email', 'location', 'message']
        widgets = {'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What do you need done? Size of the site, timelines, etc.'})}
        labels = {'service': 'Service needed', 'name': 'Your name', 'phone': 'Phone number'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service'].queryset = Service.objects.filter(is_active=True).select_related('category')
        self.fields['service'].empty_label = 'General enquiry / not sure'
        self.fields['location'].widget.attrs['placeholder'] = 'e.g. Westlands, Nairobi'
        for name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-select' if name == 'service' else 'form-control')


def _company_photo():
    from pages.models import SiteSettings
    s = SiteSettings.load()
    if s.company_image:
        return s.company_image
    for slug in ('control-panel-design-fabrication', 'solar-installations', 'backup-power'):
        svc = Service.objects.filter(slug=slug).exclude(image='').first()
        if svc:
            return svc.image
    svc = Service.objects.exclude(image='').first()
    return svc.image if svc else None


def _home_brands():
    brands = Brand.objects.filter(is_partner=True).annotate(n=Count('products'))
    with_logo = brands.exclude(logo='').order_by('-n', 'name')
    if with_logo.count() >= 6:
        return with_logo[:18]
    return brands.annotate(no_logo=Case(When(logo='', then=1), default=0, output_field=IntegerField())
                           ).order_by('no_logo', '-n', 'name')[:18]


def home(request):
    categories = ServiceCategory.objects.prefetch_related('services')
    context = {
        'service_categories': categories,
        'featured_services': Service.objects.filter(is_active=True, is_featured=True).select_related('category')[:8],
        'shop_products': Product.objects.active().exclude(image='').filter(is_recommended=True)[:6],
        # Logo brands only; falls back to name chips if fewer than 6 logos have been uploaded
        'partners': _home_brands(),
        'quote_form': QuoteForm(),
        'slider_services': sorted(
            Service.objects.filter(is_active=True).select_related('category').prefetch_related('category__services'),
            key=lambda s: (not s.image, s.category.order, s.order)),
        'projects': Project.objects.filter(is_published=True, show_on_home=True).select_related('service')[:6],
        'adverts': Advert.objects.filter(is_active=True, show_on_home=True)[:12],
        'process_steps': ProcessStep.objects.all(),
        'why_items': WhyChooseItem.objects.filter(place='home'),
        'company_photo': _company_photo(),
    }
    return render(request, 'services/home.html', context)


def service_list(request):
    categories = ServiceCategory.objects.prefetch_related('services')
    active = request.GET.get('category')
    return render(request, 'services/list.html', {'categories': categories, 'active_category': active})


def service_detail(request, slug):
    service = get_object_or_404(Service.objects.select_related('category'), slug=slug, is_active=True)
    related = service.category.services.filter(is_active=True).exclude(pk=service.pk)
    form = QuoteForm(initial={'service': service})
    return render(request, 'services/detail.html', {'service': service, 'related': related, 'form': form})


def quote(request):
    initial = {}
    slug = request.GET.get('service')
    if slug:
        initial['service'] = Service.objects.filter(slug=slug).first()
    form = QuoteForm(request.POST or None, initial=initial)
    if request.method == 'POST':
        if form.is_valid():
            q = form.save()
            messages.success(request, f'Thanks {q.name}! Your quote request has been received — '
                                      f'our team will call you on {q.phone} shortly.')
            nxt = request.POST.get('next')
            if nxt and url_has_allowed_host_and_scheme(nxt, {request.get_host()}, request.is_secure()):
                return redirect(nxt)
            return redirect('services:quote')
        messages.error(request, 'Please check the highlighted fields.')
    return render(request, 'services/quote.html', {'form': form})


def project_list(request):
    projects = Project.objects.filter(is_published=True).select_related('service__category')
    service_slug = request.GET.get('service')
    if service_slug:
        projects = projects.filter(service__slug=service_slug)
    used_services = Service.objects.filter(projects__is_published=True).distinct()
    return render(request, 'services/projects.html', {
        'projects': projects, 'used_services': used_services, 'active_service': service_slug})


def project_detail(request, slug):
    project = get_object_or_404(Project.objects.select_related('service__category').prefetch_related('images'),
                                slug=slug, is_published=True)
    more = Project.objects.filter(is_published=True).exclude(pk=project.pk)[:3]
    return render(request, 'services/project_detail.html', {'project': project, 'more': more})
