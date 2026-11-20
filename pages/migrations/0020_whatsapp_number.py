from django.db import migrations, models

WHATSAPP = '254184786662'


def set_whatsapp(apps, schema_editor):
    apps.get_model('pages', 'SiteSettings').objects.update(whatsapp=WHATSAPP)


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0019_phone_numbers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitesettings',
            name='whatsapp',
            field=models.CharField(default=WHATSAPP, help_text='International format without + or spaces, e.g. 254712345678', max_length=20, verbose_name='WhatsApp number'),
        ),
        migrations.RunPython(set_whatsapp, migrations.RunPython.noop),
    ]
