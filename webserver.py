import threading

__author__ = 'bawki'
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import multiprocessing


class CatHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(multiprocessing.current_process().name, 'Get request received')
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        # TODO: set to production url after testing!
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        # Send the html message
        self.wfile.write(bytes("Hello World !", 'UTF-8'))
        return


class CatServer(HTTPServer):
    def __init__(self):
        try:
            self = HTTPServer(("::", 8042), CatHandler, False)
            self.address_family = socket.AF_INET6
            self.socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            self.socket.setsockopt(41, socket.IPV6_V6ONLY, 0)
            self.server_bind()
            self.server_activate()
            print("Started webserver on: ", self.socket.getsockname())

            self.serve_forever()
        except KeyboardInterrupt:
            self.socket_close()