"""Rebrand the advert artwork in media/adverts/source/ (owned by BNN) with BNN Engineering branding.

    python manage.py render_brand_adverts

For each source poster it:
  1. removes the original company's logo, contacts and product brand marks (OpenCV inpainting),
  2. overlays BNN's logo and taglines in the same places (no phone numbers, emails or web addresses),
  3. renders a 1080 px-wide image with headless Chrome and stores it in Admin -> Adverts.
"""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from pages.models import Advert, SiteSettings

BROWSERS = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
]
CSS_W = 736          # design coordinates below are in a 736 px-wide space
OUT_W = 1080         # final image width

# Each advert: source file, erase boxes (x1, y1, x2, y2 in 736-space), overlay HTML, title, link.
ADS = [
    dict(key='brand-01', src='src01.jpg', title='Powering a brighter tomorrow', link='/services/solar-installations/',
         erase=[],
         html='''
<div class="pill" style="left:506px;top:820px;width:190px;height:44px;background:#1878b4;font-size:15px;font-weight:500">
  Get a Free Quote <i class="bi bi-arrow-right"></i></div>'''),

    dict(key='brand-02', src='src02.jpg', title='Sustainable power, maximum output', link='/services/solar-installations/',
         erase=[(26, 20, 162, 54), (532, 24, 708, 52), (220, 832, 516, 886)],
         html='''
<div style="position:absolute;right:26px;top:27px;color:#fff;font:500 12.5px Poppins;display:flex;gap:7px;align-items:center">
  <i class="bi bi-whatsapp"></i><i class="bi bi-facebook"></i><i class="bi bi-instagram"></i> @BNNEngineering</div>
<div style="position:absolute;left:206px;top:832px;width:324px;height:52px;border-radius:26px;background:rgba(18,18,18,.9);
  border:1px solid rgba(255,255,255,.4);display:flex;align-items:center;justify-content:space-between;padding:0 6px 0 24px;color:#fff;font:500 15px Poppins">
  Get a free solar quote
  <span style="display:grid;place-items:center;width:40px;height:40px;border-radius:50%;background:#ffd23f;color:#111;font-size:18px"><i class="bi bi-arrow-right"></i></span></div>'''),

    dict(key='brand-03', src='src03.jpg', title='Residential battery storage in Kenya',
         link='/services/battery-power-backup-systems/',
         erase=[(22, 32, 204, 100), (40, 420, 194, 456), (360, 610, 445, 670), (482, 1034, 708, 1076)],
         html='''
<div style="position:absolute;left:45px;top:420px;color:#fff;font:300 27px Montserrat;letter-spacing:.3px">in Kenya</div>
<div class="pill" style="left:480px;top:1034px;width:228px;height:40px;border:1.5px solid #fff;background:rgba(0,0,0,.5);font-size:17px;font-weight:500;justify-content:space-between;padding:0 6px 0 16px">
  Get a Free Quote <i class="bi bi-chevron-right" style="width:24px;height:24px;border-radius:50%;background:#f7b733;color:#111;display:grid;place-items:center;font-size:13px"></i></div>'''),

    dict(key='brand-04', src='src04.jpg', title='Power that lifts you higher', link='/services/battery-power-backup-systems/',
         erase=[(10, 20, 234, 98), (646, 14, 724, 54), (26, 384, 334, 434), (468, 336, 508, 402),
                (10, 850, 250, 906), (400, 850, 720, 906)],
         html='''
<div style="position:absolute;left:31px;top:389px;color:#fff;font:500 15px/1.4 Poppins">
  <b style="color:#7ed321;font-weight:700">BNN</b> Lithium Backup–Smart Energy<br>for Brighter Tomorrow</div>
<div style="position:absolute;left:0;right:0;bottom:0;height:120px;background:linear-gradient(180deg,rgba(3,10,20,0),rgba(3,10,20,.92) 55%);"></div>
<div style="position:absolute;left:0;right:0;top:866px;text-align:center;color:#fff;font:500 16px Poppins;letter-spacing:.4px">
  Lithium batteries <span style="color:#7ed321">&#9679;</span> Hybrid inverters <span style="color:#7ed321">&#9679;</span> Solar</div>'''),

    dict(key='brand-05', src='src05.jpg', title='Built for the load nobody else would dare take',
         link='/services/battery-power-backup-systems/',
         erase=[(12, 14, 146, 146), (318, 650, 408, 696), (0, 852, 736, 920)],
         html='''
<div style="position:absolute;left:8px;right:8px;top:858px;height:56px;border-radius:10px;background:#fff;display:grid;grid-template-columns:repeat(3,1fr);align-items:center;padding:0 14px;box-shadow:0 -2px 12px rgba(0,0,0,.08)">
  <div class="info"><span class="ic"><i class="bi bi-battery-charging"></i></span><div><small>Long-life</small><b>Lithium batteries</b></div></div>
  <div class="info"><span class="ic"><i class="bi bi-tools"></i></span><div><small>Professional</small><b>Installation</b></div></div>
  <div class="info"><span class="ic"><i class="bi bi-shield-check"></i></span><div><small>After-sales</small><b>Warranty support</b></div></div>
</div>'''),

    dict(key='brand-06', src='src06.jpg', title='Reliable warmth, every time', link='/shop/category/solar-water-heaters/',
         erase=[(6, 6, 150, 60), (566, 10, 720, 60), (462, 122, 532, 150), (466, 243, 502, 264)],
         html='''
<div style="position:absolute;left:0;right:0;top:866px;height:54px;background:__BAR__;display:flex;align-items:center;justify-content:center;gap:10px;color:#fff;font:500 15.5px Poppins;letter-spacing:.3px">
  <i class="bi bi-droplet-half"></i> Water heaters supplied &amp; installed by BNN Engineering</div>'''),

    dict(key='brand-07', src='src07.jpg', title='Your water heater is on right now', link='/shop/category/solar-water-heaters/',
         erase=[(350, 728, 498, 768)],
         html='''
<div style="position:absolute;left:99px;top:246px;width:104px;height:31px;border-radius:50%;background:radial-gradient(ellipse at 50% 35%,#3c4a5c,#141c26 75%);border:2px solid #9aa4ad;box-shadow:inset 0 1px 2px rgba(255,255,255,.35),0 1px 2px rgba(0,0,0,.4);display:grid;place-items:center;color:#d8dee4;font:700 13px Montserrat;letter-spacing:2px">BNN</div>'''),

    dict(key='brand-08', src='src08.jpg', title='Lower carbon, smarter living', link='/shop/category/heat-pump-water-heaters/',
         erase=[(432, 402, 508, 424)],
         html='''
<div class="pill" style="left:250px;top:50px;width:236px;height:40px;background:linear-gradient(180deg,#26405e,#152a42);border:1.5px solid rgba(255,220,140,.7);box-shadow:0 0 14px rgba(255,210,120,.45);font-size:17px;font-weight:500">
  BNN Engineering <i class="bi bi-lightning-charge-fill" style="color:#ffd23f"></i></div>'''),

    dict(key='brand-09', src='src09.jpg', title='Power your home the smart way', link='/services/solar-installations/',
         erase=[(272, 76, 468, 120), (40, 836, 384, 894)],
         html='''
<div style="position:absolute;left:52px;top:864px;color:#fff;font:500 15.5px Poppins;letter-spacing:.2px"><span style="color:#8fe33b">&#9679;</span> BNN Engineering &middot; Solar &amp; Power Solutions</div>'''),

    dict(key='brand-10', src='src10.jpg', title='Stop fueling expenses, start powering savings', link='/services/solar-installations/',
         erase=[(272, 58, 468, 102), (40, 836, 384, 894)],
         html='''
<div style="position:absolute;left:52px;top:864px;color:#222;font:500 15.5px Poppins;letter-spacing:.2px"><span style="color:#1e90ff">&#9679;</span> BNN Engineering &middot; Solar &amp; Power Solutions</div>'''),
]

PAGE = '''<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Montserrat:wght@300;400;600;700;800&display=block" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0} html,body{width:__W__px;height:__H__px;overflow:hidden;background:#000}
.bg{position:absolute;left:0;top:0;width:__W__px;height:__H__px}
.logo{position:absolute;width:auto}
.pill{position:absolute;display:flex;align-items:center;justify-content:center;gap:8px;border-radius:40px;color:#fff;font-family:Poppins,Arial,sans-serif}
.dot{display:inline-grid;place-items:center;width:34px;height:34px;border-radius:50%;color:#fff;font-size:16px}
.info{display:flex;align-items:center;gap:8px;min-width:0}
.info .ic{width:34px;height:34px;flex-shrink:0;border-radius:50%;background:#0c3556;color:#fff;display:grid;place-items:center;font-size:15px}
.info small{display:block;font:400 11.5px Poppins;color:#444}
.info b{display:block;font:600 11.5px Poppins;color:#0c3556;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
</style></head><body><img class="bg" src="__BG__">__OVERLAY__</body></html>'''


def uri(p):
    return Path(p).resolve().as_uri()


class Command(BaseCommand):
    help = 'Rebrand the owned advert artwork in media/adverts/source/ with BNN branding.'

    def add_arguments(self, parser):
        parser.add_argument('--only', help='Render a single advert, e.g. brand-04')

    def handle(self, *args, only=None, **opts):
        browser = next((b for b in BROWSERS if os.path.exists(b)), None)
        if not browser:
            raise CommandError('Google Chrome (or Edge) is required to render the adverts.')
        shop = SiteSettings.load()
        src_dir = Path(settings.MEDIA_ROOT) / 'adverts' / 'source'
        img = Path(settings.BASE_DIR) / 'static' / 'img'
        wa = shop.whatsapp or ''
        wa_display = ('+' + wa[:3] + ' ' + wa[3:6] + ' ' + wa[6:9] + ' ' + wa[9:]).strip() if len(wa) >= 12 else wa
        tokens = {
            '__PHONE1__': shop.phone1, '__PHONE2__': shop.phone2 or '', '__EMAIL__': shop.email,
            '__ADDRESS__': shop.address, '__WA__': wa_display,
            '__LOGO_LIGHT__': uri(img / 'logo-horizontal-light.png'), '__LOGO_DARK__': uri(img / 'logo-horizontal.png'),
            '__LOGO_FULL__': uri(img / 'logo-full.png'),
        }
        tmp = Path(tempfile.mkdtemp(prefix='bnn-brand-ads-'))
        try:
            for order, ad in enumerate(ADS):
                if only and ad['key'] != only:
                    continue
                src = cv2.imread(str(src_dir / ad['src']), cv2.IMREAD_COLOR)
                if src is None:
                    self.stdout.write(self.style.WARNING(f"skip {ad['key']}: missing {ad['src']}"))
                    continue
                h0, w0 = src.shape[:2]
                out_h = round(h0 * OUT_W / w0)
                big = cv2.resize(src, (OUT_W, out_h), interpolation=cv2.INTER_LANCZOS4) if w0 != OUT_W else src.copy()
                k = OUT_W / CSS_W
                if ad['erase']:
                    mask = np.zeros(big.shape[:2], np.uint8)
                    for x1, y1, x2, y2 in ad['erase']:
                        cv2.rectangle(mask, (int(x1 * k), int(y1 * k)), (int(x2 * k), int(y2 * k)), 255, -1)
                    big = cv2.inpaint(big, mask, 9, cv2.INPAINT_TELEA)
                bg = tmp / f"{ad['key']}-bg.png"
                cv2.imwrite(str(bg), big)
                # sample the original bottom-bar colour where a design uses one
                bar = big[out_h - 10, OUT_W // 2][::-1]
                css_h = round(out_h / k)
                html = ad['html']
                for t, v in tokens.items():
                    html = html.replace(t, v)
                html = html.replace('__BAR__', 'rgb(%d,%d,%d)' % tuple(int(c) for c in bar))
                page = (PAGE.replace('__W__', str(CSS_W)).replace('__H__', str(css_h))
                        .replace('__BG__', uri(bg)).replace('__OVERLAY__', html))
                hf = tmp / f"{ad['key']}.html"
                hf.write_text(page, encoding='utf-8')
                png = tmp / f"{ad['key']}.png"
                subprocess.run([browser, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
                                f'--user-data-dir={tmp / "profile"}', f'--force-device-scale-factor={k:.6f}',
                                f'--window-size={CSS_W},{css_h}', '--allow-file-access-from-files',
                                '--virtual-time-budget=8000', f'--screenshot={png}', hf.as_uri()],
                               capture_output=True, timeout=120)
                if not png.exists():
                    raise CommandError(f"Browser did not produce an image for {ad['key']}.")
                jpg = tmp / f"{ad['key']}.jpg"
                cv2.imwrite(str(jpg), cv2.imread(str(png)), [cv2.IMWRITE_JPEG_QUALITY, 92])
                advert = Advert.objects.filter(template_key=ad['key']).first() or Advert(template_key=ad['key'])
                advert.title, advert.link, advert.order, advert.is_active = ad['title'], ad['link'], order, True
                if advert.image:
                    advert.image.delete(save=False)
                with jpg.open('rb') as fh:
                    advert.image.save(f"bnn-{ad['key']}.jpg", File(fh), save=True)
                self.stdout.write(self.style.SUCCESS(f"{ad['key']}: {advert.image.url}"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
