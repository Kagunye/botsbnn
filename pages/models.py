from django.db import models


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=150)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'{self.name}: {self.subject}'


class SiteSettings(models.Model):
    """Single editable record holding company details and page text shown across the site."""
    # Company
    name = models.CharField('Company name', max_length=100, default='BNN Engineering')
    tagline = models.CharField(max_length=150, default='Power · Wiring · Security · Solar')
    email = models.EmailField(default='sales@bnnengineering.co.ke')
    phone1 = models.CharField('Phone 1', max_length=30, default='+254 700 000 000')
    phone2 = models.CharField('Phone 2', max_length=30, blank=True, default='+254 711 000 000')
    whatsapp = models.CharField('WhatsApp number', max_length=20, default='254700000000',
                                help_text='International format without + or spaces, e.g. 254712345678')
    address = models.CharField(max_length=200, default='Nairobi, Kenya')
    hours = models.CharField('Opening hours', max_length=100, default='Mon – Sat, 8:00am – 6:00pm')
    kra_pin = models.CharField('KRA PIN', max_length=20, blank=True, help_text='Shown on quotations')
    reg_no = models.CharField('Company reg. no.', max_length=40, blank=True, help_text='Shown on quotations')
    postal_address = models.CharField('Postal address', max_length=120, blank=True, help_text='e.g. P.O. Box 12345-00100, Nairobi')

    # Payment
    bank_name = models.CharField(max_length=100, default='Co-operative Bank of Kenya')
    account_name = models.CharField(max_length=100, default='BNN ENGINEERING LIMITED')
    account_no = models.CharField('Account number', max_length=40, default='01103490456001')
    paybill = models.CharField('M-PESA Paybill', max_length=20, default='400200')

    # Social
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.URLField('X / Twitter', blank=True)

    # Homepage
    hero_badge = models.CharField(max_length=100, default='Electrical engineering contractors · Nairobi')
    hero_title = models.CharField(max_length=120, default='Power, wiring & security —')
    hero_highlight = models.CharField('Hero highlighted words', max_length=80, default='engineered properly.')
    hero_text = models.TextField(default='Backup power, building wiring, switchgear, control panels, electric fencing, '
                                         'automatic gates and solar. Designed from real load data, installed to spec '
                                         'and documented for the next technician.')
    stat1_value = models.CharField(max_length=20, default='15+')
    stat1_label = models.CharField(max_length=40, default='Services')
    stat2_value = models.CharField(max_length=20, default='24/7')
    stat2_label = models.CharField(max_length=40, default='Emergency call-outs')
    stat3_value = models.CharField(max_length=20, default='100%')
    stat3_label = models.CharField(max_length=40, default='Tested & labelled')
    services_intro = models.CharField(max_length=250, default='From a single UPS to a full commercial switchroom — '
                                                              'one team for power, wiring, security and solar.')
    cta_title = models.CharField('Emergency banner title', max_length=120, default='Power out? Fence down? Gate stuck?')
    cta_text = models.CharField('Emergency banner text', max_length=200,
                                default='Our emergency team is a call away — any time.')
    show_shop_on_home = models.BooleanField('Show shop products on homepage', default=True)

    # Homepage company section
    company_kicker = models.CharField('Company section label', max_length=60, default='Why BNN Engineering')
    company_title = models.CharField('Company section headline', max_length=150,
                                     default='A trusted engineering partner for homes, businesses and industry')
    company_image = models.ImageField('Company section photo', upload_to='site/', blank=True,
                                      help_text='Leave blank to use one of your service photos')
    badge_value = models.CharField('Photo badge value', max_length=20, default='24/7')
    badge_label = models.CharField('Photo badge text', max_length=40, default='Emergency support')

    # About page & footer
    about_title = models.CharField(max_length=100, default='Who we are')
    about_body = models.TextField(default=(
        'BNN Engineering is a Nairobi-based electrical engineering contractor. We design, install and maintain '
        'backup power systems, building wiring, switchgear and control panels, electric fencing and automatic gates, '
        'and solar energy systems for homes, businesses and industry.\n\n'
        'Our approach is simple: size systems from real data, use genuine components, install neatly to standard, '
        'and label and document everything so the next technician knows exactly what is there. We also run an '
        'online shop supplying the equipment we trust and install.'))
    footer_about = models.TextField(default='Electrical engineering contractors for homes, businesses and industry — '
                                            'backup power, wiring, switchgear, control panels, security systems and '
                                            'solar, installed properly and documented for the next technician.')

    # Quotations
    default_tax_rate = models.DecimalField('Default VAT rate (%)', max_digits=5, decimal_places=2, default=16)
    quotation_validity_days = models.PositiveIntegerField('Quotation valid for (days)', default=30)
    quotation_terms = models.TextField(default=(
        '1. This quotation is valid for 30 days from the date of issue.\n'
        '2. 70% deposit required before commencement of work; balance on completion.\n'
        '3. Equipment remains the property of BNN Engineering until paid in full.\n'
        '4. Any additional work outside this scope will be quoted separately.'))

    class Meta:
        verbose_name = 'Site settings'
        verbose_name_plural = 'Site settings'

    def __str__(self):
        return 'Site settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    # Shapes used by templates (formerly settings.SHOP)
    @property
    def phones(self):
        return [p for p in (self.phone1, self.phone2) if p]

    @property
    def payment(self):
        return {'bank': self.bank_name, 'account_name': self.account_name,
                'account_no': self.account_no, 'paybill': self.paybill}

    def about_paragraphs(self):
        return [p.strip() for p in self.about_body.split('\n\n') if p.strip()]


class ProcessStep(models.Model):
    icon = models.CharField(max_length=50, default='check2-circle',
                            help_text='Bootstrap icon name (see icons.getbootstrap.com)')
    title = models.CharField(max_length=80)
    text = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'homepage process step'

    def __str__(self):
        return self.title


class WhyChooseItem(models.Model):
    PLACES = [('home', 'Homepage "why us" strip'), ('about', 'About page values')]
    place = models.CharField(max_length=10, choices=PLACES, default='home')
    icon = models.CharField(max_length=50, default='shield-check',
                            help_text='Bootstrap icon name (see icons.getbootstrap.com)')
    title = models.CharField(max_length=80)
    text = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['place', 'order']
        verbose_name = '"Why choose us" item'

    def __str__(self):
        return self.title


class Advert(models.Model):
    """Promotional poster shown in the homepage "Offers & updates" section (and handy for social media)."""
    title = models.CharField(max_length=120)
    image = models.ImageField(upload_to='adverts/', help_text='Portrait poster, ideally 1080 × 1350 px')
    link = models.CharField(max_length=200, blank=True, default='/quote/',
                            help_text='Where the advert goes when clicked, e.g. /quote/ or /services/solar-installations/')
    caption = models.CharField(max_length=200, blank=True, help_text='Short text shown under the advert (optional)')
    template_key = models.CharField(max_length=30, blank=True, editable=False,
                                    help_text='Set for adverts generated by "render_adverts"')
    is_active = models.BooleanField(default=True)
    show_on_home = models.BooleanField('Homepage', default=True, help_text='Homepage "Offers & updates" slider')
    show_in_shop_slider = models.BooleanField('Shop top slider', default=True)
    show_in_shop_promos = models.BooleanField('Shop promo rows', default=True)
    order = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created']

    def __str__(self):
        return self.title
