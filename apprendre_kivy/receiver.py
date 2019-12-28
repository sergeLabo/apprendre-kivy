#! /usr/bin/env python3
# -*- coding: utf-8 -*-

#######################################################################
# Copyright (C) La Labomedia January 2020
#
# This file is part of Apprendre Kivy.

# Apprendre Kivy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Apprendre Kivy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Apprendre Kivy.  If not, see <https://www.gnu.org/licenses/>.
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

from twisted.internet.protocol import Protocol, Factory, DatagramProtocol
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor


class Display:

    def __init__(self):
        self.img = cv2.imread("labo.jpg")
        self.loop = 1
        self.img_size = 1
        # vert, hori
        self.img_pos = 0, 0
        # Image noire du fond = 1000*1000
        self.black_image = np.zeros((1000, 1000, 3), np.uint8)

        # Lancement auto de l'affichage
        self.thread_image_display()

        print("Initialisation de Display done.")

    def thread_image_display(self):
        thread_display = threading.Thread(target=self.display)
        thread_display.start()

    def display(self):
        while self.loop:
            self.img_copy = self.img.copy()
            # Dimension
            if self.img_size < 0.2: self.img_size = 0.2
            if self.img_size > 1: self.img_size = 1
            # le logo fait maxi 400*400 sur fond noir 1000*1000
            self.img_copy = cv2.resize(self.img_copy,
                             (int(self.img_size*400), int(self.img_size*400)),
                             interpolation=cv2.INTER_LINEAR)

            black_image = self.black_image.copy()
            # Position
            if self.img_pos[0] < 0: self.img_pos[0] = 0
            if self.img_pos[0] > 1: self.img_pos[0] = 1
            if self.img_pos[1] < 0: self.img_pos[1] = 0
            if self.img_pos[1] > 1: self.img_pos[1] = 1

            x1 = int(600*self.img_pos[1])  # hori
            x2 = x1 + self.img_copy.shape[1]

            y1 = int(600*self.img_pos[0])  # vert
            y2 = y1 + self.img_copy.shape[0]

            # Collage du logo sur le fond
            black_image[y1:y2, x1:x2] = self.img_copy

            cv2.imshow('Image', black_image)

            k = cv2.waitKey(1)
            if k == 27:
                self.loop = 0
        cv2.destroyAllWindows()
        reactor.stop()
        os._exit(0)


class MyMulticastServer(DatagramProtocol):

    def startProtocol(self):
        """Called after protocol has started listening."""

        # Set the TTL>1 so multicast will cross router hops:
        self.transport.setTTL(5)
        # Join a specific multicast group:
        self.transport.joinGroup("228.0.0.5")

        self.disp = Display()
        print("Init multicast")

    def datagramReceived(self, datagram, address):
        """Rather than replying to the group multicast address, we send the
        reply directly (unicast) to the originating port:
            self.transport.write(('Client: Ping').encode("utf-8"),
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


class MyTCPServer(Protocol):
    """
    Attribut de class: nb_protocol
    Un protocol par client connecté,
    chaque protocol est  une  instance indépendante
    """

    nb_protocol = 0

    def __init__(self):
        self.message = ""
        self.disp = Display()
        print("Twisted TCP Serveur créé")

    def connectionMade(self):
        """self.factory was set by the factory"s default buildProtocol
        self.transport.loseConnection() pour fermer
        """

        MyTCPServer.nb_protocol += 1
        print("\nConnexion établie avec un client")
        print("Nombre de protocol = {}".format(MyTCPServer.nb_protocol))

    def connectionLost(self, reason):

        MyTCPServer.nb_protocol -= 1
        print("Connexion terminée")
        print("Nombre de protocol = {}\n".format(MyTCPServer.nb_protocol))

    def dataReceived(self, data):
        """msg = data.decode("utf-8")
        self.message = msg
        print("Message reçu: {}".format(msg))
        """

        print("Data received:", data)
        # data est un dict ou None
        data = datagram_to_dict(data)

        if data:
            if "image_size" in data:
                self.disp.img_size = data["image_size"]
                print("img_size", self.disp.img_size)
            if "image_pos" in data:
                self.disp.img_pos = data["image_pos"]
                print("image_pos", self.disp.img_pos)

        sleep(0.01)


class MyTCPServerFactory(Factory):

    # This will be used by the default buildProtocol to create new protocols:
    protocol = MyTCPServer

    def __init__(self, quote=None):
        print("MyTCPServerFactory créé")


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


def run_multicast_server():
    reactor.listenMulticast(18888, MyMulticastServer(), listenMultiple=True)
    reactor.run()


def run_tcp_server():
    """
    builtins.ValueError: signal only works in main thread
    http://stackoverflow.com/questions/12917980/non-blocking-server-in-twisted
    """

    port = 8000
    endpoint = TCP4ServerEndpoint(reactor, port)
    endpoint.listen(MyTCPServerFactory())
    reactor.run()


if __name__ == '__main__':

    run_multicast_server()
    # #run_tcp_server()
