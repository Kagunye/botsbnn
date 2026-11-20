from django.db import migrations, models

PHONE1 = '+254 184 786 662'
PHONE2 = '+254 184 786 663'


def set_phones(apps, schema_editor):
    SiteSettings = apps.get_model('pages', 'SiteSettings')
    SiteSettings.objects.update(phone1=PHONE1, phone2=PHONE2)


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0018_default_email_info'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitesettings',
            name='phone1',
            field=models.CharField(default=PHONE1, max_length=30, verbose_name='Phone 1'),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='phone2',
            field=models.CharField(blank=True, default=PHONE2, max_length=30, verbose_name='Phone 2'),
        ),
        migrations.RunPython(set_phones, migrations.RunPython.noop),
    ]
