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


import os, sys
import cv2
from time import sleep
import threading
import ast
import numpy as np

from twisted.internet.protocol import Protocol, Factory, DatagramProtocol,\
                                      ReconnectingClientFactory
from twisted.internet import reactor


class Display:

    def __init__(self):
        self.img = cv2.imread("labo.jpg")
        self.loop = 1
        self.img_size = 1
        self.img_pos = 10, 10
        self.thread_image_display()
        self.black_image = np.zeros((1000, 1000, 3), np.uint8)
        print("Initialisation de Display done.")

    def thread_image_display(self):
        thread_display = threading.Thread(target=self.display)
        thread_display.start()

    def display(self):
        while self.loop:
            # Dimension
            if self.img_size < 0.2:
                self.img_size = 0.2
            self.img = cv2.resize(self.img,
                             (int(self.img_size*400), int(self.img_size*400)),
                             interpolation=cv2.INTER_LINEAR)
            # Position
            black_image = self.black_image.copy()
            # gray[y1:y2, x1:x2] 162:578
            # 1440/900 = 1.6
            # #a = (self.screen[0]/self.screen[1] -1) / 2
            x1 = int(50*self.img_pos[0])
            x2 = x1 + self.img.shape[0]
            y1 = int(50*self.img_pos[1])
            y2 = y1 + self.img.shape[1]
            black_image[y1:y2, x1:x2] = self.img

            cv2.imshow('Image', black_image)

            k = cv2.waitKey(1000)
            if k == 27:
                self.loop = 0
        cv2.destroyAllWindows()
        reactor.stop()
        os._exit(0)


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
        """self.transport.write(('Client: Ping').encode("utf-8"),
                                ("228.0.0.5", 18888))
        """

        print("Datagram %s received from %s" % (datagram, address))
        # data est un dict ou None
        data = datagram_to_dict(datagram)

        if data:
            if "image_size" in data:
                self.disp.img_size = data["image_size"]
                print("img_size", self.disp.img_size)
            if "image_pos" in data:
                self.disp.img_pos = data["image_pos"]
                print("image_pos", self.disp.img_pos)

        sleep(0.01)


class MyTcpClient(Protocol):

    def __init__(self):
        self.disp = Display()
        print("Un protocol client créé")

    def dataReceived(self, data):

        print("Data received:", data)
        # data est un dict ou None
        data = datagram_to_dict(datagram)

        if data:
            if "image_size" in data:
                self.disp.img_size = data["image_size"]
                print("img_size", self.disp.img_size)
            if "image_pos" in data:
                self.disp.img_pos = data["image_pos"]
                print("image_pos", self.disp.img_pos)

        sleep(0.01)


class MyTcpClientFactory(ReconnectingClientFactory):

    def startedConnecting(self, connector):
        print("Essai de connexion ...")

    def buildProtocol(self, addr):
        print("Connecté à {}".format(addr))
        print("Resetting reconnection delay")
        self.resetDelay()
        return MyTcpClient()

    def clientConnectionLost(self, connector, reason):
        print("Lost connection.  Reason:", reason)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        print("Connection failed. Reason:", reason)
        ReconnectingClientFactory.clientConnectionFailed(self,connector,reason)


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


def run_multicast_client():
    reactor.listenMulticast(18888, MulticastClient(), listenMultiple=True)
    reactor.run()


def run_tcp_client():
    """
    builtins.ValueError: signal only works in main thread
    http://stackoverflow.com/questions/12917980/non-blocking-server-in-twisted
    """

    host, port = "192.168.0.105", 8000
    print("Lancement d'un client host:{} port:{}".format(host, port))

    reactor.connectTCP(host, port, MyTcpClientFactory())
    reactor.run(installSignalHandlers=False)

if __name__ == '__main__':

    # #run_multicast_client()
    run_tcp_client()
