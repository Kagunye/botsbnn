from django.db import migrations

STEPS = [
    ('Site survey', 'We visit, measure loads and understand how the site is actually used.'),
    ('Honest design & quote', 'Sized to your needs — not an oversized sales quote. Clear itemised pricing.'),
    ('Installation', 'Neat, standards-compliant work by qualified technicians, on schedule.'),
    ('Test, label & hand over', 'Everything tested, labelled and documented, with aftercare support.'),
]
WHY = [
    ('home', 'shield-check', 'Safe & compliant', 'Work to Kenyan wiring standards.'),
    ('home', 'tags', 'Labelled & documented', 'As-built drawings on every job.'),
    ('home', 'box-seam', 'Genuine parts', 'Sourced from trusted brands.'),
    ('home', 'headset', 'Real aftercare', 'Servicing and fast call-outs.'),
    ('about', 'rulers', 'Engineered, not guessed', 'Load surveys and proper sizing — no oversized sales quotes.'),
    ('about', 'people', 'Qualified technicians', 'Safe, standards-compliant work on every site.'),
    ('about', 'headset', 'Aftercare that answers', 'Servicing plans and emergency call-outs when you need them.'),
]


def seed(apps, schema_editor):
    SiteSettings = apps.get_model('pages', 'SiteSettings')
    ProcessStep = apps.get_model('pages', 'ProcessStep')
    WhyChooseItem = apps.get_model('pages', 'WhyChooseItem')
    SiteSettings.objects.get_or_create(pk=1)
    if not ProcessStep.objects.exists():
        for i, (title, text) in enumerate(STEPS):
            ProcessStep.objects.create(title=title, text=text, order=i)
    if not WhyChooseItem.objects.exists():
        for i, (place, icon, title, text) in enumerate(WHY):
            WhyChooseItem.objects.create(place=place, icon=icon, title=title, text=text, order=i)


class Migration(migrations.Migration):
    dependencies = [('pages', '0002_processstep_sitesettings_whychooseitem')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
