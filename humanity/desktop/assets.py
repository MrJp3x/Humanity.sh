"""A read-only loopback server for the bundled HTML, modules, and fonts.

There is no HTTP API. Commands travel exclusively over Qt's WebChannel.
Python files, Git metadata, saves, and arbitrary filesystem paths are not served.
"""

import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import unquote, urlsplit


def asset_root() -> Path:
    package = Path(__file__).resolve().parents[1]
    bundled = package / "web"
    if (bundled / "index.html").is_file():
        return bundled
    source = package.parent
    if (source / "index.html").is_file():
        return source
    raise FileNotFoundError("HTML assets are missing. Run the application from its checkout or install a complete wheel.")


class AssetServer:
    def __init__(self, root: Path | None = None):
        self.root = (root or asset_root()).resolve()
        asset_directory = self.root

        class Handler(BaseHTTPRequestHandler):
            def do_HEAD(self):
                self.serve(head=True)

            def do_GET(self):
                self.serve(head=False)

            def log_message(self, *_):
                pass

            def serve(self, *, head):
                name = unquote(urlsplit(self.path).path).lstrip("/") or "index.html"
                allowed = name in ("index.html", "humanity/data/catalog.json") or name.startswith(("src/", "public/"))
                target = (asset_directory / name).resolve()
                if not allowed or any(part.startswith(".") for part in Path(name).parts) or not target.is_relative_to(asset_directory) or not target.is_file():
                    self.send_error(404)
                    return
                mime = {".js": "text/javascript", ".json": "application/json", ".woff2": "font/woff2"}.get(target.suffix, mimetypes.guess_type(name)[0] or "application/octet-stream")
                data = target.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-cache")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data: blob:; object-src 'none'; base-uri 'self'")
                self.end_headers()
                if not head:
                    self.wfile.write(data)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.thread = Thread(target=self.server.serve_forever, name="humanity-assets", daemon=True)

    @property
    def origin(self):
        return f"http://127.0.0.1:{self.server.server_port}"

    def start(self):
        self.thread.start()
        return self.origin + "/?desktop=1"

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
