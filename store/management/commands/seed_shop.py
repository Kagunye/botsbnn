from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from store.models import Banner, Brand, Category, Product

CATEGORIES = [
    ('Solar Panels', 'grid-3x3-gap-fill', ['Monocrystalline Panels', 'Bifacial Panels', 'Polycrystalline Panels']),
    ('Solar Inverters', 'lightning-charge', ['Hybrid Inverters', 'Off-Grid Inverters', 'Solar Pumping Inverters']),
    ('Solar Batteries', 'battery-charging', ['Lithium (LiFePO4) Batteries', 'Gel Batteries']),
    ('Solar Water Heaters', 'thermometer-sun', ['Pressurised Heaters', 'Non-Pressurised Heaters', 'Heater Spares']),
    ('Solar Outdoor Lights', 'lightbulb', ['Flood Lights', 'Street Lights']),
    ('Solar Water Pumps', 'droplet', ['Submersible Pumps', 'Surface Pumps']),
    ('Accessories', 'plug', ['Cables & Connectors', 'Mounting Structures']),
]

CHILD_ICONS = {
    'Heater Spares': 'tools', 'Cables & Connectors': 'plug', 'Mounting Structures': 'nut',
    'Solar Pumping Inverters': 'lightning-charge', 'Gel Batteries': 'battery-full',
}

BRANDS = [
    ('Eastman', '#e2731b'), ('Ritar', '#c8102e'), ('JA Solar', '#00529b'), ('Jinko Solar', '#00a651'),
    ('Longi Solar', '#d6001c'), ('Trina Solar', '#0066b3'), ('Canadian Solar', '#e31837'), ('Chromagen', '#d71920'),
    ('Dyness', '#3aa935'), ('EcoFlow', '#222222'), ('Fronius', '#e2001a'), ('Haier', '#005aab'),
    ('Sollatek', '#e5531a'), ('Vestwoods', '#333333'), ('Bluetti', '#0070c0'), ('BYD', '#c8102e'),
    ('Deye', '#0067b1'), ('Felicity Solar', '#f39200'), ('Goodwe', '#d6001c'), ('Growatt', '#69b42e'),
    ('Kastom Solar', '#0b7d3e'), ('Sunsynk', '#f6a800'), ('Luminous', '#f49c00'), ('Megatank', '#0a3d91'),
    ('Must', '#e30613'), ('Solar Light', '#004b87'), ('SolaX Power', '#1e1e1e'), ('Solis', '#00539f'),
    ('SRNE Solar', '#d6001c'), ('Sungrow', '#f39800'), ('Suntree', '#e9711c'), ('Victron Energy', '#0055a5'),
    ('Weco', '#e30613'), ('Lithium Valley', '#0078c1'), ('Huawei', '#cf0a2c'), ('Veichi', '#0067b1'),
]

# name, category, brand, price, old_price, top_deal, recommended, short description, specs
PRODUCTS = [
    ('Suntree Solar PV Cable 6.0mm² (per metre)', 'Cables & Connectors', 'Suntree', 180, None, True, False,
     'Double-insulated, UV-resistant tinned copper DC cable for PV arrays.', 'Cross section: 6.0mm²\nRated voltage: 1500V DC\nConductor: Tinned copper'),
    ('Suntree MC4 Connectors | Standard Straight', 'Cables & Connectors', 'Suntree', 200, None, True, False,
     'IP68 MC4 male/female connector pair for safe panel interconnection.', 'Rated current: 30A\nRated voltage: 1500V DC\nProtection: IP68'),
    ('Jinko 625 Watts Monocrystalline Solar Panel | Bifacial', 'Bifacial Panels', 'Jinko Solar', 13750, 17300, True, False,
     'Tiger Neo N-type bifacial module with up to 30% rear-side gain.', 'Max power: 625W\nCell type: N-type TOPCon\nEfficiency: 22.9%\nWarranty: 30 years linear'),
    ('L-Feet (Long) with Roofing Bolt & Rubber for Aluminium Solar Structure', 'Mounting Structures', None, 350, None, True, False,
     'Corrosion-resistant L-foot for mounting rails on iron-sheet roofs.', 'Material: Anodised aluminium\nIncludes: Bolt, EPDM rubber'),
    ('Jinko 615 Watts Monocrystalline Solar Panel | Monofacial', 'Monocrystalline Panels', 'Jinko Solar', 13530, 16900, True, False,
     'High-efficiency N-type monofacial panel for residential and commercial roofs.', 'Max power: 615W\nEfficiency: 22.5%\nWarranty: 25 years product'),
    ('Suntree MC4 Y 2 Branch Connector Pair (Short)', 'Cables & Connectors', 'Suntree', 650, 750, True, False,
     'Parallel-connect two strings with this MC4 Y-branch pair.', 'Rated current: 30A\nProtection: IP68'),
    ('WeCo 5K3-XP 5.3 KWh 51.2V Lithium Battery | Dual Voltage Design', 'Lithium (LiFePO4) Batteries', 'Weco', 185000, 210000, True, True,
     'Stackable LiFePO4 battery with 6,000+ cycles and smart BMS.', 'Capacity: 5.3kWh\nVoltage: 51.2V / 25.6V\nCycle life: 6000+\nWarranty: 10 years'),
    ('20W Solar Tube Light', 'Flood Lights', 'Solar Light', 2250, None, True, False,
     'All-in-one solar tube light with remote and dusk-to-dawn sensor.', 'Power: 20W\nBattery: Lithium\nRuntime: 10–12 hrs'),
    ('Jinko Solar 550 Watts Monocrystalline Solar Panel', 'Monocrystalline Panels', 'Jinko Solar', 11900, 13500, True, False,
     '144 half-cut cell module, a proven workhorse for grid-tie and hybrid systems.', 'Max power: 550W\nCells: 144 half-cut\nEfficiency: 21.3%'),
    ('JA Solar 565 Watts Monocrystalline Solar Panel | Monofacial', 'Monocrystalline Panels', 'JA Solar', 12400, 14200, True, False,
     'JA DeepBlue module with excellent low-light performance.', 'Max power: 565W\nEfficiency: 21.9%'),
    ('Longi Solar 350 Watts Monocrystalline Solar Panel | Bifacial', 'Bifacial Panels', 'Longi Solar', 8200, 9500, True, False,
     'Compact bifacial Hi-MO panel ideal for small roofs and carports.', 'Max power: 350W\nType: Bifacial'),
    ('Solar End Clamp (30mm) for Aluminium Mounting Structure', 'Mounting Structures', None, 150, None, True, False,
     'Secures the outer edge of 30mm framed panels to mounting rails.', 'Frame height: 30mm\nMaterial: Aluminium'),
    ('Solarmax 10W Polycrystalline Solar Panel', 'Polycrystalline Panels', None, 650, None, False, True,
     'Small panel for phone charging, lighting kits and electric fences.', 'Max power: 10W\nVoltage: 18V'),
    ('Solar Heater Element 1.5Kw 40mm with Thermostat | Screw Type 1.25"', 'Heater Spares', None, 3500, None, False, True,
     'Backup electric element for cloudy days.', 'Power: 1.5kW\nThread: 1.25"'),
    ('SR609C 3Kw Solar Water Heater Controller', 'Heater Spares', None, 8900, 9900, False, True,
     'Intelligent controller with temperature display and timed backup heating.', 'Element output: 3kW\nDisplay: LCD'),
    ('Magnesium Anode Rod for Non-Pressurised Solar Water Heaters', 'Heater Spares', None, 900, None, False, True,
     'Protects the inner tank from corrosion — replace every 1–2 years.', 'Material: Magnesium'),
    ('Thermal Glue for Heat Pipe Systems', 'Heater Spares', None, 450, None, False, True,
     'Improves heat transfer between heat pipes and manifold.', ''),
    ('JA 575W Bifacial Solar Panel', 'Bifacial Panels', 'JA Solar', 10200, 12900, False, True,
     'N-type bifacial panel with dual-glass durability.', 'Max power: 575W\nType: Bifacial dual-glass'),
    ('Growatt SPF 5000 ES 5kW Off-Grid Inverter', 'Off-Grid Inverters', 'Growatt', 78000, 85000, False, True,
     'Off-grid inverter with built-in 100A MPPT and Wi-Fi monitoring.', 'Rated power: 5kW\nBattery: 48V\nMPPT: 100A'),
    ('Deye 8kW Hybrid Inverter SUN-8K-SG04LP3', 'Hybrid Inverters', 'Deye', 245000, 268000, False, True,
     'Three-phase hybrid inverter with seamless grid-battery switching.', 'Rated power: 8kW\nPhase: 3-phase\nMPPT trackers: 2'),
    ('Sunsynk 5kW Hybrid Inverter', 'Hybrid Inverters', 'Sunsynk', 165000, None, False, False,
     'Single-phase hybrid inverter with UPS-grade switching under 4ms.', 'Rated power: 5kW\nSwitch time: <4ms'),
    ('Must 3kW Solar Pumping Inverter', 'Solar Pumping Inverters', 'Must', 42000, 46000, False, False,
     'Run AC pumps directly from solar panels — no batteries needed.', 'Rated power: 3kW\nInput: PV / AC'),
    ('Dyness B4850 2.4kWh LiFePO4 Battery', 'Lithium (LiFePO4) Batteries', 'Dyness', 98000, None, False, False,
     'Rack-mount 48V lithium battery compatible with most hybrid inverters.', 'Capacity: 2.4kWh\nVoltage: 48V'),
    ('Ritar 200Ah 12V Gel Battery', 'Gel Batteries', 'Ritar', 38500, 41000, False, False,
     'Deep-cycle gel battery for off-grid and backup systems.', 'Capacity: 200Ah\nVoltage: 12V'),
    ('Chromagen 200L Pressurised Solar Water Heater', 'Pressurised Heaters', 'Chromagen', 165000, None, False, True,
     'Flat-plate pressurised system for strong showers and multi-storey homes.', 'Capacity: 200L\nType: Flat plate'),
    ('Megatank 150L Non-Pressurised Solar Water Heater', 'Non-Pressurised Heaters', 'Megatank', 62000, 68000, False, False,
     'Evacuated-tube heater, a cost-effective hot water solution.', 'Capacity: 150L\nTubes: 15'),
    ('100W Solar Flood Light with Remote', 'Flood Lights', 'Solar Light', 4800, 5500, False, False,
     'Bright IP65 flood light for compounds and parking.', 'Power: 100W\nProtection: IP65'),
    ('60W All-in-One Solar Street Light', 'Street Lights', 'Sollatek', 12500, None, False, False,
     'Integrated panel, battery and motion sensor in one rugged unit.', 'Power: 60W\nSensor: PIR motion'),
    ('1.1kW Solar Submersible Borehole Pump', 'Submersible Pumps', 'Kastom Solar', 115000, 125000, False, False,
     'Brushless DC submersible pump for boreholes up to 120m.', 'Power: 1.1kW\nMax head: 120m'),
    ('Solar Surface Pump 750W', 'Surface Pumps', 'Felicity Solar', 38000, None, False, False,
     'DC surface pump for irrigation from rivers, dams and tanks.', 'Power: 750W\nMax flow: 6m³/h'),
]

BANNERS = [
    dict(position='hero_main', title='Never Run Out of Power Again',
         subtitle='Hybrid inverters + LiFePO4 batteries.\nSeamless solar-battery-grid switching.\nIn stock now.',
         button_text='Shop Inverters & Batteries', link='/shop/category/solar-inverters/', icon='battery-charging', theme='orange'),
    dict(position='hero_main', title='Cut Your Power Bill by up to 80%',
         subtitle='Tier-1 solar panels from Jinko, JA & Longi.\nFree delivery within Nairobi.',
         button_text='Shop Solar Panels', link='/shop/category/solar-panels/', icon='grid-3x3-gap-fill', theme='orange', order=1),
    dict(position='hero_side', title='Solar Pumping Inverters', subtitle='Water your way, powered by the sun',
         link='/shop/category/solar-pumping-inverters/', icon='droplet-half', theme='blue'),
    dict(position='hero_side', title='Solar Panels', subtitle='Cut your electricity bills starting today',
         link='/shop/category/solar-panels/', icon='grid-3x3-gap-fill', theme='green', order=1),
    dict(position='promo', title='Solar <b>Water Heaters</b>', subtitle='Hot water every day, powered entirely by the sun',
         link='/shop/category/solar-water-heaters/', icon='thermometer-sun', theme='red'),
    dict(position='promo', title='Lithium <b>Batteries-LiFePO4</b>', subtitle='Store your solar energy and use it anytime you need',
         link='/shop/category/solar-batteries/', icon='battery-full', theme='emerald', order=1),
    dict(position='promo_alt', eyebrow='Solar Flash Sales', title='Blazing flash deals gone before the sun sets',
         link='/shop/products/?sale=1', icon='lightning-charge-fill', theme='yellow'),
    dict(position='promo_alt', eyebrow='Black Friday Deals', title='Harvest massive savings this Black Friday',
         link='/shop/products/?sale=1', icon='sun', theme='navy', order=1),
]


class Command(BaseCommand):
    help = 'Populate the shop with demo categories, brands, products and banners.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Delete existing catalogue data first')

    @transaction.atomic
    def handle(self, *args, reset=False, **opts):
        if reset:
            Product.objects.all().delete()
            Banner.objects.all().delete()
            Category.objects.all().delete()
            Brand.objects.all().delete()

        cats = {}
        for i, (name, icon, children) in enumerate(CATEGORIES):
            parent, _ = Category.objects.get_or_create(name=name, parent=None, defaults={'icon': icon, 'order': i})
            cats[name] = parent
            for j, child in enumerate(children):
                c, _ = Category.objects.get_or_create(
                    name=child, parent=parent, defaults={'icon': CHILD_ICONS.get(child, icon), 'order': j})
                cats[child] = c

        brands = {}
        for name, color in BRANDS:
            brands[name], _ = Brand.objects.get_or_create(name=name, defaults={'color': color})

        created = 0
        for (name, cat, brand, price, old, deal, rec, short, specs) in PRODUCTS:
            _, was_created = Product.objects.get_or_create(name=name, defaults=dict(
                category=cats[cat], brand=brands.get(brand), price=Decimal(price),
                old_price=Decimal(old) if old else None, is_top_deal=deal, is_recommended=rec,
                short_description=short, specifications=specs,
                description=f'{short}\n\nSupplied with full manufacturer warranty. Professional installation '
                            f'available across Kenya — talk to our engineers for sizing advice.',
                stock=25,
            ))
            created += was_created

        if not Banner.objects.exists():
            for b in BANNERS:
                Banner.objects.create(**b)

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(cats)} categories, {len(brands)} brands, {created} new products, '
            f'{Banner.objects.count()} banners.'))
