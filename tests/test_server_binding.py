from http.server import ThreadingHTTPServer
import pytest
from noema.editor import Handler, NoemaHTTPServer


def test_two_live_servers_cannot_silently_share_one_address():
    with NoemaHTTPServer(("127.0.0.1", 0), Handler) as first:
        for cls in (NoemaHTTPServer, ThreadingHTTPServer):
            with pytest.raises(OSError):
                with cls(first.server_address, Handler):
                    pass


def test_new_server_rejects_an_address_already_used_by_a_legacy_server():
    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as legacy:
        with pytest.raises(OSError):
            with NoemaHTTPServer(legacy.server_address, Handler):
                pass
