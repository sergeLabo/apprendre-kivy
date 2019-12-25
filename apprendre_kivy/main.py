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
import socket

from kivy.support import install_twisted_reactor
install_twisted_reactor()
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, Factory,\
                                      ClientFactory, DatagramProtocol


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


# Récupération de l'ip locale pour l'envoyer à tous les clients en multicast
def get_my_LAN_ip():
    sok = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sok.connect(("8.8.8.8", 80))
    ip = sok.getsockname()[0]
    sok.close()
    print("LAN Ip =", ip)
    return ip
LAN_IP = get_my_LAN_ip()


class TCPServer(Protocol):
    def dataReceived(self, data):
        response = self.factory.app.handle_message(data)
        if response:
            self.transport.write(response)


class TCPServerFactory(Factory):
    protocol = TCPServer

    def __init__(self, app):
        self.app = app


class EchoClient(Protocol):
    def connectionMade(self):
        self.factory.app.on_connection(self.transport)

    def dataReceived(self, data):
        self.factory.app.print_message(data.decode('utf-8'))


class EchoClientFactory(ClientFactory):
    protocol = EchoClient

    def __init__(self, app):
        self.app = app

    def startedConnecting(self, connector):
        # #self.app.print_message('Started to connect.')
        print('Started to connect.')

    def clientConnectionLost(self, connector, reason):
        # #self.app.print_message('Lost connection.')
        print('Lost connection.')

    def clientConnectionFailed(self, connector, reason):
        # #self.app.print_message('Connection failed.')
        print('Connection failed.')


class MulticastServer(DatagramProtocol):

    def __init__(self, app, multi_ip):
        self.app = app
        self.multi_ip = multi_ip
        self.tictac = None

    def startProtocol(self):
        """Called after protocol has started listening."""

        # Set the TTL>1 so multicast will cross router hops:
        self.transport.setTTL(5)
        # Join a specific multicast group:
        self.transport.joinGroup(self.multi_ip)

        # Boucle
        self.tictac = Clock.schedule_interval(self.update, 1)  # 0.016)

    def datagramReceived(self, datagram, address):
        print("Datagram %s received from %s" % (datagram, address))
        if datagram == "Client: Ping":
            # Rather than replying to the group multicast address, we send the
            # reply directly (unicast) to the originating port:

            self.transport.write(("Server: Pong").encode("utf-8"), address)

    def update(self, dt):
        data = self.app.get_slider()
        address = ("228.0.0.5", 18888)
        self.transport.write(data, address)


class MainScreen(Screen):
    """Ecran principal, l'appli s'ouvre sur cet écran
    root est le parent de cette classe dans la section <MainScreen> du kv
    """

    # Attributs de class
    bgcolor = ListProperty([0,0,0])

    def __init__(self, **kwargs):
        # Vieux python 2 ! super(MainScreen, self).__init__(**kwargs)
        # Simple en python 3
        super().__init__(**kwargs)

        # Construit le jeu, le réseau, tourne tout le temps
        scr_manager = self.get_screen_manager()
        print("Initialisation du Screen MainScreen ok")

    def get_screen_manager(self):
        return ApprendreKivyApp.get_running_app().screen_manager


class Screen1(Screen):
    """root est le parent de cette classe dans la section <Screen1> du kv
    """

    def __init__(self, **kwargs):
        # Vieux python 2 !
        # super(Screen1, self).__init__(**kwargs)
        # Simple en python 3
        super().__init__(**kwargs)
        self.img_size = 1

        print("Initialisation du Screen Screen1 ok")

    def do_slider(self, iD, instance, value):
        """Called if slider change."""

        print("slider", iD, value)
        if iD == "un_un":
            self.img_size = value

# Variable globale qui définit les écrans
# L'écran de configuration est toujours créé par défaut
# Il suffit de créer un bouton d'accès
# Les class appelées (MainScreen, Screen1) sont placées avant
SCREENS = { 0: (MainScreen, "Main"),
            1: (Screen1, "Screen1")}


class ApprendreKivyApp(App):
    """Construction de l'application. Exécuté par __main__,
    app est le parent de cette classe dans kv.

    def __init__(self):
        self.cast = None
        # Pour savoir quel réseau tourne
        self.tcp = None
        self.multi = None
    """

    connection = None
    textbox = None
    label = None

    def build(self):
        """Exécuté après build_config
        Construit les écrans
        """

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
        """

        self.cast = self.config.get('network', 'cast')
        if reactor.running:
            reactor.stop()
            sleep(1)

        if self.cast == 'multi':
            # Multicast
            multi_ip = self.config.get('network', 'multi_ip')
            multi_port = int(self.config.get('network', 'multi_port'))
            reactor.listenMulticast(multi_port,
                                    MulticastServer(self, multi_ip),
                                    listenMultiple=True)
            print("Multicast server started: ip = {} port = {}".format(multi_ip, multi_port))

        if self.cast == 'tcp':
            # TCP
            tcp_port = int(self.config.get('network', 'tcp_port'))
            reactor.listenTCP(tcp_port, TCPServerFactory(self))
            print("TCP server started sur le port {}".format(tcp_port))

    def handle_message(self, msg):
        """Pour le TCP"""

        msg = msg.decode('utf-8')
        print("received:  {}\n".format(msg))

        if msg == "ping":
            msg = "Pong"
        if msg == "plop":
            msg = "Kivy Rocks!!!"
        print("responded: {}\n".format(msg))
        return msg.encode('utf-8')

    def get_slider(self):
        scr1 = self.screen_manager.get_screen("Screen1")
        img_size = scr1.img_size
        data_dict = {"image size": img_size}
        data = json.dumps(data_dict).encode("utf-8")
        return data

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
                              'cast': 'tcp',
                              'freq': 60})

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
                      "section": "network", "key": "freq"}
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

        #if touch.is_double_tap:
        self.screen_manager.current = ("Main")

    def do_quit(self):

        print("Je quitte proprement")

        # ## Stop propre de Clock.schedule_interval
        # #net = self.screen_manager.get_screen("Screen1")
        # #net.tictac.cancel()

        # Stop de Twisted
        if reactor.running:
            reactor.stop()

        # Kivy
        ApprendreKivyApp.get_running_app().stop()

        # Extinction forcée de tout, si besoin
        os._exit(0)



if __name__ == '__main__':
    ApprendreKivyApp().run()

    """
['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__events__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__proxy_getter', '__proxy_setter', '__pyx_vtable__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setstate__', '__sizeof__', '__str__', '__subclasshook__', '_app_directory', '_app_name', '_app_settings', '_app_window', '_get_user_data_dir', '_install_settings_keys', '_kwargs_applied_init', '_on_config_change', '_on_keyboard_settings', '_running_app', '_user_data_dir', 'apply_property', 'bind', 'build', 'build_config', 'build_settings', 'built', 'cast', 'close_settings', 'config', 'create_property', 'create_settings', 'destroy_settings', 'directory', 'dispatch', 'dispatch_children', 'dispatch_generic', 'display_settings', 'do_quit', 'events', 'fbind', 'funbind', 'get_application_config', 'get_application_icon', 'get_application_name', 'get_property_observers', 'get_running_app', 'getter', 'go_mainscreen', 'handle_message', 'icon', 'is_event_type', 'kv_directory', 'kv_file', 'load_config', 'load_kv', 'name', 'on_config_change', 'on_icon', 'on_pause', 'on_resume', 'on_start', 'on_stop', 'on_title', 'open_settings', 'options', 'properties', 'property', 'proxy_ref', 'register_event_type', 'root', 'root_window', 'run', 'screen_manager', 'setter', 'settings_cls', 'stop', 'title', 'uid', 'unbind', 'unbind_uid', 'unregister_event_types', 'use_kivy_settings', 'user_data_dir']

['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__implemented__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__name__', '__ne__', '__new__', '__providedBy__', '__provides__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_cancelCallLater', '_cancellations', '_checkProcessArgs', '_childWaker', '_disconnectSelectable', '_doIterationInThread', '_doReadOrWrite', '_doSelectInThread', '_eventTriggers', '_exitSignal', '_handleSignals', '_initThreadPool', '_initThreads', '_insertNewDelayedCalls', '_installSignalHandlers', '_interleave', '_internalReaders', '_justStopped', '_lock', '_mainLoopShutdown', '_moveCallLaterSooner', '_nameResolver', '_newTimedCalls', '_pendingTimedCalls', '_preenDescriptorsInThread', '_process_Failure', '_process_Notify', '_reallyStartRunning', '_registerAsIOThread', '_removeAll', '_sendToMain', '_sendToThread', '_started', '_startedBefore', '_stopThreadPool', '_stopped', '_supportedAddressFamilies', '_threadpoolStartupID', '_uninstallHandler', '_wakerFactory', '_workerInThread', 'addReader', 'addSystemEventTrigger', 'addWriter', 'adoptDatagramPort', 'adoptStreamConnection', 'adoptStreamPort', 'callFromThread', 'callInThread', 'callLater', 'callWhenRunning', 'connectSSL', 'connectTCP', 'connectUNIX', 'connectUNIXDatagram', 'crash', 'disconnectAll', 'doIteration', 'doThreadIteration', 'ensureWorkerThread', 'fireSystemEvent', 'getDelayedCalls', 'getReaders', 'getThreadPool', 'getWriters', 'installNameResolver', 'installResolver', 'installWaker', 'installed', 'interleave', 'iterate', 'listenMulticast', 'listenSSL', 'listenTCP', 'listenUDP', 'listenUNIX', 'listenUNIXDatagram', 'mainLoop', 'mainWaker', 'nameResolver', 'reads', 'removeAll', 'removeReader', 'removeSystemEventTrigger', 'removeWriter', 'resolve', 'resolver', 'run', 'runUntilCurrent', 'running', 'seconds', 'sigBreak', 'sigInt', 'sigTerm', 'spawnProcess', 'startRunning', 'stop', 'suggestThreadPoolSize', 'threadCallQueue', 'threadpool', 'threadpoolShutdownID', 'timeout', 'toMainThread', 'toThreadQueue', 'usingThreads', 'wakeUp', 'waker', 'workerThread', 'writes']


"""

    # #def on_start(self):
        # #self.connect_to_server()

    # #def connect_to_server(self):
        # #reactor.connectTCP('localhost', 8000, EchoClientFactory(self))

    # #def on_connection(self, connection):
        # #self.print_message("Connected successfully!")
        # #self.connection = connection

    # #def send_message(self, *args):
        # #if msg and self.connection:
            # #self.connection.write(msg.encode('utf-8'))
