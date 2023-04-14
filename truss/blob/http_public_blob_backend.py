import shutil
from pathlib import Path

import requests
from truss.blob.blob_backend import BlobBackend
from truss.blob.blob_backend_registry import BlobBackendRegistry
from truss.constants import HTTP_PUBLIC_BLOB_BACKEND

BLOB_DOWNLOAD_TIMEOUT_SECS = 600  # 10 minutes


class HttpPublic(BlobBackend):
    def download(self, URL: str, download_to: Path):
        # Streaming download to keep memory usage low
        resp = requests.get(
            URL,
            allow_redirects=True,
            stream=True,
            timeout=BLOB_DOWNLOAD_TIMEOUT_SECS,
        )
        resp.raise_for_status()
        with download_to.open("wb") as file:
            shutil.copyfileobj(resp.raw, file)


BlobBackendRegistry.register_backend(HTTP_PUBLIC_BLOB_BACKEND, HttpPublic())