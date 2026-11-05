from django.urls import path

from . import views

app_name = 'services'

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.service_list, name='list'),
    path('services/<slug:slug>/', views.service_detail, name='detail'),
    path('quote/', views.quote, name='quote'),
    path('projects/', views.project_list, name='projects'),
    path('projects/<slug:slug>/', views.project_detail, name='project'),
]
