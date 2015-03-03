import signal
import sys
import socket
import webserver

__author__ = 'bawki'

#=============================================================================#

w = webserver.CatServer()

def signal_handler():
    print("Why u kill me :(")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)   # Handle Ctrl-C
if hasattr(signal, "SIGBREAK"):
    # Handle Ctrl-Break e.g. under Windows
    signal.signal(signal.SIGBREAK, signal_handler)