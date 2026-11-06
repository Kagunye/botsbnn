from django.db import migrations

INDUSTRIES = [
    ('house-door', 'Homes & estates', 'Backup power, solar, wiring, fencing and gates for residences.'),
    ('building', 'Offices & commercial', 'Reliable power and structured cabling for workplaces.'),
    ('hospital', 'Hospitals & clinics', 'UPS and generator backup for critical equipment.'),
    ('mortarboard', 'Schools & institutions', 'Solar, security and electrical installations.'),
    ('tree', 'Farms & agribusiness', 'Solar pumping and off-grid power for rural sites.'),
    ('gear-wide-connected', 'Manufacturing & industry', 'Switchgear, control panels and standby power.'),
    ('cup-hot', 'Hotels & hospitality', 'Water heating, backup power and access control.'),
    ('router', 'Telecom & data', 'Clean, uninterrupted power for networks and servers.'),
]

FAQS = [
    ('Do you offer a free site survey?',
     'Yes. Before quoting we visit the site, assess your loads and understand how the space is used, so the system '
     'is sized to your actual needs.'),
    ('How does the quotation work?',
     'After the survey you receive a clear, itemised quotation listing equipment, labour and any delivery, with VAT '
     'shown separately. Nothing starts until you approve it.'),
    ('Which areas do you cover?',
     'We are based in Nairobi and carry out installations for homes, businesses and institutions across Kenya. '
     'Contact us with your location and we will confirm.'),
    ('Do you handle emergencies?',
     'Yes — we offer emergency call-outs for power failures, tripping breakers, electric fence faults and stuck gates.'),
    ('Do you supply equipment as well as install it?',
     'Yes. We supply genuine equipment from trusted brands — solar panels, inverters, batteries, water heaters and '
     'more — and our technicians install, test and hand over the complete system.'),
    ('How can I pay?',
     'You can pay by M-PESA Paybill or by bank deposit/transfer to our company account. Full details are on the '
     'How to Pay page and on every quotation and invoice.'),
    ('Is the equipment covered by warranty?',
     'Equipment carries the manufacturer\'s warranty, and we provide after-sales support and servicing for the '
     'systems we install.'),
]


def seed(apps, schema_editor):
    Industry = apps.get_model('pages', 'Industry')
    FAQ = apps.get_model('pages', 'FAQ')
    if not Industry.objects.exists():
        for i, (icon, title, text) in enumerate(INDUSTRIES):
            Industry.objects.create(icon=icon, title=title, text=text, order=i)
    if not FAQ.objects.exists():
        for i, (q, a) in enumerate(FAQS):
            FAQ.objects.create(question=q, answer=a, order=i)


class Migration(migrations.Migration):
    dependencies = [('pages', '0009_industries_testimonials_faqs')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
