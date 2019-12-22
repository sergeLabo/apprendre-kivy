#! /usr/bin/env python3
# -*- coding: utf-8 -*-


__version__ = '0.001'


import os

import kivy
kivy.require('1.11.1')

from kivy.core.window import Window
# Les 3 lignes ci-dessous sont à commenter pour buildozer
# L'écran de mon tél fait 1280*720
k = 1.2
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


class PongPaddle(Widget):
    score = NumericProperty(0)
    can_bounce = BooleanProperty(True)
    size = 15, 20

    def bounce_ball(self, ball):
        if self.collide_widget(ball) and self.can_bounce:
            vx, vy = ball.velocity
            offset = (ball.center_y - self.center_y) / (self.height / 2)
            bounced = Vector(-1 * vx, vy)
            vel = bounced * 1.1
            ball.velocity = vel.x, vel.y + offset
            self.can_bounce = False
        elif not self.collide_widget(ball) and not self.can_bounce:
            self.can_bounce = True


class PongBall(Widget):
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)
    size = 25, 25

    def move(self):
        self.pos = Vector(*self.velocity) + self.pos


class PongGame(Screen, Widget):

    # Attributs de class
    ball = ObjectProperty(None)
    player1 = ObjectProperty(None)
    player2 = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(PongGame, self).__init__(**kwargs)
        print("Initialisation du Screen Pong ok")
        self.tictac = Clock.schedule_interval(self.update, 0.016)

    def serve_ball(self, vel=(4, 0)):
        self.ball.center = self.center
        self.ball.velocity = vel

    def update(self, dt):
        print("Update", self.ball.x, self.ball.y)
        self.ball.move()

        # bounce ball off paddles
        self.player1.bounce_ball(self.ball)
        self.player2.bounce_ball(self.ball)

        # bounce ball off bottom or top
        if (self.ball.y < self.y) or (self.ball.top > self.top):
            self.ball.velocity_y *= -1

        # went off a side to score point?
        if self.ball.x < self.x:
            self.player2.score += 1
            self.serve_ball(vel=(4, 0))
        if self.ball.x > self.width:
            self.player1.score += 1
            self.serve_ball(vel=(-4, 0))

    def on_touch_move(self, touch):
        if touch.x < self.width / 3:
            self.player1.center_y = touch.y
        if touch.x > self.width - self.width / 3:
            self.player2.center_y = touch.y


class MainScreen(Screen):
    """Ecran principal, l'appli s'ouvre sur cet écran"""

    # Attributs de class
    bgcolor = ListProperty([0,0,0])

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        # Construit le jeu, le réseau, tourne tout le temps
        scr_manager = self.get_screen_manager()
        print("Initialisation du Screen MainScreen ok")

    def get_screen_manager(self):
        return TrainingPongApp.get_running_app().screen_manager


# Variable globale qui définit les écrans
# L'écran de configuration est toujours créé par défaut
# Il suffit de créer un bouton d'accès
SCREENS = { 0: (MainScreen, "Main"), 1: (PongGame, "Pong")}


class TrainingPongApp(App):
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
        pass

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
                              'log_name': 'pong_%y-%m-%d_%_.txt',
                              'log_dir': '/sdcard',
                              'log_enable': '1'})

        config.setdefaults('postproc',
                            { 'double_tap_time': 250,
                              'double_tap_distance': 20})

    def build_settings(self, settings):
        """Construit l'interface de l'écran Options, pour multipong seul,
        Kivy est par défaut, appelé par app.open_settings() dans .kv
        """

        data = """[{"type": "title", "title":"Configuration du réseau"},
                      {"type": "numeric",
                      "title": "Fréquence",
                      "desc": "Fréquence entre 1 et 60 Hz",
                      "section": "network", "key": "freq"}
                   ]"""

        # self.config est le config de build_config
        settings.add_json_panel('Training-Pong', self.config, data=data)

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
        pong_screen = self.screen_manager.get_screen("Pong")
        pong_screen.tictac.cancel()

        # Kivy
        TrainingPongApp.get_running_app().stop()

        # Extinction forcée de tout, si besoin
        os._exit(0)


if __name__ == '__main__':
    TrainingPongApp().run()
