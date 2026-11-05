"""
Import a product catalogue export (products.json + images/ folder).

    python manage.py import_catalog path/to/folder [--replace-demo] [--update]

Each JSON item: {"title", "description", "image_files": ["images/x.jpg", ...]}
Category and brand are inferred from the title. Prices are not in the export,
so products are created as "Price on request" — set prices in /admin/.
"""
import hashlib
import json
import re
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image

from store.models import Brand, Category, Product, ProductImage

# child category -> (parent, icon)
CATEGORY_TREE = {
    'Monocrystalline Panels': ('Solar Panels', 'grid-3x3-gap-fill'),
    'Bifacial Panels': ('Solar Panels', 'grid-3x3-gap-fill'),
    'Polycrystalline Panels': ('Solar Panels', 'grid-3x3-gap-fill'),
    'Hybrid Inverters': ('Solar Inverters', 'lightning-charge'),
    'Off-Grid Inverters': ('Solar Inverters', 'lightning-charge'),
    'Grid-Tie Inverters': ('Solar Inverters', 'lightning-charge'),
    'Solar Pumping Inverters': ('Solar Inverters', 'lightning-charge'),
    'Lithium (LiFePO4) Batteries': ('Solar Batteries', 'battery-charging'),
    'Gel Batteries': ('Solar Batteries', 'battery-full'),
    'Power Stations': ('Solar Batteries', 'battery-charging'),
    'Battery Accessories': ('Solar Batteries', 'tools'),
    'Pressurised Heaters': ('Solar Water Heaters', 'thermometer-sun'),
    'Non-Pressurised Heaters': ('Solar Water Heaters', 'thermometer-sun'),
    'Heat Pump Water Heaters': ('Solar Water Heaters', 'thermometer-sun'),
    'Heater Spares': ('Solar Water Heaters', 'tools'),
    'Flood Lights': ('Solar Outdoor Lights', 'lightbulb'),
    'Street Lights': ('Solar Outdoor Lights', 'lightbulb'),
    'Submersible Pumps': ('Solar Water Pumps', 'droplet'),
    'Surface Pumps': ('Solar Water Pumps', 'droplet'),
    'Monitoring & Accessories': ('Accessories', 'plug'),
    'Cables & Connectors': ('Accessories', 'plug'),
}
PARENT_ICONS = {
    'Solar Panels': 'grid-3x3-gap-fill', 'Solar Inverters': 'lightning-charge', 'Solar Batteries': 'battery-charging',
    'Solar Water Heaters': 'thermometer-sun', 'Solar Outdoor Lights': 'lightbulb', 'Solar Water Pumps': 'droplet',
    'Accessories': 'plug',
}

# lowercase pattern -> brand name (matched at the earliest position in the title)
BRAND_PATTERNS = {
    r'seven ss stars': 'Seven SS Stars', r'lithium valley': 'Lithium Valley', r'freedom won': 'Freedom Won',
    r'jinko': 'Jinko Solar', r'longi': 'Longi Solar', r'\bja\b': 'JA Solar', r'\bdeye\b': 'Deye',
    r'sunsynk': 'Sunsynk', r'\bsolis\b': 'Solis', r'fronius': 'Fronius', r'\batess\b': 'ATESS', r'\btbb\b': 'TBB',
    r'lekkerix': 'Lekkerix', r'euroheat': 'EuroHeat', r'megasun': 'Megasun', r'solarstar': 'Solarstar',
    r'renepv': 'RenePV', r'amerisolar': 'Amerisolar', r'felicity': 'Felicity Solar', r'eternity': 'Eternity',
    r'growatt': 'Growatt', r'victron': 'Victron Energy', r'huawei': 'Huawei', r'trina': 'Trina Solar',
    r'canadian solar': 'Canadian Solar', r'dyness': 'Dyness', r'pylontech': 'Pylontech', r'must\b': 'Must',
    r'vestwoods': 'Vestwoods', r'megatank': 'Megatank', r'veichi': 'Veichi', r'\bhober\b': 'Hober',
}

MIN_GALLERY_BYTES = 3000  # skip tiny icon/spacer images


def clean(text):
    text = re.sub(r'(\d)�\s?([CF])\b', r'\1°\2', text)   # broken degree signs
    text = text.replace('�', ' ').replace(' ', ' ').replace('\xa0', ' ')
    return text


def clean_title(title):
    title = clean(title)
    title = re.sub(r'([A-Za-z])- ([A-Za-z])', r'\1\2', title)   # "INVERT- ER" -> "INVERTER"
    title = re.sub(r'(\d)- ([A-Z])', r'\1-\2', title)            # "100-3- D" -> "100-3-D"
    title = re.sub(r'\s+[-–]?\s*\(VAT INCL\.?\)', '', title, flags=re.I)
    title = re.sub(r'\s{2,}', ' ', title).strip(' -–')
    title = re.sub(r'\s+\|', ' |', title)
    return title


HEADING_LINES = {'feature', 'features', 'key features', 'description', 'product description', 'overview',
                 'details', 'specification', 'specifications', 'technical specifications', 'technical data',
                 'specs', 'parameter', 'parameters', 'value'}
SPEC_HEADERS = {'specification', 'specifications', 'technical specifications', 'technical data', 'specs',
                'parameter', 'parameters'}
# Sentences referring to the source shop are removed so they don't appear as claims on this site.
SOURCE_SHOP_RE = re.compile(r'solar\s?shop', re.I)


def strip_source_shop(line):
    sentences = re.split(r'(?<=[.!?])\s+', line)
    return ' '.join(s for s in sentences if not SOURCE_SHOP_RE.search(s)).strip()


def parse_description(desc):
    """Return (description, specifications) — flattened label/value spec tables become 'Key: Value' lines."""
    lines = []
    for raw in desc.splitlines():
        line = re.sub(r'\s{2,}', ' ', clean(raw)).strip()
        line = re.sub(r'^(?:[✔✓•]\s*|[-–]\s+)', '', line).strip()   # bullet markers, but keep "-20°C"
        line = strip_source_shop(line)
        if line:
            lines.append(line)

    body, specs, i = [], [], 0
    while i < len(lines):
        low = lines[i].lower().rstrip(':')
        nxt = lines[i + 1].lower().rstrip(':') if i + 1 < len(lines) else ''
        two_col_header = low in HEADING_LINES and nxt in HEADING_LINES   # e.g. "Feature" / "Description"
        if low in SPEC_HEADERS or two_col_header:
            i += 2 if two_col_header else 1
            # consume short label/value pairs
            while i + 1 < len(lines) and len(lines[i]) <= 45 and len(lines[i + 1]) <= 80 \
                    and lines[i].lower().rstrip(':') not in HEADING_LINES:
                specs.append(f'{lines[i].rstrip(":")}: {lines[i + 1]}')
                i += 2
            continue
        if low not in HEADING_LINES:
            body.append(lines[i])
        i += 1
    return '\n'.join(body), '\n'.join(specs)


def pick_summary(description):
    for line in description.splitlines():
        if len(line) >= 30:
            return line[:300]
    return (description.splitlines() or [''])[0][:300]


def classify(title):
    t = title.lower()
    if 'heat pump' in t:
        return 'Heat Pump Water Heaters'
    if 'water heat' in t:
        if re.search(r'non[\s-]?pressur', t):
            return 'Non-Pressurised Heaters'
        if 'pressur' in t or 'flat plate' in t:
            return 'Pressurised Heaters'
        return 'Non-Pressurised Heaters'
    if any(k in t for k in ('power station', 'solar generator', 'all-in-one')):
        return 'Power Stations'
    if 'inverter' in t:
        if 'pump' in t:
            return 'Solar Pumping Inverters'
        if 'battery inverter' in t:
            return 'Hybrid Inverters'
        if 'hybrid' in t:
            return 'Off-Grid Inverters' if re.search(r'off[\s-]?grid', t) else 'Hybrid Inverters'
        return 'Grid-Tie Inverters'
    if any(k in t for k in ('bracket', 'cleat', 'cluster controller', 'pdu')):
        return 'Battery Accessories'
    if 'dongle' in t or 'monitoring' in t:
        return 'Monitoring & Accessories'
    if 'gel' in t:
        return 'Gel Batteries'
    if 'battery' in t or 'batteries' in t or 'kwh' in t:
        return 'Lithium (LiFePO4) Batteries'
    if 'panel' in t or 'watts' in t or re.search(r'\d\s*w\b', t):
        if 'bifacial' in t and 'monofacial' not in t:
            return 'Bifacial Panels'
        if 'polycrystalline' in t or re.search(r'\d+p\b', t):
            return 'Polycrystalline Panels'
        return 'Monocrystalline Panels'
    if 'pump' in t:
        return 'Submersible Pumps' if ('submersible' in t or 'borehole' in t) else 'Surface Pumps'
    if 'light' in t:
        return 'Street Lights' if 'street' in t else 'Flood Lights'
    if 'cable' in t or 'connector' in t or 'mc4' in t:
        return 'Cables & Connectors'
    return 'Monitoring & Accessories'


def detect_brand(title):
    t = title.lower()
    best = None
    for pattern, name in BRAND_PATTERNS.items():
        m = re.search(pattern, t)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), name)
    return best[1] if best else None


def file_hash(path):
    return hashlib.md5(path.read_bytes()).hexdigest()


def valid_image(path):
    try:
        with Image.open(path) as im:
            im.verify()
        return True
    except Exception:
        return False


class Command(BaseCommand):
    help = 'Import products, descriptions and images from a catalogue export folder (products.json + images/).'

    def add_arguments(self, parser):
        parser.add_argument('folder', help='Folder containing products.json and images/')
        parser.add_argument('--replace-demo', action='store_true',
                            help='Delete existing products that have no image (the seed_shop demo items)')
        parser.add_argument('--update', action='store_true',
                            help='Refresh description/images of products that already exist (matched by name)')
        parser.add_argument('--featured', type=int, default=12,
                            help='How many products to flag as Top Deals / Recommended (default 12 each)')

    def handle(self, folder, replace_demo, update, featured, **opts):
        root = Path(folder)
        data_file = root / 'products.json'
        if not data_file.exists():
            raise CommandError(f'{data_file} not found')
        items = json.loads(data_file.read_text(encoding='utf-8'))

        with transaction.atomic():
            if replace_demo:
                n, _ = Product.objects.filter(image='').delete()
                self.stdout.write(f'Removed {n} demo product rows without images.')

            cats = self._ensure_categories()
            created = updated = skipped = gallery_count = 0
            per_category = {}

            for item in items:
                name = clean_title(item['title'])[:200]
                description, specifications = parse_description(item.get('description', ''))
                files = [root / f for f in item.get('image_files', [])]
                files = [f for f in files if f.exists() and valid_image(f)]

                product = Product.objects.filter(name=name).first()
                if product and not update:
                    skipped += 1
                    continue

                cat_name = classify(name)
                brand_name = detect_brand(name)
                brand = None
                if brand_name:
                    brand, _ = Brand.objects.get_or_create(name=brand_name)

                is_new = product is None
                if is_new:
                    product = Product(name=name, price=None, stock=10)
                product.category = cats[cat_name]
                product.brand = brand
                product.description = description
                product.specifications = specifications
                product.short_description = pick_summary(description)
                product.save()

                if files:
                    main = files[0]
                    if product.image:
                        product.image.delete(save=False)
                    with main.open('rb') as fh:
                        product.image.save(main.name, File(fh), save=True)
                    for g in product.gallery.all():
                        g.image.delete(save=False)
                    product.gallery.all().delete()
                    seen = {file_hash(main)}
                    for i, extra in enumerate(files[1:]):
                        h = file_hash(extra)
                        if extra.stat().st_size < MIN_GALLERY_BYTES or h in seen:
                            continue
                        seen.add(h)
                        with extra.open('rb') as fh:
                            ProductImage(product=product, order=i).image.save(extra.name, File(fh), save=True)
                        gallery_count += 1

                per_category.setdefault(cat_name, []).append(product)
                created += is_new
                updated += not is_new

            self._flag_featured(per_category, featured)

        self.stdout.write(self.style.SUCCESS(
            f'Imported {created} new, updated {updated}, skipped {skipped} existing; '
            f'{gallery_count} extra gallery images.'))
        for cat, prods in sorted(per_category.items()):
            self.stdout.write(f'  {cat}: {len(prods)}')

    def _ensure_categories(self):
        parents = {}
        for i, (name, icon) in enumerate(PARENT_ICONS.items()):
            parents[name], _ = Category.objects.get_or_create(
                name=name, parent=None, defaults={'icon': icon, 'order': i})
        cats = {}
        for child, (parent, icon) in CATEGORY_TREE.items():
            cats[child], _ = Category.objects.get_or_create(
                name=child, parent=parents[parent], defaults={'icon': icon})
        return cats

    def _flag_featured(self, per_category, count):
        """Pick a varied set (round-robin across categories) for the homepage rows."""
        if not count:
            return
        queues = [list(v) for v in per_category.values()]
        picks = []
        while any(queues) and len(picks) < count * 2:
            for q in queues:
                if q and len(picks) < count * 2:
                    picks.append(q.pop(0))
        for i, p in enumerate(picks):
            Product.objects.filter(pk=p.pk).update(is_top_deal=(i % 2 == 0), is_recommended=(i % 2 == 1))
