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
Server avec kivy

Uniquement pour utilisation sur PC

Inspiré du fichier texture.py de la documention de kivy
"""


# Import de la bibliothèque standard, ne pas les ajouter dans buildozer.spec
import os
import ast
from time import sleep

# Pour twisted
from kivy.support import install_twisted_reactor
install_twisted_reactor()
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, Factory, DatagramProtocol
from twisted.internet.endpoints import TCP4ServerEndpoint

# Pour kivy
import kivy
kivy.require('1.11.1')
from kivy.core.window import Window

k = 1.0
WS = (int(1280*k), int(720*k))
Window.size = WS

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.clock import Clock


# Variable globale:
# Pour passer des valeurs entre MyMulticastServer et TextureAccessibleWidget
GLOBAL_DICT = { "image_size": 1,
                "image_pos": (0, 0),
                "freq": 1}


class MyMulticastServer(DatagramProtocol):

    global GLOBAL_DICT

    def __init__(self, app, multi_ip):
        self.app = app
        self.multi_ip = multi_ip

    def startProtocol(self):
        """Called after protocol has started listening."""

        # Set the TTL>1 so multicast will cross router hops:
        self.transport.setTTL(5)
        # Join a specific multicast group:
        self.transport.joinGroup(self.multi_ip)

        print("Init multicast")

    def datagramReceived(self, datagram, address):
        """Si réception, met à jour la variable globale"""

        global GLOBAL_DICT

        # #print("Datagram %s received from %s" % (datagram, address))
        # data est un dict ou None
        data = datagram_to_dict(datagram)

        if data:
            if "image_size" in data:
                GLOBAL_DICT["image_size"] = data["image_size"]

            if "image_pos" in data:
                GLOBAL_DICT["image_pos"] = data["image_pos"]
        else:
            GLOBAL_DICT = { "image_size": 1,
                            "image_pos": (0, 0),
                            "freq": 1}


class MyTCPServer(Protocol):
    """
    Attribut de class: nb_protocol
    Un protocol par client connecté,
    chaque protocol est  une  instance de cette class indépendante
    """

    global GLOBAL_DICT
    nb_protocol = 0

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

        global GLOBAL_DICT

        # #print("Data received:", data)
        # data est un dict ou None
        data = datagram_to_dict(data)

        if data:
            if "image_size" in data:
                GLOBAL_DICT["image_size"] = data["image_size"]

            if "image_pos" in data:
                GLOBAL_DICT["image_pos"] = data["image_pos"]
        else:
            GLOBAL_DICT = { "image_size": 1,
                            "image_pos": (0, 0),
                            "freq": 1}


class MyTCPServerFactory(Factory):

    # This will be used by the default buildProtocol to create new protocols:
    protocol = MyTCPServer

    def __init__(self, app, quote=None):
        self.app = app
        print("MyTCPServerFactory créé")


class TextureAccessibleWidget(Widget):
    """class appelé uniquement par le kv
        self d'ici est <TextureAccessibleWidget> dans le kv
    GLOBAL_DICT est la solution simple trouvée pour échanger entre ici et
    MyMulticastServer
    classs pas Accessible du tout, puisque j'utilise une variable globale
    pour les échanges: GLOBAL_DICT
    """

    texture = ObjectProperty(None)
    global GLOBAL_DICT

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        Clock.schedule_once(self.texture_init, 0)

        # Boucle permanente
        self.freq = 1
        self.event = None
        self.clock_schedule()

    def clock_schedule(self):

        self.freq = GLOBAL_DICT["freq"]
        if self.freq != 0:
            tempo = 1 / self.freq
        else:
            tempo = 1

        self.event = Clock.schedule_interval(self.update, tempo)

    def texture_init(self, *args):
        self.texture = self.canvas.children[-1].texture

        self.size_ori = self.texture.size
        self.width = self.size_ori[0] * 0.6
        self.height = self.size_ori[1] * 0.6

    def update(self, dt):

        global GLOBAL_DICT

        # Si il y a eu changement de fréquence
        freq = GLOBAL_DICT["freq"]

        if freq != self.freq:
            self.freq = freq
            print("Fréquence:", freq)
            self.clock_schedule()

        # Size
        k = GLOBAL_DICT["image_size"]
        self.width  = self.size_ori[0] * k * 0.6
        self.height = self.size_ori[1] * k * 0.6

        # Position
        pos = GLOBAL_DICT["image_pos"]
        self.pos = (pos[0] * 200, pos[1] * 200)


class Server(Screen):
    """Le seul écran défini dans le kv"""

    def __init__(self, app, **kwargs):

        super().__init__(**kwargs)
        self.app = app


class ServerKivyApp(App):
    """Pas de __init__() dans cette class ...App"""

    global GLOBAL_DICT

    def build(self):
        """Exécuté après build_config, construit l' écran
        Le self d'ici est le self.app des autres class"""

        return Server(self)

    def build_config(self, config):
        """Excécuté en premier.
        Si le fichier *.ini n'existe pas,
                il est créé avec ces valeurs par défaut.
        Il s'appelle comme le kv mais en ini
        Si il manque seulement des lignes, il ne fait rien !
        """

        print("Création du fichier *.ini si il n'existe pas")

        config.setdefaults('network',
                            { 'multi_ip': '228.0.0.5',
                              'multi_port': 18888,
                              'tcp_port': 8000,
                              'cast': 'multi',
                              'freq': 60,
                              'tcp_ip': '192.168.0.105'})

        config.setdefaults('kivy',
                            { 'log_level': 'debug',
                              'log_name': 'apprendre-kivy_%y-%m-%d_%_.txt',
                              'log_dir': '/sdcard',
                              'log_enable': '1'})

        config.setdefaults('postproc',
                            { 'double_tap_time': 250,
                              'double_tap_distance': 20})

        print("self.config peut maintenant être appelé")

    def build_settings(self, settings):
        """Construit l'interface de l'écran Options, pour apprendre_kivy seul,
        les réglages Kivy sont par défaut.

        Cette méthode est appelée par app.open_settings() dans .kv,
        donc si Options est cliqué !
        """

        print("Construction de l'écran Options")

        data = """[
                    {"type": "title", "title":"Configuration du réseau"},

                    {"type": "string",
                      "title": "Multicast IP",
                      "desc": "IP = 228.0.0.5",
                      "section": "network", "key": "multi_ip"},

                    {"type": "numeric",
                      "title": "Multicast Port",
                      "desc": "Port = 18888",
                      "section": "network", "key": "multi_port"},

                    {"type": "numeric",
                      "title": "TCP Port",
                      "desc": "Port = 8000",
                      "section": "network", "key": "tcp_port"},

                    {"type": "string",
                      "title": "Cast",
                      "desc": "multi ou tcp",
                      "section": "network", "key": "cast"},

                    {"type": "numeric",
                      "title": "Fréquence",
                      "desc": "Fréquence entre 1 et 60 Hz",
                      "section": "network", "key": "freq"},

                    {"type": "string",
                      "title": "TCP IP",
                      "desc": "IP = 192.168.0.105",
                      "section": "network", "key": "tcp_ip"}
                   ]"""

        # self.config est le config de build_config
        settings.add_json_panel('ServerKivy', self.config, data=data)

    def on_start(self):
        """Exécuté apres build()
        Lancement du Multicast ou du TCP
        """

        global GLOBAL_DICT

        freq = int(self.config.get('network', 'freq'))
        GLOBAL_DICT["freq"] = freq
        print("Fréquence de réception:", freq)
        self.cast = self.config.get('network', 'cast')

        if self.cast == 'multi':
            # Multicast
            multi_ip = self.config.get('network', 'multi_ip')
            multi_port = int(self.config.get('network', 'multi_port'))
            reactor.listenMulticast(multi_port,
                                    MyMulticastServer(self, multi_ip),
                                    listenMultiple=True)
            aaaa = "Multicast server started: ip = {} port = {}"
            print(aaaa.format(multi_ip, multi_port))

        elif self.cast == 'tcp':
            # TCP
            tcp_port = int(self.config.get('network', 'tcp_port'))
            endpoint = TCP4ServerEndpoint(reactor, tcp_port)
            endpoint.listen(MyTCPServerFactory(self))
            print(dir(endpoint))
            print("TCP server started sur le port {}".format(tcp_port))

        else:
            # Si erreur de saisie, forcé en multi
            self.config.set('network', 'cast', 'multi')
            self.config.write()
            self.cast = 'multi'
            self.on_start()

    def on_config_change(self, config, section, key, value):
        """Si modification des options, fonction appelée automatiquement
        menu = self.screen_manager.get_screen("Main")
        """

        if config is self.config:  # du joli python rigoureux
            token = (section, key)

            # Frequency
            if token == ('network', 'freq'):
                GLOBAL_DICT["freq"] = int(token[1])

            # Cast
            if token == ('network', 'cast'):
                print("Nouveau réseau:", value)
                self.cast = value
                # relance du réseau
                # TODO BUG les 2 réseaux vont tourner ensemble
                self.on_start()

    def do_quit(self):

        print("Je quitte proprement")

        # Stop de Twisted
        if reactor.running:
            reactor.stop()

        # Kivy
        ServerKivyApp.get_running_app().stop()

        # Extinction forcée de tout, si besoin
        os._exit(0)


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
        print("Ajouter ast dans les import")
        msg = dec

    if isinstance(msg, dict):
        return msg
    else:
        print("Message reçu: None")
        return None


if __name__ == '__main__':

    ServerKivyApp().run()
