from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render

from .models import Quotation


@staff_member_required
def print_quotation(request, pk):
    quotation = get_object_or_404(Quotation.objects.prefetch_related('items'), pk=pk)
    return render(request, 'quotations/print.html', {'q': quotation})
