import socket
import sys
from abc import ABC, abstractmethod
from threading import Thread, Lock
from http import server
from time import time


DEFAULT_SERVER_TIMEOUT = 60 * 2


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


class BaseRequestHandler(ABC, server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    server_version = 'HTTP/1.1'
    close_connection = True

    @abstractmethod
    def get_message(self) -> str:
        ...

    def send_response_(self, message):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(bytes(message, "utf-8"))

    def do_GET(self):
        message = self.get_message()
        self.send_response_(message)


class DefaultWatcher(Thread):
    def __init__(self, http_server, timeout):
        super().__init__()
        self.daemon = True
        self.lock = Lock()
        self.http_server = http_server
        self.timeout = timeout

    def run(self):
        self.lock.acquire()
        stop_time = time() + self.timeout
        while time() < stop_time and self.lock.locked():
            continue
        self.http_server.shutdown()

    def shutdown(self):
        self.lock.release()



def start_server(request_handler, port=80, timeout=DEFAULT_SERVER_TIMEOUT, watcher=None):
    ip = get_local_ip()
    with server.HTTPServer(('', port), request_handler) as http_server:
        if watcher is None:
            watcher = DefaultWatcher(http_server, timeout)

        server_thread = Thread(target=http_server.serve_forever, daemon=True)
        watcher.start()
        server_thread.start()
        print(f'Server started @ {ip}, will run for {timeout} seconds')
        try:
            while watcher.is_alive():
                continue
        except TimeoutError:
            print("Stopping server from timeout")
            watcher.shutdown()
        except KeyboardInterrupt:
            print("Stopping server from user interrupt")
            watcher.shutdown()
        except:
            print("Received unknown exception")
            watcher.shutdown()
            raise sys.exc_info()[1]
        finally:
            print("Shut down server")

