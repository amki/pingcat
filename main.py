import signal
import sys
from pingtest import PingTest
from webserver import CatServer
from multiprocessing import Process
import database
__author__ = 'bawki'

#=============================================================================#

db = database.CatDb()


def pingtest(waitperiod, hostname, timeout, count, numDataBytes, ipv6):
    PingTest.begin(waitperiod, hostname, timeout, count, numDataBytes, ipv6)


def signal_handler():
    print("Why u kill me :(")
    sys.exit(0)

tasks = [
    ("WebServer", CatServer, ""),
    ("Pingtest v6", pingtest, (5, "2001:4ba0:ffe8:e::101", 3000, 3, 1024, True)),
    ("PingTest v4", pingtest, (4, "89.163.214.191", 3000, 3, 1024, False))
    ]

if __name__ == '__main__':
    for task in tasks:
        p = Process(target=task[1], name=task[0], args=task[2])
        p.start()
    signal.signal(signal.SIGINT, signal_handler)   # Handle Ctrl-C
    if hasattr(signal, "SIGBREAK"):
        # Handle Ctrl-Break e.g. under Windows
        signal.signal(signal.SIGBREAK, signal_handler)