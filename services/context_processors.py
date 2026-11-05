from .models import ServiceCategory


def service_nav(request):
    return {'nav_service_categories': ServiceCategory.objects.prefetch_related('services')}
