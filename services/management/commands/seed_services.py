from django.core.management.base import BaseCommand
from django.db import transaction

from services.models import Service, ServiceCategory

# (category, icon, tagline, [(name, icon, summary, description, included, featured), ...])
DATA = [
    ('Power & Backup', 'lightning-charge', 'Keep the lights, servers and machines running through every outage.', [
        ('Backup Power', 'lightning-charge',
         'Automatic backup that takes over the moment KPLC goes off.',
         'We design backup systems around what you actually need to keep running — from a few lights and a '
         'fridge to an entire office — and install them with automatic changeover so nobody has to flip a switch.',
         'Load survey and outage-pattern assessment\nInverter, battery or generator-based options\n'
         'Automatic changeover switching\nInstallation, testing and handover', True),
        ('Battery & Power Backup Systems', 'battery-charging',
         'Battery banks sized to your outage pattern, not an oversized sales quote.',
         'Lithium (LiFePO4) and gel battery banks matched to your load and how long your outages really last. '
         'We size honestly, install safely and set up monitoring so you can see your battery health.',
         'Battery sizing from real load data\nLithium and gel battery options\nRacking, protection and cabling\n'
         'Remote monitoring setup', True),
        ('UPS Installations', 'power',
         'Clean, uninterrupted power for servers, POS systems and sensitive equipment.',
         'Online and line-interactive UPS systems for offices, data rooms, clinics and retail — installed with '
         'proper protection, bypass and battery runtime matched to your equipment.',
         'UPS sizing and runtime calculation\nDedicated UPS circuits and distribution\nMaintenance bypass installation\n'
         'Battery replacement and servicing'),
        ('Voltage Stabilisers', 'activity',
         'Protect appliances and machinery from low, high and fluctuating voltage.',
         'Single and three-phase automatic voltage stabilisers for homes, workshops and industrial equipment — '
         'ideal where voltage drops or surges damage motors, compressors and electronics.',
         'Voltage logging and assessment\nSingle and three-phase stabilisers\nSurge protection\nInstallation and commissioning'),
        ('Generator Servicing & Installations', 'gear-wide-connected',
         'Supply, installation, ATS changeover and scheduled servicing for standby generators.',
         'From new generator installations with automatic transfer switches to routine servicing and repairs, '
         'we keep your standby power ready for when you need it.',
         'Generator sizing and supply\nATS / changeover panel installation\nScheduled servicing and oil changes\n'
         'Fault finding and repairs', True),
    ]),
    ('Wiring & Infrastructure', 'diagram-3', 'Safe, tidy, compliant electrical and data installations.', [
        ('Electrical Installations', 'lightbulb',
         'Complete electrical installations for homes, offices, shops and industrial sites.',
         'Distribution boards, lighting, power points, earthing and three-phase supplies — installed to '
         'standard and tested before handover.',
         'Distribution boards and sub-mains\nLighting and power circuits\nEarthing and lightning protection\n'
         'Testing and certification'),
        ('Building Wiring', 'plug',
         'First-fix to final-fix wiring for new construction and full rewires.',
         'We work alongside contractors from conduit first-fix through to final fittings, and carry out full '
         'rewires of older buildings with minimal disruption.',
         'Conduit and trunking first-fix\nCabling and final-fix fittings\nFull and partial rewires\nInspection and test reports', True),
        ('Structured Network Cabling', 'ethernet',
         'Cat6 and fibre runs, patched, labelled and tested.',
         'Office and building data networks installed neatly — every point labelled, patched and tested so your '
         'IT team knows exactly what goes where.',
         'Cat6 / Cat6A and fibre installation\nCabinets, patch panels and trunking\nLabelling and documentation\n'
         'Cable testing and certification'),
    ]),
    ('Industrial & Commercial', 'cpu', 'Panels and switchgear built to spec and documented.', [
        ('Control Panel Design & Fabrication', 'motherboard',
         'Panels built and wired to schematic, labelled for the next technician.',
         'Motor control, pump control, changeover and automation panels designed, fabricated and wired in-house, '
         'with full labelling and as-built drawings.',
         'Panel design and schematics\nMotor, pump and changeover panels\nPLC and automation wiring\n'
         'Labelling and as-built documentation', True),
        ('Industrial & Commercial Switchgear', 'toggles',
         'LV switchgear supply, installation and changeover, built to spec.',
         'Low-voltage main switchboards, distribution panels and changeover systems for commercial and industrial '
         'buildings — supplied, installed and commissioned.',
         'LV switchboard supply and installation\nBreakers, busbars and metering\nChangeover systems\nCommissioning and testing'),
    ]),
    ('Access & Security', 'shield-lock', 'Perimeter protection and access control, installed to spec.', [
        ('Electric Security Fencing', 'shield-check',
         'Perimeter fencing wired to an energiser and alarm, installed to spec.',
         'Wall-top and free-standing electric fences with energisers, alarms and proper earthing — plus repairs '
         'and upgrades to existing fences.',
         'Wall-top and free-standing fences\nEnergiser, siren and alarm integration\nEarthing and warning signage\n'
         'Fence repairs and upgrades', True),
        ('Electric & Security Gates', 'door-closed',
         'Motorised sliding and swing gates for homes, estates and businesses.',
         'Supply and installation of gate motors and accessories for sliding and swing gates, including safety '
         'beams and remote controls.',
         'Sliding and swing gate motors\nRemote controls and keypads\nSafety beams and limit switches\nBattery backup for gate motors'),
        ('Automatic Gate Systems', 'door-open',
         'Fully automated gates with access control, intercoms and backup power.',
         'Complete automatic gate solutions — motors, access control, intercoms and solar or battery backup so '
         'your gate works even during power cuts.',
         'Access control (cards, tags, keypads)\nVideo and audio intercoms\nSolar and battery backup\nServicing and repairs'),
        ('Emergency Electrical & Security Call-outs', 'alarm',
         'Fast response when power, fences or gates fail.',
         'Power failure, tripping breakers, a dead electric fence or a stuck gate — call us and a technician will '
         'be dispatched to diagnose and fix the problem.',
         'Fault finding and repairs\nElectric fence and gate faults\nPower restoration\nNairobi and environs'),
    ]),
    ('Solar & Clean Energy', 'sun', 'Cut your power bill with properly engineered solar.', [
        ('Solar Installations', 'sun',
         'Grid-tie, hybrid and off-grid solar systems designed and installed by engineers.',
         'Residential, commercial and industrial solar PV systems — designed from your consumption data, installed '
         'with quality components from our shop and commissioned with monitoring.',
         'Site survey and energy audit\nSystem design and sizing\nPanels, inverters and batteries supplied\n'
         'Installation, commissioning and monitoring', True),
    ]),
]


class Command(BaseCommand):
    help = 'Create the BNN Engineering service categories and services.'

    @transaction.atomic
    def handle(self, *args, **opts):
        created = 0
        for ci, (cname, cicon, tagline, services) in enumerate(DATA):
            cat, _ = ServiceCategory.objects.update_or_create(
                name=cname, defaults={'icon': cicon, 'tagline': tagline, 'order': ci})
            for si, row in enumerate(services):
                name, icon, summary, description, included = row[:5]
                featured = row[5] if len(row) > 5 else False
                _, was_created = Service.objects.update_or_create(name=name, defaults=dict(
                    category=cat, icon=icon, summary=summary, description=description,
                    included=included, is_featured=featured, order=si))
                created += was_created
        self.stdout.write(self.style.SUCCESS(
            f'{ServiceCategory.objects.count()} categories, {Service.objects.count()} services ({created} new).'))
