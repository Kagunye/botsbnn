from django.urls import path

from . import views

app_name = 'store'

urlpatterns = [
    path('shop/', views.home, name='home'),
    path('shop/products/', views.shop, name='shop'),
    path('shop/category/<slug:slug>/', views.category, name='category'),
    path('shop/brand/<slug:slug>/', views.brand, name='brand'),
    path('shop/product/<slug:slug>/', views.product_detail, name='product'),
]
