__author__ = 'bawki'
from http.server import BaseHTTPRequestHandler, HTTPServer


class CatHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print('Get request received')
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        # Send the html message
        self.wfile.write(bytes("Hello World !", 'UTF-8'))
        return
PORT = 8042

try:
    server = HTTPServer(('', PORT), CatHandler)

    print('Started HTTPServer')
    server.serve_forever()
except KeyboardInterrupt:
    server.socket.close()
