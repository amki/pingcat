import threading

__author__ = 'bawki'
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import multiprocessing


class CatHandler(BaseHTTPRequestHandler):
    def servePingData(self, arguments):
        self.sendSuccessHeader()
        print('servePingData: arguments->', arguments)
        for a in arguments:
            print("sending: ", a)
            self.wfile.write(bytes(a, "UTF-8"))
        return


    servlets = [("pingdata", servePingData), ]


    def do_GET(self):
        print(multiprocessing.current_process().name, 'Get request received. Path: ', self.path)
        path = self.path
        req = path[1:].split("/")
        print('parsed req: ', req)
        function = [item[1] for item in self.servlets if item[0] == req[0]]
        if len(function) == 1:
            function[0](self, req)
        else:
            self.sendNotFoundHeader()
        return



    def sendSuccessHeader(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        # TODO: set to production url after testing!
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def sendNotFoundHeader(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()


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
            self.server_close()

if __name__ == '__main__':
    c = CatServer()