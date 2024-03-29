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
Application avec 3 écrans:
    - Main: image, button
    - Screen1: avec des slider
    - Screen2: Scatter qui gère le tactile

Simulation du dpi
    KIVY_METRICS_FONTSCALE=1.2 python3 main.py

"""

__version__ = '0.26'

# De la bibliothèque standard, ne pas les ajouter dans buildozer.spec
import os
import json
import socket
from time import sleep
from glob import glob
from os.path import join, dirname

# Pour twisted
# ajouter twisted dans les requirements de buildozer.spec
from kivy.support import install_twisted_reactor
install_twisted_reactor()
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, Factory, DatagramProtocol
from twisted.internet.protocol import ReconnectingClientFactory

# Pour kivy
# ajouter kivy dans les requirements de buildozer.spec
import kivy
kivy.require('1.11.1')

from kivy.core.window import Window
# Les 3 lignes ci-dessous sont à commenter pour buildozer
# L'écran de mon tél fait 1280*720
k = 1.0
WS = (int(1280*k), int(720*k))
Window.size = WS

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.logger import Logger
# Pour appliquer le tactile multitouch
from kivy.uix.scatter import Scatter


class MyTcpClient(Protocol):
    """Un client TCP seul"""

    def __init__(self, app):
        """app:
        Ce mot clé se réferre toujours à l'instance de votre application kivy,
        soit ApprendreKivyApp()
        Permet d'échanger avec les autres class.
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

        # Ecran en cours
        scr_name = self.app.screen_manager.current_screen.name
        scr = self.app.screen_manager.get_screen(scr_name)

        if scr.name != "Main":
            data = scr.create_message()
        else:
            data = json.dumps({}).encode("utf-8")

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


class Picture(Scatter):
    """Scatter capture et applique le tactile"""

    # Le kv appelle cet attribut avec root.source
    # C'est un attribut de class, obligatoire pour être appelé
    source = StringProperty(None)


class MulticastClient(DatagramProtocol):
    """Avantage du multicast: tout le monde envoie et reçoit sans IP à définir,
    Inconvénient: charge le routeur
    """

    def __init__(self, app, multi_ip):
        """self.app:
        Ce mot clé se réferre toujours à l'instance de votre application.
        Permet d'échanger avec les autres class.
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

        # Ecran en cours
        scr_name = self.app.screen_manager.current_screen.name
        scr = self.app.screen_manager.get_screen(scr_name)

        if scr.name != "Main":
            data = scr.create_message()
        else:
            data = json.dumps({}).encode("utf-8")

        self.transport.write(data, self.address)


class MainScreen(Screen):
    """Ecran principal, l'appli s'ouvre sur cet écran
    root est le parent de cette classe dans la section <MainScreen> du kv
    """

    # Attribut de class, obligatoire poue appeler root.titre dans kv
    titre = StringProperty("toto")

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        self.titre = "Apprendre Kivy"
        print("Initialisation du Screen MainScreen ok")


class Screen1(Screen):
    """root est le parent de cette classe dans la section <Screen1> du kv"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        self.img_size = 1
        self.pos_vert = 0
        self.pos_hori = 0

        print("Initialisation du Screen Screen1 ok")

    def do_slider(self, iD, instance, value):
        """Called if slider change."""

        if iD == "img_size":
            # Le slider dans kv à l'id: img_size
            self.img_size = value

        if iD == "pos_vert":
            self.pos_vert = value

        if iD == "pos_hori":
            self.pos_hori = value

    def create_message(self):
        """Le message est un dict, puis json.dumps,
        puis encode pour avoir des bytes.
        Dans cet écran, des coefficients sont envoyés, et non des pixels.
        """

        data_dict = {   "ip": LAN_IP,
                        "unit": "coeff",
                        "image_size": self.img_size,
                        "image_pos": (self.pos_hori, self.pos_vert)}

        data = json.dumps(data_dict).encode("utf-8")

        return data

    def go_to_screen_2(self):
        screen2 = self.manager.get_screen("screen2")


class Screen2(Screen):
    """Déplacement, resize, rotation d'une image avec le tactile
    La class du kv de cette class appelle Picture(Scatter)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("Initialisation du Screen Screen2:")

        # Toules les images chargées dans un dict
        self.pictures = {}

        # Get any files into images directory
        curdir = dirname(__file__)
        n = 0
        for filename in glob(join(curdir, 'images', '*')):
            try:
                # load the image
                self.pictures[n] = Picture(source=filename, rotation=0)

                # add to the main field
                self.add_widget(self.pictures[n])

                n += 1

            except Exception as e:
                Logger.exception('Pictures: Unable to load {}'.format(filename))

    def create_message(self):

        if self.pictures[0]:
            img_scale = self.pictures[0].scale
            image_size = (  self.pictures[0].width * img_scale,
                            self.pictures[0].height * img_scale )

            pos_hori, pos_vert = (  self.pictures[0].pos[0],
                                    self.pictures[0].pos[1])

            angle = self.pictures[0].rotation

            data_dict = {   "unit": "pixel",
                            "image_size": image_size,
                            "image_pos": (pos_hori, pos_vert),
                            "angle": angle}

        else:
            data_dict = {}

        return json.dumps(data_dict).encode("utf-8")


# Variable globale qui définit les écrans
# L'écran de configuration est toujours créé par défaut
# Il suffit de créer un bouton d'accès
# Les class appelées (MainScreen, Screen1) sont placées avant
SCREENS = { 0: (MainScreen, "Main"),
            1: (Screen1, "Screen1"),
            2: (Screen2, "Screen2")}


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

        # le reactor tourne en continu, il ne faut pas l'arrêter

        if self.cast == 'multi':
            # Multicast
            self.multi_ip = self.config.get('network', 'multi_ip')
            self.multi_port = int(self.config.get('network', 'multi_port'))
            # Le self d'ici est app de MulticastClient(self, app, ...
            reactor.listenMulticast(self.multi_port,
                                    MulticastClient(self, self.multi_ip),
                                    listenMultiple=True)
            aaaa = "Multicast client started: ip = {} port = {}"
            print(aaaa.format(self.multi_ip, self.multi_port))

        elif self.cast == 'tcp':
            # TCP
            self.tcp_port = int(self.config.get('network', 'tcp_port'))
            self.tcp_ip = self.config.get('network', 'tcp_ip')
            # On appelle:
            # class TCPServerFactory(Factory):
            #     def __init__(self, app):
            #         ....
            # app est en fait le self de cette class ApprendreKivyApp()
            reactor.connectTCP(self.tcp_ip, self.tcp_port, MyTcpClientFactory(self))
            print("TCP Client started ip: {} port: {}".format(self.tcp_ip,
                                                              self.tcp_port))

        else:
            # Si erreur de saisie, forcé en multi
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

            # multi_ip = 228.0.0.5
            if token == ('network', 'multi_ip'):
                print("multi_ip", value)
                self.multi_ip = value

            # Frequency
            if token == ('network', 'freq'):
                # TODO recalcul tempo
                print("Nouvelle fréquence:", value)

            # Cast
            if token == ('network', 'cast'):
                print("Nouveau réseau:", value)
                self.cast = value
                # relance du réseau
                # TODO BUG les 2 réseaux vont tourner ensemble
                self.on_start()

            # multi_port = 18888
            if token == ('network', 'multi_port'):
                print("multi_port", value)
                self.multi_port = value

            # tcp_port = 8000
            if token == ('network', 'tcp_port'):
                print("tcp_port", value)
                self.tcp_port = value

            # tcp_ip = 192.168.0.105
            if token == ('network', 'tcp_ip'):
                print("tcp_ip", value)
                self.tcp_ip = value

    def go_mainscreen(self):
        """Retour au menu principal depuis les autres écrans."""

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
