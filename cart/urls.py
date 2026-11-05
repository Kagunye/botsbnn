from django.urls import path

from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='detail'),
    path('add/<int:product_id>/', views.cart_add, name='add'),
    path('remove/<int:product_id>/', views.cart_remove, name='remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:order_id>/complete/', views.order_complete, name='order_complete'),
]
