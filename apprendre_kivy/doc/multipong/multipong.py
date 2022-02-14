#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# #####################################################################
# Copyright (C) Labomedia November 2017
#
# This file is part of multipong.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# #####################################################################


__version__ = '0.603'

"""
ne pas oublier de commenter le Window.size

version
0.603 pour gogle play
0.602 classement 6 ok verif ok
0.601 window ok
0.600 user ok, classement ok avec modif sur game_dictator
0.507 reste bug classement et quelques plantages
0.506 quit en bord d'écran
0.500 acceptable
"""

import kivy
kivy.require('1.10.0')

from kivy.core.window import Window
# ## Les 3 lignes ci-dessous sont à commenter pour buildozer
# #k = 1
# #WS = (int(1280*k), int(720*k))
# #Window.size = WS


from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.core.audio import SoundLoader

import os
import getpass
from time import time
import json
import ast
import random

# Les fichiers de ces modules sont dans le dossier courant
from labmulticast import Multicast
from labtcpclient import LabTcpClient


# Pass variable between python script http://bit.ly/2n0ksWh
COEF = Window.size[1]/720

# Puis import
from scr1 import Screen1
from scr2 import Screen2
from scr3 import Screen3
from scr4 import Screen4
from scr5 import Screen5
from scr6 import Screen6


class PongBall(Widget):
    pass


class PongPaddle(Widget):
    color = ListProperty([1, 1, 1])
    source = StringProperty()


class PongPaddle3(Widget):
    color = ListProperty([1, 1, 1])
    source = StringProperty()


class PongPaddle5(Widget):
    color = ListProperty([1, 1, 1])
    source = StringProperty()


class PongPaddle6(Widget):
    color = ListProperty([1, 1, 1])
    source = StringProperty()


class MainScreen(Screen):
    """Ecran principal"""

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        # Construit le jeu, le réseau, tourne tout le temps
        scr_manager = self.get_screen_manager()
        self.game = Game(scr_manager)

        print("Initialisation de MainScreen ok")

    def get_screen_manager(self):
        return MultiPongApp.get_running_app().screen_manager


class Network:
    """Message recu du serveur:
        {'svr_msg': {'ip': '192.168.1.12',
                     'dictat': {'scene': 'play',
                                'rank_end': 0,
                                'ball': [-5.4, 3.5],
                                'who_are_you': {},
                                'reset': 0,
                                'paddle': [],
                                'level': 1,
                                'classement': {},
                                'transit': 0,
                                'score': [8, 6]}}}
                                'mur': 1
                                'raquette': 1
        Message envoyé:
        {'joueur': {'name':   a1_452,
                    'paddle': [300, 500]}
    """

    def __init__(self, screen_manager):

        # config, obtenu avec des dir()
        config = MultiPongApp.get_running_app().config

        self.t_print = time()

        # Multi
        self.multi_ip, self.multi_port = self.get_multicast_addr(config)
        self.my_multi = Multicast(  self.multi_ip,
                                    self.multi_port,
                                    1024)

        # Serveur data
        self.dictat = None

        # TCP
        self.tcp_ip = None
        self.tcp_port = self.get_tcp_port(config)
        self.tcp_clt = None
        self.tcp_msg = {}

        print("Initialisation de Network ok")

    def network_update(self):
        """Maj de réception, maj des datas, envoi"""

        # Recup du message du serveur en multicast
        svr_msg = self.get_multicast_msg()
        self.dictat = self.get_dictat(svr_msg)

        # Set TCP
        self.tcp_ip = self.get_server_ip(svr_msg)
        self.create_tcp_socket()

    def get_dictat(self, svr_msg):
        """Retourne dictat"""

        try:
            sm = svr_msg["svr_msg"]
            dictat = sm["dictat"]
        except:
            dictat = None

        return dictat

    def get_server_ip(self, svr_msg):
        try:
            tcp_ip = svr_msg["svr_msg"]["ip"]
        except:
            tcp_ip = None
        return tcp_ip

    def get_multicast_addr(self, config):
        """Retourne l'adresse multicast"""

        multi_ip = config.get('network', 'multi_ip')
        multi_port = int(config.get('network', 'multi_port'))

        return multi_ip, multi_port

    def get_multicast_msg(self):
        """{svr_msg = 'svr_msg':
                    {'ip': '192.168.1.12',
                    'dictat': { 'level': 1,
                                'ball': [9.55, 9.32],
                                'transit': 0,
                                'who_are_you': {'alice': 0, 'bob': 1},
                                'rank_end': 0,
                                'paddle': {},
                                'score': [8,9],
                                'scene': 'play',
                                'classement': {},
                                'reset': 0}}}
        """

        try:
            data = self.my_multi.receive()
            svr_msg = datagram_to_dict(data)
        except:
            svr_msg = None

        return svr_msg

    def get_tcp_port(self, config):
        """Retourne le port TCP"""

        return int(config.get('network', 'tcp_port'))

    def create_tcp_socket(self):
        if self.tcp_ip and not self.tcp_clt:
            try:
                self.tcp_clt = LabTcpClient(self.tcp_ip,
                                            self.tcp_port)
            except:
                self.tcp_clt = None
                print("Pas d'ip dans le message du serveur")

    def send_tcp_msg(self):
        env = json.dumps(self.tcp_msg).encode("utf-8")
        if self.tcp_clt:
            #self.print_stuff()
            self.tcp_clt.send(env)

    def print_stuff(self):
        if time() - self.t_print > 2:
            #os.system('clear')
            print("  Joueur")
            print("Envoi de:")
            try:
                msg = self.tcp_msg["joueur"]
                for k, v in msg.items():
                    print("    ", k, v)
            except:
                pass

            print("\nRéception de:")

            if self.dictat:
                for k, v in self.dictat.items():
                    print("    ", k, v)

            self.t_print = time()


class Game(Network):

    volume = NumericProperty(1.0)

    def __init__(self, screen_manager, **kwargs):

        super(Game, self).__init__(screen_manager, **kwargs)

        self.scr_manager = screen_manager
        self.cur_screen = self.get_current_screen()

        # Rafraichissement du jeu
        tempo = self.get_tempo()
        self.event = Clock.schedule_interval(self.game_update, tempo)

        # Vérif freq
        self.t = time()
        self.v_freq = 0

        self.my_name = get_user_id()
        self.my_num = self.get_my_number()

        # Chargement des sons
        self.mur = SoundLoader.load('./sound/mur.ogg')
        self.raquette = SoundLoader.load('./sound/raquette.ogg')

        print("Initialisation de Game ok")

    def get_tempo(self):
        """Retourne la tempo de la boucle de Clock."""

        config = MultiPongApp.get_running_app().config
        freq = int(config.get('network', 'freq'))

        if freq > 60:
            freq = 60
        if freq < 1:
            freq = 1
        print("Frequence d'envoi en TCP =", freq)
        return 1/freq

    def game_update(self, dt):
        """self.dictat = {  "level":  2,
                            "scene" : 'play',
                            "classement": {},
                            "ball":   [7.19, 7.19],
                            "score":  [9, 7],
                            "paddle": [[-9.4, 0.0], [-9.4, 0.40]],
                            "who_are_you": {'moi': 0, 'toi': 1},
                            "match_end": 0,
                            "reset":   0,
                            "transit": 0,
                            "mur": 1,
                            "raquette": 0 }
        """

        self.verif_freq()
        self.network_update()
        self.apply_good_screen()
        self.my_num = self.get_my_number()
        self.apply_paddle_red_color()

        # Maj du screen courant
        self.get_current_screen()

        # Apply
        self.apply_my_num()
        self.apply_ball_pos()
        self.apply_other_paddles_pos()
        self.apply_score()
        self.apply_classement()
        self.sound()

        # Envoi au serveur
        self.create_msg()
        self.send_tcp_msg()

    def apply_good_screen(self):
        """Défini l'écran correspondant au nombre de joueurs
        calculé avec len()
        """

        if self.dictat:
            if "who_are_you" in self.dictat:
                #print(len(self.dictat["who_are_you"]))
                combien = len(self.dictat["who_are_you"])
                if combien > 6:
                    combien = 6
                if combien and self.cur_screen:
                    if str(combien) not in self.cur_screen.name:
                        self.scr_manager.current = (str(combien))

    def apply_my_num(self):
        """Tous les écrans 1 à 10 doivent avoir ces méthodes"""

        if self.cur_screen:
            if self.cur_screen.name != "Main":
                self.cur_screen.apply_my_num(self.my_num)

    def apply_paddle_red_color(self):
        """Les screen de 1 a 10 doivent avoir apply_paddle_red_color()
        """

        if self.cur_screen:
            if self.cur_screen.name != "Main":
                self.cur_screen.apply_paddle_red_color()

    def apply_score(self):
        """self.dictat = {... "score": [8, 9],..."""

        try:
            score = self.dictat["score"]
        except:
            score = None

        # Les screen de 1 a 10 doivent avoir apply_score()
        if score:
            if self.cur_screen.name != "Main":
                self.cur_screen.apply_score(score)

    def apply_classement(self):
        """self.dictat = {'classement': {'pierre': 1, 'AI': 2} """

        try:
            classement = self.dictat["classement"]
        except:
            classement = None

        # Les screen de 1 a 10 doivent avoir apply_(classement)
        if self.cur_screen.name != "Main":
            self.cur_screen.apply_classement(classement)

    def apply_ball_pos(self):
        """self.dictat = {... "ball": [7.19, 7.19],..."""

        try:
            ball_pos = self.dictat["ball"]
        except:
            ball_pos = None

        # Les screen de 1 a 10 doivent avoir apply_ball_pos()
        if ball_pos:
            if self.cur_screen.name != "Main":
                self.cur_screen.apply_ball_pos(ball_pos)

    def apply_other_paddles_pos(self):
        """paddle_pos = [[2, 3], [5, 6], ... """

        try:
            paddles = self.dictat["paddle"]
        except:
            paddles = None

        if paddles:
            # Les screen de 1 a 10 doivent avoir
            #   apply_other_paddles_pos()
            if self.cur_screen.name != "Main":
                self.cur_screen.apply_other_paddles_pos(paddles)

    def verif_freq(self):
        self.v_freq += 1
        a = time()
        if a - self.t > 1:
            #print("FPS:", self.v_freq)
            self.v_freq = 0
            self.t = a

    def get_current_screen(self):
        """Retourne le screen en cours"""

        self.cur_screen = self.scr_manager.current_screen

    def get_my_number(self):
        """Retourne le numéro attribué par le serveur.
        Je suis self.my_name
        self.dictat = { ...,
                        'who_are_you': {'moi': 0, 'toi': 1},
                        ...}
        """

        try:
            num = self.dictat['who_are_you'][self.my_name]
        except:
            num = None

        return num

    def create_msg(self):
        if "Main" not in self.cur_screen.name:
            paddle = self.get_my_blender_paddle_pos()
            self.tcp_msg = {"joueur": {"name":   self.my_name,
                                       "paddle": paddle        }}

    def get_my_blender_paddle_pos(self):
        """Valable pour tous les niveaux"""

        return self.cur_screen.get_my_blender_paddle_pos()

    def get_my_name():
        if "Main" not in self.cur_screen.name:
            return "Joueur" + self.cur_screen
        else:
            return None

    def sound(self):
        try:
            mur = self.dictat["mur"]
            raquette = self.dictat["raquette"]
        except:
            mur, raquette = None, None

        if mur:
            self.mur_sound()
        if raquette:
            self.raquette_sound()

    def mur_sound(self):
        if self.mur:
            volume = random.uniform(0.1, 1)
            self.mur.volume = volume
            self.mur.play()

    def raquette_sound(self):
        if self.raquette:
            volume = random.uniform(0.1, 1)
            self.raquette.volume = volume
            self.raquette.play()


SCREENS = { 0: (MainScreen, "Main"),
            1: (Screen1,    "1"),
            2: (Screen2,    "2"),
            3: (Screen3,    "3"),
            4: (Screen4,    "4"),
            5: (Screen5,    "5"),
            6: (Screen6,    "6")}


class MultiPongApp(App):
    """Construction de l'application. Exécuté par __main__,
    app est le parent de cette classe dans kv.
    """

    def build(self):
        """Exécuté en premier après run()"""

        # Creation des ecrans
        self.screen_manager = ScreenManager()
        for i in range(len(SCREENS)):
            self.screen_manager.add_widget(SCREENS[i][0](name=SCREENS[i][1]))

        return self.screen_manager

    def on_start(self):
        """Exécuté apres build()"""
        pass

    def build_config(self, config):
        """Si le fichier *.ini n'existe pas,
        il est créé avec ces valeurs par défaut.
        Si il manque seulement des lignes, il ne fait rien !
        """

        config.setdefaults('network',
                            { 'multi_ip': '228.0.0.5',
                              'multi_port': '18888',
                              'tcp_port': '8000',
                              'freq': '60'})

        config.setdefaults('kivy',
                            { 'log_level': 'debug',
                              'log_name': 'multipong_%y-%m-%d_%_.txt',
                              'log_dir': '/sdcard',
                              'log_enable': '1'})

        config.setdefaults('postproc',
                            { 'double_tap_time': 250,
                              'double_tap_distance': 20})

    def build_settings(self, settings):
        """Construit l'interface de l'écran Options,
        pour multipong seul,
        Kivy est par défaut,
        appelé par app.open_settings() dans .kv
        """

        data = """[{"type": "title", "title":"Configuration du réseau"},
                      {"type": "numeric",
                      "title": "Fréquence",
                      "desc": "Fréquence entre 1 et 60 Hz",
                      "section": "network", "key": "freq"}
                   ]"""

        # self.config est le config de build_config
        settings.add_json_panel('MultiPong', self.config, data=data)

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

        # Stop propre de Clock
        menu = self.screen_manager.get_screen("Main")
        menu.game.event.cancel()

        # Kivy
        MultiPongApp.get_running_app().stop()

        # Extinction de tout
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
        msg = dec

    if isinstance(msg, dict):
        return msg
    else:
        print("Message reçu: None")
        return None

def get_user_id():
    """u0_a73 sur android"""

    try:
        user = getpass.getuser()
        print("Ton nom est:", user)
        # Ajout de qq chiffre pour distinction en debug sur mon PC
        user += str(int(10000* time()))[-8:]
        print("User login:", user)
    except:
        user = "j" + str(int(100*time()))[-8:]
        print("User:", user)
    return  user


if __name__ == '__main__':
    MultiPongApp().run()
