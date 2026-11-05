from decimal import Decimal

from django import forms
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from store.models import Order, OrderItem, Product

from .cart import Cart

NAIROBI_FREE_DELIVERY = 'nairobi'
UPCOUNTRY_DELIVERY_FEE = Decimal('1000')


def _qty(request):
    try:
        return max(1, int(request.POST.get('quantity', 1)))
    except (TypeError, ValueError):
        return 1


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    if not product.has_price:
        msg = f'“{product.name}” is priced on request — contact us for a quote.'
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': msg}, status=400)
        messages.warning(request, msg)
        return redirect(product.get_absolute_url())
    cart = Cart(request)
    cart.add(product, _qty(request), override=request.POST.get('override') == '1')
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'count': len(cart), 'message': f'{product.name} added to cart'})
    messages.success(request, f'“{product.name}” added to your cart.')
    nxt = request.POST.get('next')
    if nxt and url_has_allowed_host_and_scheme(nxt, {request.get_host()}, request.is_secure()):
        return redirect(nxt)
    return redirect('cart:detail')


@require_POST
def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Cart(request).remove(product)
    messages.info(request, f'“{product.name}” removed from your cart.')
    return redirect('cart:detail')


def cart_detail(request):
    return render(request, 'cart/detail.html')


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'email', 'phone', 'town', 'address', 'payment_method', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Anything we should know? (optional)'}),
            'payment_method': forms.RadioSelect,
        }
        labels = {'town': 'Town / City', 'address': 'Delivery address'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'payment_method':
                field.widget.attrs.setdefault('class', 'form-control')


def checkout(request):
    cart = Cart(request)
    if not len(cart):
        messages.warning(request, 'Your cart is empty.')
        return redirect('store:shop')

    initial = {}
    if request.user.is_authenticated:
        u = request.user
        initial = {'full_name': u.get_full_name(), 'email': u.email}

    form = CheckoutForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            is_nairobi = NAIROBI_FREE_DELIVERY in order.town.lower()
            order.delivery_fee = Decimal('0') if is_nairobi else UPCOUNTRY_DELIVERY_FEE
            order.save()
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'],
                                         product_name=item['product'].name,
                                         price=item['price'], quantity=item['quantity'])
                p = item['product']
                p.stock = max(0, p.stock - item['quantity'])
                p.save(update_fields=['stock'])
        cart.clear()
        request.session['last_order_id'] = order.id
        return redirect('cart:order_complete', order_id=order.id)

    return render(request, 'cart/checkout.html', {
        'form': form, 'upcountry_fee': UPCOUNTRY_DELIVERY_FEE,
    })


def order_complete(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    allowed = request.session.get('last_order_id') == order.id or (
        request.user.is_authenticated and order.user_id == request.user.id)
    if not allowed:
        return redirect('services:home')
    return render(request, 'cart/order_complete.html', {'order': order})
