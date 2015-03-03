__author__ = 'bawki'
from http.server import BaseHTTPRequestHandler, HTTPServer


class CatHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print('Get request received')
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
            self = HTTPServer(('', 8042), CatHandler)
            self.serve_forever()
        except KeyboardInterrupt:
            self.socket_close()

