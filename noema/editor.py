"""Local writing desk: the same strict parser serves CLI and browser input."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from .grammar import parse, format_graph
from .glossary import lexicon
from .render import render
from .script import encode

MAX_BODY = 262144


def inspect_text(text):
    graph = parse(text)
    canonical = format_graph(graph)
    # Browser JSON.parse rounds integers beyond 2**53. Keep a serialized copy
    # for display/export so the written language's exact quantities survive.
    return {"canonical": canonical, "graph": graph, "graph_json": json.dumps(graph, ensure_ascii=False, indent=2),
            "script": encode(canonical), "svg": render(canonical, 22)}


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, body, content_type="application/json; charset=utf-8"):
        payload = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        resources = {"/": ("editor.html", "text/html; charset=utf-8"), "/practice": ("practice.html", "text/html; charset=utf-8"), "/font.ttf": ("NoemaWritten.ttf", "font/ttf")}
        if self.path in resources:
            name, content_type = resources[self.path]
            self.respond(200, files("noema").joinpath("resources", name).read_bytes(), content_type)
        elif self.path == "/lexicon":
            self.respond(200, lexicon())
        elif self.path == "/practice/tasks":
            from .practice import public_tasks
            self.respond(200, public_tasks())
        elif self.path == "/alphabet.svg":
            from .render import alphabet_svg
            self.respond(200, alphabet_svg().encode("utf-8"), "image/svg+xml")
        else:
            self.respond(404, {"error": "Not found"})

    def do_POST(self):
        if self.path not in ("/inspect", "/practice/grade"):
            self.respond(404, {"error": "Not found"})
            return
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            self.respond(415, {"error": "Expected application/json"})
            return
        origin = self.headers.get("Origin")
        port = self.server.server_port
        if origin is not None and origin not in (f"http://127.0.0.1:{port}", f"http://localhost:{port}"):
            self.respond(403, {"error": "Use the local editor origin"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_BODY:
                self.respond(413, {"error": "Document exceeds the editor input limit"})
                return
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            if self.path == "/practice/grade":
                from .practice import grade
                self.respond(200, grade(data))
                return
            if not isinstance(data, dict) or not isinstance(data.get("text"), str):
                raise ValueError("Expected a text field")
            self.respond(200, inspect_text(data["text"]))
        except (ValueError, TypeError, RecursionError) as exc:
            self.respond(400, {"error": str(exc)})

    def log_message(self, fmt, *args):
        # Documents and names are never written into request logs.
        return


def serve(port=8765):
    if not 0 <= port <= 65535:
        raise ValueError("Invalid editor port")
    with ThreadingHTTPServer(("127.0.0.1", port), Handler) as server:
        print(f"Noema writing desk: http://127.0.0.1:{server.server_port} (Ctrl+C to stop)", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
