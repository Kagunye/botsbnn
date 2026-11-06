from django.apps import AppConfig
from django.conf import settings


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # On Vercel without DATABASE_URL the bundled SQLite file is read-only. Django normally writes the
        # "last login" time on every login, which would crash with a Server Error (500). Skip that write there.
        if getattr(settings, 'READ_ONLY_DB', False):
            from django.contrib.auth.models import update_last_login
            from django.contrib.auth.signals import user_logged_in
            user_logged_in.disconnect(update_last_login, dispatch_uid='update_last_login')
