"""Local forwarding with verified SSH host keys and deterministic cleanup."""
import select
import socketserver
import threading
from contextlib import contextmanager


@contextmanager
def ssh_tunnel(host, username, remote_host, remote_port, key_filename=None, port=22, known_hosts=None):
    import paramiko
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    if known_hosts:
        client.load_host_keys(known_hosts)
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    server = None
    thread = None
    try:
        client.connect(host, port=port, username=username, key_filename=key_filename,
                       timeout=15, auth_timeout=15, banner_timeout=15)
        transport = client.get_transport()

        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                channel = transport.open_channel("direct-tcpip", (remote_host, remote_port),
                                                 self.request.getpeername(), timeout=15)
                if channel is None:
                    return
                try:
                    while transport.is_active():
                        ready, _, _ = select.select([self.request, channel], [], [], 1)
                        for source in ready:
                            data = source.recv(65536)
                            if not data:
                                return
                            (channel if source is self.request else self.request).sendall(data)
                finally:
                    channel.close()

        class Server(socketserver.ThreadingTCPServer):
            daemon_threads = True

        server = Server(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        yield server.server_address
    finally:
        if server:
            server.shutdown()
            server.server_close()
        client.close()
        if thread:
            thread.join(timeout=5)
