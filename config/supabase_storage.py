"""Django file storage backed by a public Supabase Storage bucket (REST API, no extra packages).

Files are uploaded with the service-role key (server side only) and served from the bucket's public URL.
Configured in settings.py from SUPABASE_URL / NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.
"""
import json
import mimetypes
import urllib.error
import urllib.request
from urllib.parse import quote

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class SupabaseStorage(Storage):
    def __init__(self, bucket=None):
        self.base = settings.SUPABASE_URL
        self.key = settings.SUPABASE_SERVICE_KEY
        self.bucket = bucket or settings.SUPABASE_BUCKET

    # -- helpers -------------------------------------------------------------------------------------------
    def _path(self, name):
        return quote(name.replace('\\', '/').lstrip('/'))

    def _request(self, method, url, data=None, headers=None, timeout=60):
        h = {'Authorization': f'Bearer {self.key}', 'apikey': self.key}
        h.update(headers or {})
        req = urllib.request.Request(url, data=data, headers=h, method=method)
        return urllib.request.urlopen(req, timeout=timeout)

    def _public(self, name):
        return f'{self.base}/storage/v1/object/public/{self.bucket}/{self._path(name)}'

    # -- Storage API ---------------------------------------------------------------------------------------
    def _save(self, name, content):
        name = name.replace('\\', '/')
        if hasattr(content, 'seek'):
            content.seek(0)
        data = content.read()
        ctype = getattr(content, 'content_type', None) or mimetypes.guess_type(name)[0] or 'application/octet-stream'
        url = f'{self.base}/storage/v1/object/{self.bucket}/{self._path(name)}'
        self._request('POST', url, data=data, headers={'Content-Type': ctype, 'x-upsert': 'true',
                                                        'Cache-Control': 'max-age=31536000'}, timeout=120)
        return name

    def _open(self, name, mode='rb'):
        with self._request('GET', f'{self.base}/storage/v1/object/{self.bucket}/{self._path(name)}') as r:
            return ContentFile(r.read(), name=name)

    def exists(self, name):
        try:
            with self._request('HEAD', self._public(name), timeout=20) as r:
                return r.status == 200
        except urllib.error.HTTPError:
            return False

    def delete(self, name):
        body = json.dumps({'prefixes': [name.replace('\\', '/')]}).encode()
        try:
            self._request('DELETE', f'{self.base}/storage/v1/object/{self.bucket}', data=body,
                          headers={'Content-Type': 'application/json'}).close()
        except urllib.error.HTTPError:
            pass

    def size(self, name):
        with self._request('HEAD', self._public(name), timeout=20) as r:
            return int(r.headers.get('Content-Length', 0))

    def url(self, name):
        return self._public(name)

    def path(self, name):
        raise NotImplementedError('Supabase files have no local path')
