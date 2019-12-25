#!/usr/bin/python3
# -*- coding: UTF-8 -*-

#######################################################################
# Copyright (C) La Labomedia August 2018
#
# This file is part of pymultilame.

# pymultilame is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# pymultilame is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with pymultilame.  If not, see <https://www.gnu.org/licenses/>.
#######################################################################

"""
Multicast avec twisted
"""


from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

import sys
import cv2
from time import sleep
import threading
import ast

class Display:

    def __init__(self):
        self.img = cv2.imread("labo.jpg")
        self.loop = 1
        self.img_size = 1
        self.thread_play_partition()

    def thread_play_partition(self):
        thread_partition = threading.Thread(target=self.display)
        thread_partition.start()

    def display(self):
        while self.loop:
            if self.img_size < 0.2:
                self.img_size = 0.2
            self.img = cv2.resize(self.img,
                             (int(self.img_size*1024), int(self.img_size*1024)),
                             interpolation=cv2.INTER_LINEAR)
            cv2.imshow('Image', self.img)

            k = cv2.waitKey(1)
            if k == 27:
                cv2.destroyAllWindows()


class MulticastClient(DatagramProtocol):

    def startProtocol(self):
        # Join the multicast address, so we can receive replies:
        self.transport.joinGroup("228.0.0.5")
        # Send to 228.0.0.5:18888 - all listeners on the multicast address
        # (including us) will receive this message.
        self.transport.write(('Client: Ping').encode("utf-8"), ("228.0.0.5", 18888))
        print("Joined to the multicast")

        self.disp = Display()
        print("Init multicast")

    def datagramReceived(self, datagram, address):
        """self.transport.write(('Client: Ping').encode("utf-8"), ("228.0.0.5", 18888))"""

        print("Datagram %s received from %s" % (datagram, address))
        # data est un dict ou None
        data = datagram_to_dict(datagram)
        if data:
            if "image size" in data:
                self.disp.img_size = data["image size"]
                print("img_size", self.disp.img_size)
        sleep(0.01)


class MulticastServer(DatagramProtocol):

    def startProtocol(self):
        """Called after protocol has started listening."""

        # Set the TTL>1 so multicast will cross router hops:
        self.transport.setTTL(5)
        # Join a specific multicast group:
        self.transport.joinGroup("228.0.0.5")

    def datagramReceived(self, datagram, address):
        print("Datagram %s received from %s" % (datagram, address))
        if datagram == "Client: Ping":
            # Rather than replying to the group multicast address, we send the
            # reply directly (unicast) to the originating port:
            self.transport.write(("Server: Pong").encode("utf-8"), address)


def datagram_to_dict(data):
    """Décode le message.
    Retourne un dict ou None
    """

    try:
        dec = data.decode("utf-8")
    except:
        print("Décodage UTF-8 impossible")
        dec = data

    try:
        msg = ast.literal_eval(dec)
    except:
        print("ast.literal_eval impossible")
        msg = dec

    if isinstance(msg, dict):
        return msg
    else:
        print("Message reçu: None")
        return None


def run_client():
    reactor.listenMulticast(18888, MulticastClient(), listenMultiple=True)
    reactor.run()


def run_server():
    """
    We use listenMultiple=True so that we can run MulticastServer.py and
    MulticastClient.py on same machine.
    """

    reactor.listenMulticast(8005, MulticastServer(), listenMultiple=True)
    reactor.run()


def main(opt):

    if opt == "server":
        run_server()

    if opt == "client":
        run_client()


if __name__ == '__main__':
    # #run_server()
    run_client()

    # #print("""\n\nLancement du script avec:
    # #python3 labmulticasttwisted.py server
    # #ou
    # #python3 labmulticasttwisted.py client\n\n
    # #""")

    # #opt = sys.argv[1]
    # #main(opt)
