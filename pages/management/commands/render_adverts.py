"""Render the BNN-branded advert posters (templates/adverts/poster_N.html) to 1080x1350 PNGs.

    python manage.py render_adverts

Uses the company details in Admin -> Site settings, so re-run after changing phone numbers or email.
Needs Microsoft Edge or Google Chrome installed (used headless to take the picture).
"""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string

from pages.models import Advert, SiteSettings

BROWSERS = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
]

# key: (template, photo under MEDIA_ROOT, title, link, caption)
POSTERS = [
    ('backup', 'adverts/poster_1.html', 'services/power-backup.jpg', 'Power that keeps you running',
     '/services/battery-power-backup-systems/', 'Hybrid inverters, UPS & lithium batteries'),
    ('generator', 'adverts/poster_2.html', 'services/generator-servicing.jpg', 'Backup power that never sleeps',
     '/services/generator-servicing-installations/', 'Generator supply, installation & servicing'),
    ('solar-output', 'adverts/poster_3.html', 'services/solar-installation.jpg', 'Sustainable power, maximum output',
     '/services/solar-installations/', 'Solar systems designed and installed properly'),
    ('solar-tomorrow', 'adverts/poster_4.html', 'services/solar-installation.jpg', 'Powering a brighter tomorrow',
     '/quote/?service=solar-installations', 'Grid-tie, hybrid & off-grid solar'),
]


def file_uri(path):
    return Path(path).resolve().as_uri()


class Command(BaseCommand):
    help = 'Render BNN advert posters to PNG and add/update them in Admin -> Adverts.'

    def handle(self, *args, **opts):
        browser = next((b for b in BROWSERS if os.path.exists(b)), None)
        if not browser:
            raise CommandError('Microsoft Edge or Google Chrome is required to render the adverts.')
        shop = SiteSettings.load()
        static_img = Path(settings.BASE_DIR) / 'static' / 'img'
        wa = shop.whatsapp or ''
        wa_display = ('+' + wa[:3] + ' ' + wa[3:6] + ' ' + wa[6:]) if len(wa) >= 9 else wa
        tmp = Path(tempfile.mkdtemp(prefix='bnn-adverts-'))
        try:
            for i, (key, tpl, photo, title, link, caption) in enumerate(POSTERS):
                photo_path = Path(settings.MEDIA_ROOT) / photo
                if not photo_path.exists():
                    self.stdout.write(self.style.WARNING(f'skip {key}: missing photo {photo}'))
                    continue
                html = render_to_string(tpl, {
                    'shop': shop, 'photo': file_uri(photo_path), 'wa_display': wa_display,
                    'logo_light': file_uri(static_img / 'logo-horizontal-light.png'),
                    'logo_dark': file_uri(static_img / 'logo-horizontal.png'),
                })
                html_file = tmp / f'{key}.html'
                html_file.write_text(html, encoding='utf-8')
                png = tmp / f'{key}.png'
                subprocess.run([browser, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
                                f'--user-data-dir={tmp / "profile"}',
                                '--force-device-scale-factor=1', '--window-size=1080,1350',
                                '--allow-file-access-from-files', '--virtual-time-budget=8000',
                                f'--screenshot={png}', html_file.as_uri()],
                               check=False, capture_output=True, timeout=120)
                if not png.exists():
                    raise CommandError(f'Browser did not produce an image for {key}.')
                ad = Advert.objects.filter(template_key=key).first() or Advert(template_key=key, order=i)
                ad.title, ad.link, ad.caption = title, link, caption
                if ad.image:
                    ad.image.delete(save=False)
                with png.open('rb') as fh:
                    ad.image.save(f'bnn-advert-{key}.png', File(fh), save=True)
                self.stdout.write(self.style.SUCCESS(f'rendered {key} -> {ad.image.url}'))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
