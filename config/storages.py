"""
Google Cloud Storage backend for Django media files.
Stores uploaded PDFs, documents, and files in Google Cloud Storage.
Free tier: 15GB (same as your Gmail account).
"""
import os
from django.conf import settings
from storages.backends.gcloud import GoogleCloudStorage


class GoogleCloudMediaStorage(GoogleCloudStorage):
    """
    Google Cloud Storage backend for media files (uploads).
    Files are stored in: gs://<bucket>/media/
    """
    location = 'media'
    file_overwrite = False
    default_acl = 'publicRead'

    def __init__(self, *args, **kwargs):
        kwargs['bucket_name'] = settings.GS_BUCKET_NAME
        super().__init__(*args, **kwargs)

    def get_available_name(self, name, max_length=None):
        """
        Returns a unique filename to prevent overwrites.
        """
        import uuid
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        available_name = f"{file_root}_{uuid.uuid4().hex[:8]}{file_ext}"
        if dir_name:
            return os.path.join(dir_name, available_name)
        return available_name


class GoogleCloudStaticStorage(GoogleCloudStorage):
    """
    Google Cloud Storage backend for static files.
    Files are stored in: gs://<bucket>/static/
    """
    location = 'static'
    default_acl = 'publicRead'
    file_overwrite = True

    def __init__(self, *args, **kwargs):
        kwargs['bucket_name'] = settings.GS_BUCKET_NAME
        super().__init__(*args, **kwargs)
