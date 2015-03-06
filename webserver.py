import threading

__author__ = 'bawki'
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import multiprocessing
import json
from database import CatDb


class CatHandler(BaseHTTPRequestHandler):
    def servePingData(self, arguments):
        self.sendSuccessHeader()
        print('servePingData: arguments->', arguments)
        self.wfile.write(bytes(self.statsToJson(), "UTF-8"))

    servlets = [("pingdata", servePingData), ]

    def __init__(self, request, client_address, server):
        self.db = CatDb()
        self.db.connect()
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

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

    def statsToJson(self):
        self.db.c.execute("SELECT * FROM 'pingdata'")
        results = self.db.c.fetchall()
        data = []
        for result in results:
            rdata = {
                'date': result[0],
                'thisIP': result[1],
                'pktsSend': result[2],
                'pktsRcvd': result[3],
                'minTime': result[4],
                'maxTime': result[5],
                'totTime': result[6],
                'fracLoss': result[7]
            }
            data.append(rdata)
        return json.dumps(data, indent=4)

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