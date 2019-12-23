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
    - Main: un serveur TCP est lancé, avec 1 menu
    - Screen1: envoi réception
"""


__version__ = '0.001'


import os
import json


from kivy.support import install_twisted_reactor
install_twisted_reactor()
from twisted.internet import reactor
from twisted.internet import protocol


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
from kivy.uix.widget import Widget
from kivy.properties import  NumericProperty, ReferenceListProperty,\
                             ObjectProperty, BooleanProperty,\
                             ListProperty
from kivy.vector import Vector
from kivy.clock import Clock


class MainScreen(Screen):
    """Ecran principal, l'appli s'ouvre sur cet écran
    root est le parent de cette classe dans la section <MainScreen> du kv
    """

    # Attributs de class
    bgcolor = ListProperty([0,0,0])

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        # Construit le jeu, le réseau, tourne tout le temps
        scr_manager = self.get_screen_manager()
        print("Initialisation du Screen MainScreen ok")

    def get_screen_manager(self):
        return ApprendreKivyApp.get_running_app().screen_manager


class Screen1(Screen):
    """root est le parent de cette classe dans la section <Screen1> du kv
    """

    def __init__(self, **kwargs):
        super(Screen1, self).__init__(**kwargs)
        self.tictac = Clock.schedule_interval(self.update, 0.016)
        print("Initialisation du Screen Screen1 ok")

    def update(self, dt):
        pass

    def do_slider(self, iD, instance, value):
        """Called if slider change."""

        print("slider", iD, value)


class TwistedServer(protocol.Protocol):
    def dataReceived(self, data):
        response = self.factory.app.handle_message(data)
        if response:
            self.transport.write(response)


class TwistedServerFactory(protocol.Factory):
    protocol = TwistedServer

    def __init__(self, app):
        self.app = app


# Variable globale qui définit les écrans
# L'écran de configuration est toujours créé par défaut
# Il suffit de créer un bouton d'accès
SCREENS = { 0: (MainScreen, "Main"), 1: (Screen1, "Screen1")}


class ApprendreKivyApp(App):
    """Construction de l'application. Exécuté par __main__,
    app est le parent de cette classe dans kv.
    """

    def build(self):
        """Exécuté en premier après run()"""

        # Création des écrans
        self.screen_manager = ScreenManager()
        for i in range(len(SCREENS)):
            # Pour chaque écran, équivaut à
            # self.screen_manager.add_widget(MainScreen(name="Main"))
            self.screen_manager.add_widget(SCREENS[i][0](name=SCREENS[i][1]))

        return self.screen_manager

    def on_start(self):
        """Exécuté apres build()"""

        print("server started")
        reactor.listenTCP(8000, TwistedServerFactory(self))

    def handle_message(self, msg):
        msg = msg.decode('utf-8')
        print("received:  {}\n".format(msg))

        if msg == "ping":
            msg = "Pong"
        if msg == "plop":
            msg = "Kivy Rocks!!!"
        print("responded: {}\n".format(msg))
        return msg.encode('utf-8')

    def build_config(self, config):
        """Si le fichier *.ini n'existe pas,
                il est créé avec ces valeurs par défaut.
        Il s'appelle comme le kv mais en ini
        Si il manque seulement des lignes, il ne fait rien !
        """

        config.setdefaults('network',
                            { 'multi_ip': '228.0.0.5',
                              'multi_port': '18888',
                              'tcp_port': '8000',
                              'freq': '60'})

        config.setdefaults('kivy',
                            { 'log_level': 'debug',
                              'log_name': 'apprendre-kivy_%y-%m-%d_%_.txt',
                              'log_dir': '/sdcard',
                              'log_enable': '1'})

        config.setdefaults('postproc',
                            { 'double_tap_time': 250,
                              'double_tap_distance': 20})

    def build_settings(self, settings):
        """Construit l'interface de l'écran Options, pour training_kivy seul,
        Kivy est par défaut, appelé par app.open_settings() dans .kv
        """

        data = """[{"type": "title", "title":"Configuration du réseau"},
                      {"type": "numeric",
                      "title": "Fréquence",
                      "desc": "Fréquence entre 1 et 60 Hz",
                      "section": "network", "key": "freq"}
                   ]"""

        # self.config est le config de build_config
        settings.add_json_panel('training_kivy', self.config, data=data)

    def on_config_change(self, config, section, key, value):
        """Si modification des options, fonction appelée automatiquement
        """

        freq = int(self.config.get('network', 'freq'))
        menu = self.screen_manager.get_screen("Main")

        if config is self.config:
            token = (section, key)

            # If frequency change
            if token == ('network', 'freq'):
                # TODO recalcul tempo
                print("Nouvelle fréquence", freq)

    def go_mainscreen(self):
        """Retour au menu principal depuis les autres écrans."""

        #if touch.is_double_tap:
        self.screen_manager.current = ("Main")

    def do_quit(self):

        print("Je quitte proprement")

        # Stop propre de Clock.schedule_interval
        net = self.screen_manager.get_screen("Screen1")
        net.tictac.cancel()

        # Stop de Twisted
        reactor.stop()

        # Kivy
        ApprendreKivyApp.get_running_app().stop()

        # Extinction forcée de tout, si besoin
        os._exit(0)


if __name__ == '__main__':
    ApprendreKivyApp().run()
