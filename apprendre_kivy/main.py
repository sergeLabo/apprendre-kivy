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
Application avec 2 écrans:
    - Main: image, button
    - Screen1: slider
"""


__version__ = '0.07'


# De la bibliothèque standard, ne pas les ajouter dans buildozer.spec
import os
import json
import socket
from time import sleep

# Pour twisted
from kivy.support import install_twisted_reactor
install_twisted_reactor()
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, Factory, DatagramProtocol
from twisted.internet.protocol import ReconnectingClientFactory


# Pour kivy
import kivy
kivy.require('1.11.1')
from kivy.core.window import Window
# Les 3 lignes ci-dessous sont à commenter pour buildozer
# L'écran de mon tél fait 1280*720
# #k = 1.0
# #WS = (int(1280*k), int(720*k))
# #Window.size = WS

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.properties import  NumericProperty, ReferenceListProperty,\
                             ObjectProperty, BooleanProperty,\
                             ListProperty
from kivy.vector import Vector
from kivy.clock import Clock


# Récupération de l'ip locale pour l'envoyer à tous les clients en multicast
def get_my_LAN_ip():
    try:
        sok = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sok.connect(("8.8.8.8", 80))
        ip = sok.getsockname()[0]
        sok.close()
    except:
        ip = "127.0.0.1"
    return ip

LAN_IP = get_my_LAN_ip()
print("LAN IP =", LAN_IP)


class MyTcpClient(Protocol):
    """Un client TCP seul"""

    def __init__(self, app):
        """self.app:
        Ce mot clé se réferre toujours à l'instance de votre application kivy,
        soit ApprendreKivyApp()
        Permet d'échager avec les autres class.
        """

        self.app = app

        # Boucle infinie
        freq = int(self.app.config.get('network', 'freq'))
        if freq != 0:
            self.tempo = 1 / freq
        else:
            self.tempo = 1
        self.tictac = Clock.schedule_interval(self.update, self.tempo)
        print("Un protocol client créé")

    def update(self, dt):
        """Appelé par Clock, donc tourne tout le temps.
        Va récupérer les valeurs des sliders de Screen1 en utilisant le
        self.app
        """

        scr1 = self.app.screen_manager.get_screen("Screen1")
        data = scr1.create_message()
        # #print("Envoi de:", data)
        self.transport.write(data)


class MyTcpClientFactory(ReconnectingClientFactory):
    """L'usine de clients TCP avec reconnexion.
    Un maxDelay existe voir doc twisted
    """

    def __init__(self, app):
        """self.app:
        Ce mot clé se réferre toujours à l'instance de votre application kivy,
        soit ApprendreKivyApp()
        Permet d'échager avec les autres class.
        """
        self.app = app

    # 4 méthodes pour réaliser les reconnexions
    def startedConnecting(self, connector):
        print("Essai de connexion ...")

    def buildProtocol(self, addr):
        print("Connecté à {}".format(addr))
        print("Resetting reconnection delay")
        self.resetDelay()
        return MyTcpClient(self.app)

    def clientConnectionLost(self, connector, reason):
        print("Lost connection.  Reason:", reason)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        print("Connection failed. Reason:", reason)
        ReconnectingClientFactory.clientConnectionFailed(self,connector,reason)


class MulticastClient(DatagramProtocol):
    """Avantge du multicast: tout le monde envoie et reçoit sans IP à définir,
    Inconvénient: charge le routeur

    De la doc:
    def datagramReceived(self, datagram, address):
        print("Datagram %s received from %s" % (datagram, address))
        if datagram == "Client: Ping":
            # Rather than replying to the group multicast address, we send the
            # reply directly (unicast) to the originating port:
            self.transport.write(("Server: Pong").encode("utf-8"), address)
        """

    def __init__(self, app, multi_ip):
        """self.app:
        Ce mot clé se réferre toujours à l'instance de votre application.
        Permet d'échager avec les autres class.
        """
        self.app = app

        # Boucle d'envoi
        self.tictac = None

        # Adresse multicast
        self.multi_ip = self.app.config['network']['multi_ip']
        self.multi_port = int(self.app.config['network']['multi_port'])
        self.address = self.multi_ip, self.multi_port

    def startProtocol(self):
        """Called after protocol has started listening."""

        # Join a specific multicast group:
        self.transport.joinGroup(self.multi_ip)

        # Boucle infinie
        freq = int(self.app.config.get('network', 'freq'))
        if freq != 0:
            self.tempo = 1 / freq
        else:
            self.tempo = 1
        self.tictac = Clock.schedule_interval(self.update, self.tempo)

    def update(self, dt):
        """Appelé par Clock, donc tourne tout le temps.
        Va récupérer les valeurs des sliders de Screen1 en utilisant le
        self.app
        """

        scr1 = self.app.screen_manager.get_screen("Screen1")
        data = scr1.create_message()
        # #print("Envoi de:", data)
        self.transport.write(data,self.address)


class MainScreen(Screen):
    """Ecran principal, l'appli s'ouvre sur cet écran
    root est le parent de cette classe dans la section <MainScreen> du kv
    """

    def __init__(self, **kwargs):
        """Vieux python 2 !
        super(MainScreen, self).__init__(**kwargs)
        plus simple en python 3 !
        """

        super().__init__(**kwargs)
        print("Initialisation du Screen MainScreen ok")


class Screen1(Screen):
    """root est le parent de cette classe dans la section <Screen1> du kv"""

    def __init__(self, **kwargs):
        """Vieux python 2 !
        super(MainScreen, self).__init__(**kwargs)
        plus simple en python 3 !
        """

        super().__init__(**kwargs)
        self.img_size = 1
        self.pos_vert = 0
        self.pos_hori = 0

        print("Initialisation du Screen Screen1 ok")

    def do_slider(self, iD, instance, value):
        """Called if slider change."""

        print("slider", iD, value)

        if iD == "img_size":
            self.img_size = value

        if iD == "pos_vert":
            self.pos_vert = value

        if iD == "pos_hori":
            self.pos_hori = value

    def create_message(self):
        """Le message est un dict, puis json.dumps,
        puis encode pour avoir des bytes
        dict avec keys:
                "kivy ip": "228.0.0.5"
                "image size": 1.0
                "image position": (100, 200)
        """

        data_dict = {   "kivy_ip": LAN_IP,
                        "image_size": self.img_size,
                        "image_pos": (self.pos_hori, self.pos_vert)}

        data = json.dumps(data_dict).encode("utf-8")

        return data


"""
Variable globale qui définit les écrans
L'écran de configuration est toujours créé par défaut
Il suffit de créer un bouton d'accès
Les class appelées (MainScreen, Screen1) sont placées avant
"""
SCREENS = { 0: (MainScreen, "Main"),
            1: (Screen1, "Screen1")}


class ApprendreKivyApp(App):
    """Construction de l'application. Exécuté par if __name__ == '__main__':,
    app est le parent de cette classe dans kv
    """

    def build(self):
        """Exécuté après build_config, construit les écrans"""

        # Création des écrans
        self.screen_manager = ScreenManager()
        for i in range(len(SCREENS)):
            # Pour chaque écran, équivaut à
            # self.screen_manager.add_widget(MainScreen(name="Main"))
            self.screen_manager.add_widget(SCREENS[i][0](name=SCREENS[i][1]))

        return self.screen_manager

    def on_start(self):
        """Exécuté apres build()
        Pas de reactor.run()
        install_twisted_reactor() du début du script semble le faire !

        Lancement du Multicast ou du TCP
        """

        self.cast = self.config.get('network', 'cast')
        if reactor.running:
            reactor.stop()
            sleep(1)

        if self.cast == 'multi':
            # Multicast
            multi_ip = self.config.get('network', 'multi_ip')
            multi_port = int(self.config.get('network', 'multi_port'))
            # dans MulticastClient(self, ... self est app !
            reactor.listenMulticast(multi_port,
                                    MulticastClient(self, multi_ip),
                                    listenMultiple=True)
            aaaa = "Multicast server started: ip = {} port = {}"
            print(aaaa.format(multi_ip, multi_port))

        elif self.cast == 'tcp':
            # TCP
            tcp_port = int(self.config.get('network', 'tcp_port'))
            host = self.config.get('network', 'tcp_ip')
            # On appelle:
            # class TCPServerFactory(Factory):
            #     def __init__(self, app):
            #         ....
            # app est en fait le self de cette class ApprendreKivyApp()
            reactor.connectTCP(host, tcp_port, MyTcpClientFactory(self))
            print("TCP server started sur le port {}".format(tcp_port))

        else:
            # Si erreur de saisie, forcé en multi
            # TODO revoir la doc si saisie des options contraignable !
            self.config.set('network', 'cast', 'multi')
            self.config.write()
            self.cast = 'multi'
            self.on_start()

    def build_config(self, config):
        """Excécuté en premier (ou après __init__()).
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
        Les réglages Kivy sont par défaut.
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
        settings.add_json_panel('ApprendreKivy', self.config, data=data)

    def on_config_change(self, config, section, key, value):
        """Si modification des options, fonction appelée automatiquement
        menu = self.screen_manager.get_screen("Main")
        """

        if config is self.config:  # du joli python rigoureux
            token = (section, key)

            # Frequency
            if token == ('network', 'freq'):
                # TODO recalcul tempo
                print("Nouvelle fréquence:", value)

            # Cast
            if token == ('network', 'cast'):
                print("Nouveau réseau:", value)
                self.cast = value
                # relance du réseau
                self.on_start()

    def go_mainscreen(self):
        """Retour au menu principal depuis les autres écrans."""

        # TODO Ajouter un bouton de retour
        self.screen_manager.current = ("Main")

    def do_quit(self):

        print("Je quitte proprement")

        # Stop de Twisted
        if reactor.running:
            reactor.stop()

        # Kivy
        ApprendreKivyApp.get_running_app().stop()

        # Extinction forcée de tout, si besoin
        os._exit(0)



if __name__ == '__main__':
    """L'application s'appelle apprendrekivy
    d'où
    la class
        ApprendreKivyApp()
    les fichiers:
        apprendrekivy.kv
        apprendrekivy.ini
    """

    ApprendreKivyApp().run()

# TODO à revoir pour réception
"""
    def handle_message(self, msg):
        '''Pour le TCP'''

        msg = msg.decode('utf-8')
        print("received:  {}\n".format(msg))

        if msg == "ping":
            msg = "Pong"
        if msg == "plop":
            msg = "Kivy Rocks!!!"
        print("responded: {}\n".format(msg))
        return msg.encode('utf-8')
"""
