from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=50, default='lightning-charge', help_text='Bootstrap icon name')
    tagline = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to='service-categories/', blank=True,
                              help_text='Photo for the homepage "What we do" tile. '
                                        'Leave blank to use a photo from one of its services.')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'service categories'

    @property
    def display_image(self):
        if self.image:
            return self.image
        for s in self.services.all():
            if s.image and s.is_active:
                return s.image
        return None

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, related_name='services', on_delete=models.PROTECT)
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    summary = models.CharField(max_length=250, help_text='One-line pitch shown on cards')
    description = models.TextField(blank=True, help_text='Intro paragraph for the service page')
    included = models.TextField(blank=True, help_text="What's included — one item per line")
    icon = models.CharField(max_length=50, default='lightning-charge', help_text='Bootstrap icon name')
    image = models.ImageField(upload_to='services/', blank=True)
    is_featured = models.BooleanField(default=False, help_text='Show in the homepage highlight row')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['category__order', 'order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('services:detail', args=[self.slug])

    @property
    def card_image(self):
        """Own photo, or the category's photo as a fallback."""
        return self.image or self.category.display_image

    def get_quote_url(self):
        return f"{reverse('services:quote')}?service={self.slug}"

    def included_list(self):
        return [line.strip(' •-') for line in self.included.splitlines() if line.strip(' •-')]


class QuoteRequest(models.Model):
    STATUS = [('new', 'New'), ('contacted', 'Contacted'), ('quoted', 'Quoted'), ('won', 'Won'), ('lost', 'Lost')]
    service = models.ForeignKey(Service, null=True, blank=True, related_name='quote_requests', on_delete=models.SET_NULL)
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    location = models.CharField('Site location', max_length=150)
    message = models.TextField('Describe the job', blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='new')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'{self.name} – {self.service or "General enquiry"}'


class Project(models.Model):
    title = models.CharField(max_length=150, help_text='e.g. "10kW hybrid solar system – Karen residence"')
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    service = models.ForeignKey(Service, null=True, blank=True, related_name='projects', on_delete=models.SET_NULL,
                                help_text='Which service this project shows off (optional)')
    location = models.CharField(max_length=120, blank=True, help_text='e.g. Westlands, Nairobi')
    client = models.CharField(max_length=120, blank=True, help_text='Leave blank to keep the client private')
    completed_on = models.DateField(null=True, blank=True)
    summary = models.CharField(max_length=250, help_text='One line shown on the project card')
    description = models.TextField(blank=True, help_text='What was done – shown on the project page')
    cover_image = models.ImageField(upload_to='projects/', help_text='Main photo shown on the homepage card')
    show_on_home = models.BooleanField('Show on homepage', default=True)
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text='Lower numbers show first')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-completed_on', '-created']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:150] or 'project'
            slug, n = base, 1
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f'{base}-{n}'
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('services:project', args=[self.slug])


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='projects/gallery/')
    caption = models.CharField(max_length=150, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.caption or f'Photo for {self.project}'
