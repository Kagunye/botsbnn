from django.urls import path

from . import views

app_name = 'quotations'

urlpatterns = [
    path('<int:pk>/print/', views.print_quotation, name='print'),
]
