from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    icon = models.CharField(max_length=50, default='sun', help_text='Bootstrap icon name, e.g. "sun", "battery-charging"')
    description = models.TextField(blank=True)
    show_in_nav = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return f'{self.parent} › {self.name}' if self.parent else self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:category', args=[self.slug])

    def descendant_ids(self):
        ids = [self.id]
        for child in self.children.all():
            ids += child.descendant_ids()
        return ids


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True)
    color = models.CharField(max_length=7, default='#333333', help_text='Text colour used when no logo is uploaded')
    is_partner = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:brand', args=[self.slug])


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.PROTECT)
    brand = models.ForeignKey(Brand, related_name='products', null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    sku = models.CharField(max_length=50, blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    specifications = models.TextField(blank=True, help_text='One "Key: Value" per line')
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                help_text='Leave blank to show "Price on request" (customers ask for a quote)')
    old_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                    help_text='Original price; set higher than price to show a SALE badge')
    image = models.ImageField(upload_to='products/', blank=True)
    stock = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    is_top_deal = models.BooleanField('Top deal of the day', default=False)
    is_recommended = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:200]
            slug, n = base, 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f'{base}-{n}'
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:product', args=[self.slug])

    @property
    def has_price(self):
        return self.price is not None

    @property
    def can_buy(self):
        return self.has_price and self.stock > 0

    @property
    def on_sale(self):
        return bool(self.has_price and self.old_price and self.old_price > self.price)

    def description_points(self):
        """Description lines, for rendering as a bullet list."""
        return [line.strip(' •\t') for line in self.description.splitlines() if line.strip(' •\t')]

    @property
    def discount_percent(self):
        if not self.on_sale:
            return 0
        return int(round((self.old_price - self.price) / self.old_price * 100))

    @property
    def savings(self):
        return self.old_price - self.price if self.on_sale else 0

    @property
    def in_stock(self):
        return self.stock > 0

    def spec_list(self):
        rows = []
        for line in self.specifications.splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                rows.append((k.strip(), v.strip()))
        return rows


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='gallery', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/gallery/')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'Image for {self.product}'


class Banner(models.Model):
    POSITIONS = [
        ('hero_main', 'Hero – large slide'),
        ('hero_side', 'Hero – side tile'),
        ('promo', 'Promo strip (2 across)'),
        ('promo_alt', 'Second promo strip (2 across)'),
    ]
    THEMES = [
        ('orange', 'Orange'), ('blue', 'Blue'), ('green', 'Green'), ('red', 'Red'),
        ('emerald', 'Emerald'), ('yellow', 'Yellow'), ('navy', 'Navy'),
    ]
    position = models.CharField(max_length=20, choices=POSITIONS)
    eyebrow = models.CharField(max_length=60, blank=True, help_text='Small label shown above the title')
    title = models.CharField(max_length=120)
    subtitle = models.TextField(blank=True, help_text='Separate lines with a new line')
    button_text = models.CharField(max_length=40, default='View More')
    link = models.CharField(max_length=200, default='/shop/')
    icon = models.CharField(max_length=50, default='sun', help_text='Bootstrap icon used as artwork when no image')
    image = models.ImageField(upload_to='banners/', blank=True)
    theme = models.CharField(max_length=20, choices=THEMES, default='orange')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['position', 'order']

    def __str__(self):
        return f'{self.get_position_display()}: {self.title}'

    def subtitle_lines(self):
        return [line for line in self.subtitle.splitlines() if line.strip()]


class Order(models.Model):
    STATUS = [
        ('pending', 'Pending'), ('paid', 'Paid'), ('processing', 'Processing'),
        ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled'),
    ]
    PAYMENT = [('mpesa', 'M-PESA Paybill'), ('bank', 'Bank deposit / transfer'), ('cod', 'Cash on Delivery')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='orders',
                             on_delete=models.SET_NULL)
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    town = models.CharField(max_length=80)
    address = models.CharField(max_length=250)
    notes = models.TextField(blank=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT, default='mpesa')
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'Order #{self.pk}'

    @property
    def subtotal(self):
        return sum((i.line_total for i in self.items.all()), Decimal('0'))

    @property
    def total(self):
        return self.subtotal + self.delivery_fee


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.quantity} × {self.product_name}'

    @property
    def line_total(self):
        return self.price * self.quantity
