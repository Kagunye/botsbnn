# BNN Engineering – company website + shop (Django)

An engineering-services website (power & backup, wiring, industrial panels, security, solar) with an online equipment shop as one section. Django 5 + Bootstrap 5.

## Quick start

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_services                      # service categories + 15 services
python manage.py seed_shop                          # shop categories, partner brands, banners (+30 demo products)
python manage.py import_catalog <export-folder> --replace-demo   # real products + images (see below)
python manage.py createsuperuser                    # for /admin/
python manage.py runserver
```

## Configuration (environment variables)

DEBUG is **off** by default. Set these on the server (or in your shell for local work):

| Variable | Example | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | a long random string | **Required for a live site** (a dev fallback is used if unset) |
| `DJANGO_ALLOWED_HOSTS` | `bnnengineering.co.ke,www.bnnengineering.co.ke` | Domains the site answers on (default `localhost,127.0.0.1`) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://bnnengineering.co.ke` | Needed for forms when served over HTTPS on a domain |
| `DJANGO_DEBUG` | `True` | Turn on Django's debug pages for local development only |
| `DJANGO_SERVE_MEDIA` | `False` | Set if your web server (e.g. Nginx) serves `/media/` itself |

Static files (CSS/JS/video) are served by WhiteNoise; run `python manage.py collectstatic` when deploying.

## Site map

| URL | Page |
|---|---|
| `/` | Company homepage – hero with quote form, service groups, popular services, process, shop teaser |
| `/services/` | All services, grouped (Power & Backup, Wiring & Infrastructure, Industrial & Commercial, Access & Security, Solar & Clean Energy) |
| `/services/<slug>/` | Service detail with "what's included" and a quote form |
| `/quote/` (`?service=<slug>`) | Quote request form – saved under **Quote requests** in admin |
| `/shop/` | Shop landing (banners, top deals, partners) |
| `/shop/products/` | Product search / filter / sort |
| `/about/`, `/contact/` | Company pages |
| `/cart/`, `/cart/checkout/` | Cart and checkout (priced products only) |
| `/admin/` | Manage everything |

## Apps

- `services` – ServiceCategory, Service, QuoteRequest. Edit services, icons, "what's included" and featured flags in admin.
- `store` – shop catalogue (categories, brands, products + gallery images, banners, orders).
- `cart` – session cart and checkout.
- `accounts` – register / login / my orders.
- `pages` – About, Contact (contact messages saved in admin).

## Importing a product catalogue

`import_catalog` reads a folder with `products.json` (`title`, `description`, `image_files`) and `images/`:

- category and brand are inferred from the product title
- the first image becomes the main photo; other real images (not tiny icons) go into the gallery
- flattened spec tables become the **Specifications** tab
- sentences that mention the source shop are dropped
- products are created **without prices** ("Price on request" + WhatsApp quote button). Set a price in admin to make a product purchasable.

Use `--update` to refresh existing products by name.

## Managing content (Admin → /admin/)

| Admin section | What it controls |
|---|---|
| **Pages → Site settings** | Company name, phones, email, WhatsApp, address, hours, KRA PIN, payment details (bank, account, Paybill), social links, homepage hero text & stats, emergency banner, About page text, footer text, default VAT rate, quotation validity & terms |
| Pages → Homepage process steps / "Why choose us" items | The "How we work" steps, the homepage strip and the About page value cards |
| Services → Services / Service categories | All services, photos, "what's included", featured flag |
| Services → Quote requests | Website quote requests – select one and run **"Create a quotation from selected request"** |
| **Quotations → Quotations** | Build quotations (see below) |
| Store → Products / Categories / Brands / Banners / Orders | The shop |
| Pages → Contact messages | Contact form messages |

## Quotations

Admin → Quotations → Add:

- Client details, project title, issue date and "valid until" (auto-set from Site settings).
- Line items: description (or pick a shop product), quantity, unit, unit price – line totals and the grand total update live.
- **Discount**: percentage or fixed KSh amount.
- **Charge VAT** checkbox: ticked = VAT (default 16%, editable) is added on the discounted subtotal; unticked = no VAT.
- Numbers are automatic: `BNN-Q2026-0001`, `BNN-Q2026-0002`, ...
- **View / Print / Save as PDF** opens a branded A4 quotation with your logo, payment details, terms and signature lines (use the browser's "Save as PDF"). Only logged-in staff can open it.
- List actions: mark as sent, mark as accepted, duplicate.

## Before going live

- Replace the placeholder phone numbers / email / WhatsApp in Admin → Site settings.
- Make sure you have the right to use any product photos and descriptions you imported.
- Set `DEBUG = False`, a new `SECRET_KEY`, `ALLOWED_HOSTS`; use PostgreSQL; run `collectstatic`; serve `/media/`.
- Optionally email staff on new quote requests and integrate M-Pesa for shop payments.

## Deploying to Vercel with www.bnnengineering.co.ke

1. Environment variables: in Vercel open **Project → Settings → Environment Variables → Import .env** and pick the
   private `.env` file (template: `.env.example`). Never commit `.env`.
2. Domain: **Project → Settings → Domains → Add** `www.bnnengineering.co.ke` (and `bnnengineering.co.ke`, set to
   redirect to www). At your domain registrar add the DNS records Vercel shows (usually `CNAME www → cname.vercel-dns.com`
   and an `A` record for the root domain).
3. Redeploy. Both domains are already allowed in `config/settings.py`.

## Database and images: Supabase

The live site keeps its data in **Supabase Postgres** and uploaded images in the public **Supabase Storage** bucket `media`.

Settings read either name for each value, so Vercel's Supabase integration works without extra setup:

| Purpose | Variable (either works) |
|---|---|
| Database | `DATABASE_URL` or `POSTGRES_URL` (transaction pooler, port 6543) |
| Storage URL | `SUPABASE_URL` or `NEXT_PUBLIC_SUPABASE_URL` |
| Storage key (server only) | `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_SECRET_KEY` |

Without them the site falls back to the bundled SQLite file and `/media/` (read-only on Vercel).

**After changing models**, apply migrations to Supabase from your computer, with the private `.env` loaded and the
session pooler (port 5432):

```bash
DATABASE_URL="<POSTGRES_URL_NON_POOLING>" python manage.py migrate
```

`python manage.py runserver` on its own still uses the local `db.sqlite3`. Edits made there do **not** reach the live
site; make content changes in the live admin.

## Email (Zoho Mail)

The site sends mail through Zoho SMTP as `info@bnnengineering.co.ke` (`smtp.zoho.com`, port 465 SSL):

- a notification to `NOTIFY_EMAIL` for every quote request, contact message and shop order (Reply-To = the customer);
- a confirmation to the customer when they give an email address.

Set `EMAIL_HOST_PASSWORD` (mailbox password, or an app-specific password if two-factor sign-in is on) in `.env` and
in Vercel's environment variables. Without it, emails are only written to the server log and forms keep working.
If the Zoho account is in another region, set `EMAIL_HOST` (e.g. `smtp.zoho.eu`). For port 587 set `EMAIL_PORT=587`.
