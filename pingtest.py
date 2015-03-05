#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    ===========================================================================
    IP header info from RFC791
      -> http://tools.ietf.org/html/rfc791)

    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |Version|  IHL  |Type of Service|          Total Length         |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |         Identification        |Flags|      Fragment Offset    |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |  Time to Live |    Protocol   |         Header Checksum       |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                       Source Address                          |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                    Destination Address                        |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                    Options                    |    Padding    |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

    ===========================================================================
    ICMP Echo / Echo Reply Message header info from RFC792
      -> http://tools.ietf.org/html/rfc792

        0                   1                   2                   3
        0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |     Type      |     Code      |          Checksum             |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |           Identifier          |        Sequence Number        |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |     Data ...
        +-+-+-+-+-

    ===========================================================================
    ICMP parameter info:
      -> http://www.iana.org/assignments/icmp-parameters/icmp-parameters.xml
"""

import os
import sys
import time
import array
import socket
import struct
import select
from database import CatDb
import sqlite3

try:
    from _thread import get_ident
except ImportError:
    def get_ident(): return 0

if sys.platform == "win32":
    # On Windows, the best timer is time.clock()
    default_timer = time.clock
else:
    # On most other platforms the best timer is time.time()
    default_timer = time.time

class PingTest:
    # ICMP parameters

    ICMP_ECHOREPLY = 0		# Echo reply (per RFC792)
    ICMP_ECHO = 8			# Echo request (per RFC792)
    ICMP_ECHO_IPV6 = 128		# Echo request (per RFC4443)
    ICMP_ECHO_IPV6_REPLY = 129  # Echo request (per RFC4443)
    ICMP_MAX_RECV = 2048		# Max size of incoming buffer


    MAX_SLEEP = 1000

    class MyStats:
        thisIP = "0.0.0.0"
        pktsSent = 0
        pktsRcvd = 0
        minTime = 999999999
        maxTime = 0
        totTime = 0
        avrgTime = 0

    def checksum(source_string):
        """
        A port of the functionality of in_cksum() from ping.c
        Ideally this would act on the string as a series of 16-bit ints (host
        packed), but this works.
        Network data is big-endian, hosts are typically little-endian
        """
        if (len(source_string) % 2):
            source_string += "\x00"
        converted = array.array("H", source_string)
        if sys.byteorder == "big":
            converted.bytewap()
        val = sum(converted)

        val &= 0xffffffff # Truncate val to 32 bits (a variance from ping.c, which
                          # uses signed ints, but overflow is unlikely in ping)

        val = (val >> 16) + (val & 0xffff)    # Add high 16 bits to low 16 bits
        val += (val >> 16)                    # Add carry from above (if any)
        answer = ~val & 0xffff                # Invert and truncate to 16 bits
        answer = socket.htons(answer)

        return answer

    def do_one(myStats, destIP, hostname, timeout, mySeqNumber, numDataBytes, quiet = False, ipv6=False):
        """
        Returns either the delay (in ms) or None on timeout.
        """
        delay = None

        if ipv6:
            try:  # One could use UDP here, but it's obscure
                mySocket = socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.getprotobyname("ipv6-icmp"))
                mySocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # except socket.error
            except OSError as e:
                # etype, evalue, etb = sys.exc_info()
                print("failed. (socket error: '%s')" % str(e))  # evalue.args[1])
                print('Note that this test requires root.')
                raise  # raise the original error
        else:
            try:  # One could use UDP here, but it's obscure
                mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
                mySocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # except socket.error:
            except OSError as e:
                # etype, evalue, etb = sys.exc_info()
                print("failed. (socket error: '%s')" % str(e))  # evalue.args[1])
                print('Note that this test requires root.')
                raise  # raise the original error

        #my_ID = os.getpid() & 0xFFFF
        my_ID = (os.getpid() ^ get_ident()) & 0xFFFF

        sentTime = PingTest.send_one_ping(mySocket, destIP, my_ID, mySeqNumber, numDataBytes, ipv6)
        if sentTime == None:
            mySocket.close()
            return delay

        myStats.pktsSent += 1

        recvTime, dataSize, iphSrcIP, icmpSeqNumber, iphTTL = PingTest.receive_one_ping(mySocket, my_ID, timeout, ipv6)

        mySocket.close()

        if recvTime:
            delay = (recvTime-sentTime)*1000
            myStats.pktsRcvd += 1
            myStats.totTime += delay
            if myStats.minTime > delay:
                myStats.minTime = delay
            if myStats.maxTime < delay:
                myStats.maxTime = delay
        else:
            delay = None

        return delay

    def send_one_ping(mySocket, destIP, myID, mySeqNumber, numDataBytes, ipv6=False):
        """
        Send one ping to the given >destIP<.
        """
        #destIP  =  socket.gethostbyname(destIP)

        # Header is type (8), code (8), checksum (16), id (16), sequence (16)
        # (numDataBytes - 8) - Remove header size from packet size
        myChecksum = 0

        # Make a dummy header with a 0 checksum.
        if ipv6:
            header = struct.pack(
                "!BbHHh", PingTest.ICMP_ECHO_IPV6, 0, myChecksum, myID, mySeqNumber
            )
        else:
            header = struct.pack(
                "!BBHHH", PingTest.ICMP_ECHO, 0, myChecksum, myID, mySeqNumber
            )

        padBytes = []
        startVal = 0x41
        for i in range(startVal, startVal + numDataBytes):
            padBytes += [(i & 0xff)]  # Keep chars in the 0-255 range
            # data = bytes(padBytes)
            data = bytearray(padBytes)

        # Calculate the checksum on the data and the dummy header.
        myChecksum = PingTest.checksum(header + data) # Checksum is in network order

        # Now that we have the right checksum, we put that in. It's just easier
        # to make up a new header than to stuff it into the dummy.
        if ipv6:
            header = struct.pack(
                "!BbHHh", PingTest.ICMP_ECHO_IPV6, 0, myChecksum, myID, mySeqNumber
            )
        else:
            header = struct.pack(
                "!BBHHH", PingTest.ICMP_ECHO, 0, myChecksum, myID, mySeqNumber
            )

        packet = header + data

        sendTime = default_timer()

        try:
            mySocket.sendto(packet, (destIP, 1))  # Port number is irrelevant for ICMP
        # except socket.error:
        except OSError as e:
            # etype, evalue, etb = sys.exc_info()
            print("General failure (%s)" % str(e))  # (evalue.args[1]))
            return

        return sendTime

    def receive_one_ping(mySocket, myID, timeout, ipv6 = False):
        """
        Receive the ping from the socket. Timeout = in ms
        """
        timeLeft = timeout/1000

        while True:  # Loop while waiting for packet or timeout
            startedSelect = default_timer()
            whatReady = select.select([mySocket], [], [], timeLeft)
            howLongInSelect = (default_timer() - startedSelect)
            if whatReady[0] == []: # Timeout
                return None, 0, 0, 0, 0

            timeReceived = default_timer()

            recPacket, addr = mySocket.recvfrom(PingTest.ICMP_MAX_RECV)

            ipHeader = recPacket[:20]
            iphVersion, iphTypeOfSvc, iphLength, \
            iphID, iphFlags, iphTTL, iphProtocol, \
            iphChecksum, iphSrcIP, iphDestIP = struct.unpack(
                "!BBHHHBBHII", ipHeader
            )

            if ipv6:
                icmpHeader = recPacket[0:8]
            else:
                icmpHeader = recPacket[20:28]

            icmpType, icmpCode, icmpChecksum, \
            icmpPacketID, icmpSeqNumber = struct.unpack(
                "!BBHHH", icmpHeader
            )

            # Match only the packets we care about
            if (icmpType != 8) and (icmpPacketID == myID):
                dataSize = len(recPacket) - 28
                # print (len(recPacket.encode()))
                return timeReceived, (dataSize + 8), iphSrcIP, icmpSeqNumber, iphTTL

            timeLeft = timeLeft - howLongInSelect
            if timeLeft <= 0:
                return None, 0, 0, 0, 0

    def verbose_ping(self, hostname, timeout=3000, count=3, numDataBytes=64, ipv6=False):
        """
        Send >count< ping to >destIP< with the given >timeout< and display
        the result.
        """
        myStats = self.MyStats()  # Reset the stats

        mySeqNumber = 0  # Starting value

        try:
            if ipv6:
                info = socket.getaddrinfo(hostname, None)[0]
                destIP = info[4][0]
            else:
                info = socket.getaddrinfo(hostname, None)[0]
                destIP = info[4][0]
            print("Starting PingTest to %s (%s) with %d data bytes" % (hostname, destIP, numDataBytes))
        except socket.gaierror as e:
            # etype, evalue, etb = sys.exc_info()
            print("PingTest: Unknown host: %s (%s)" % (hostname, str(e)))  # (hostname, evalue.args[1]))
            print()
            return

        myStats.thisIP = destIP

        for i in range(count):
            delay = PingTest.do_one(myStats, destIP, hostname, timeout, mySeqNumber, numDataBytes, ipv6=ipv6)
            if delay is None:
                delay = 0

            mySeqNumber += 1

            # Pause for the remainder of the MAX_SLEEP period (if applicable)
            if PingTest.MAX_SLEEP > delay:
                time.sleep((PingTest.MAX_SLEEP - delay)/1000)
        return myStats

    # FIXME: this has a serious race condition on first startup
    def maybeCreateTable(self):
        exists = False
        self.db.c.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='pingdata';""")
        data = self.db.c.fetchall()
        for row in data:
            if row[0] == 'pingdata':
                exists = True

        if not exists:
            self.db.c.execute("""create table pingdata (
                date REAL,
                dst text,
                sent int,
                received int,
                min int,
                max int,
                avg int,
                loss float)""")
            self.db.db.commit()
            self.db.c.fetchone()

    def storeData(self, stats):
        print("Storing data...")
        print(stats)
        fracLoss = (stats.pktsSent - stats.pktsRcvd)/stats.pktsSent
        try:
            self.db.c.execute("""INSERT INTO 'pingdata' VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                              (time.time(), stats.thisIP, stats.pktsSent, stats.pktsRcvd, stats.minTime, stats.maxTime, stats.totTime/stats.pktsRcvd, 100*fracLoss))
            self.db.db.commit()
        except sqlite3.OperationalError:
            print("PingTest - WARNING: COULD NOT WRITE TO DB, TRYING NEXT ROUND")
        return

    def begin(self, waitperiod, hostname, timeout, count, numDataBytes, ipv6):
        self.db.connect()
        self.maybeCreateTable()
        while True:
            stats = self.verbose_ping(hostname, timeout, count, numDataBytes, ipv6)
            self.storeData(stats)
            time.sleep(waitperiod)

    def __init__(self):
        self.db = CatDb()

def dump_stats(myStats):
    """
    Show stats when pings are done
    """
    print("\n----%s PYTHON PING Statistics----" % myStats.thisIP)

    if myStats.pktsSent > 0:
        myStats.fracLoss = (myStats.pktsSent - myStats.pktsRcvd)/myStats.pktsSent

    print("%d packets transmitted, %d packets received, %0.1f%% packet loss" % (myStats.pktsSent, myStats.pktsRcvd, 100.0 * myStats.fracLoss))

    if myStats.pktsRcvd > 0:
        print("round-trip (ms)  min/avg/max = %d/%0.1f/%d" % (myStats.minTime, myStats.totTime/myStats.pktsRcvd, myStats.maxTime))

    print("")
    return