from decimal import Decimal

from django.conf import settings

from store.models import Product


class Cart:
    """Session-backed shopping cart: {product_id: {'quantity': n, 'price': 'x.xx'}}."""

    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.setdefault(settings.CART_SESSION_ID, {})

    def add(self, product, quantity=1, override=False):
        pid = str(product.id)
        item = self.cart.setdefault(pid, {'quantity': 0, 'price': str(product.price)})
        item['quantity'] = quantity if override else item['quantity'] + quantity
        item['price'] = str(product.price)
        if item['quantity'] <= 0:
            del self.cart[pid]
        self.save()

    def remove(self, product):
        self.cart.pop(str(product.id), None)
        self.save()

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.cart = self.session[settings.CART_SESSION_ID]
        self.save()

    def save(self):
        self.session.modified = True

    def __iter__(self):
        products = Product.objects.filter(id__in=self.cart.keys()).select_related('brand')
        by_id = {str(p.id): p for p in products}
        for pid, item in list(self.cart.items()):
            product = by_id.get(pid)
            if product is None:
                continue
            price = Decimal(item['price'])
            yield {
                'product': product,
                'quantity': item['quantity'],
                'price': price,
                'total': price * item['quantity'],
            }

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    @property
    def subtotal(self):
        return sum((Decimal(i['price']) * i['quantity'] for i in self.cart.values()), Decimal('0'))
