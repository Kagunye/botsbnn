from django.db.utils import OperationalError
from django.shortcuts import render


class ReadOnlyDatabaseMiddleware:
    """Show a friendly page instead of a Server Error (500) when something tries to save while the
    database is read-only (Vercel without DATABASE_URL): registering, quote requests, orders, admin edits."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, OperationalError) and 'readonly' in str(exception).replace('-', '').lower():
            return render(request, 'saving_unavailable.html', status=503)
        return None
