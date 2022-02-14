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


import kivy
kivy.require('1.10.0')

from kivy.app import App
from kivy.properties import ListProperty
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen

from terrain import Terrain


# Points pour kivy
NUM = 1
TERRAIN = Terrain(NUM)
LINE = TERRAIN.line
NET = TERRAIN.net_line
PATH = TERRAIN.path_line


# Pass variable between python script http://bit.ly/2n0ksWh
from __main__ import *


class Screen1(Screen):
    """1 joueur en position 0"""

    points = ListProperty(LINE)
    net = ListProperty(NET)
    ball = ObjectProperty()

    paddle_0 = ObjectProperty()
    paddle_1 = ObjectProperty()

    score_0 = ObjectProperty()
    score_1 = ObjectProperty()

    titre = ObjectProperty()
    classement = ObjectProperty()

    def __init__(self, **kwargs):

        super(Screen1, self).__init__(**kwargs)

        self.coef = COEF

        self.my_num = 0

        # Dict des paddles
        self.paddle_d = {   0: self.paddle_0,
                            1: self.paddle_1}

        self.paddle_d[0].source = './images/g_v.png'
        self.paddle_d[1].source = './images/g_v.png'

        # Ma paddle position
        self.my_pad_pos = [0, 0]

        # Dict des scores
        self.score_d = {    0: self.score_0,
                            1: self.score_1}

        # height = 100 --> bidouille
        h = 720 * self.coef
        # 1/2 Taille de la balle
        self.BALL = h/(33*2)
        # 1/2 Taille de paddle
        self.PADDLE = h/(5.142*2)

    def apply_paddle_red_color(self):
        """J'applique le rouge à ma paddle"""

        if self.my_num == 0:
            self.paddle_d[0].source = './images/r_v.png'
            self.paddle_d[1].source = './images/g_v.png'

    def apply_my_num(self, my_num):
        """Appelé dans main"""

        self.my_num = my_num

    def apply_classement(self, classement):
        """Applique le classement
        classement = {'pierre': 1, 'AI': 2}
        str = 'pierre': 1, 'AI': 2
        """

        text = "\n"
        if classement:
            for i in range(len(classement)):
                for name, rank in classement.items():
                    if rank == i + 1:
                        if name != "Isac  Asimov":
                            name = name[:-8]
                        text += ". " + str(i+1) + "  " + name + "\n\n"

            self.classement.text = text
            self.titre.text = "Classement"
        else:
            self.titre.text = ""
            self.classement.text = ""

    def apply_score(self, score):
        """Set les scores
        score = [4, 2]
        """

        self.score_0.text = str(score[0])
        self.score_1.text = str(score[1])

    def apply_ball_pos(self, ball_pos):
        """Positionne la balle avec position du serveur."""

        if ball_pos:
            x, y = TERRAIN.get_kivy_coord(ball_pos)

            # Correction de Window size
            x *= self.coef
            y *= self.coef

            # Ajout du décalage de centre de ball, pas de coef
            s = self.BALL
            x -= s
            y -= s

            X = int(x)
            Y = int(y)

            self.ball.pos = [X, Y]

    def apply_other_paddles_pos(self, paddle_pos):
        """  Toutes les paddles sauf la mienne
             moi         l'autre
        [[-9.5, 0.0], [9.5, -1.81], [0, 0], [0, 0], ....]
        au reset len(paddle_pos) = 10

        """

        # Valable pour level 1 seul, applique sur paddle 1
        if paddle_pos[1]!= [0, 0]:
            x, y = TERRAIN.get_kivy_coord(paddle_pos[1])

            # Correction de Window size
            x *= self.coef
            y *= self.coef

            # Ajout du décalage de centre de paddle
            s = self.PADDLE
            x -= s
            y -= s

            X = int(x)
            Y = int(y)

            self.paddle_d[1].pos = [X, Y]

    def on_touch_move(self, touch):
        """Capture de la position de touch"""

        try:
            x = touch.x/self.coef
            y = touch.y/self.coef
            self.apply_touch(x, y)
        except:
            print("Pb avec on_touch_move")

    def apply_touch(self, x, y):
        """Calcul du déplacement de ma paddle."""

        # Vertical y = y
        x = PATH[2]

        # Correction pour jouabilité
        y = y*840/700 - 80

        # Position centée de ma paddle pour blender
        self.my_pad_pos = [x, y]
        # Pour kivy ici
        self.apply_my_paddle_pos(x, y)

    def apply_my_paddle_pos(self, x, y):
        """my paddle soit0, avec la capture de position sur l'écran"""

        # Correction de Window size
        x *= self.coef
        y *= self.coef

        # Ajout du décalage de centre de ball, pas de coef
        s = self.PADDLE
        x -= s
        y -= s

        X = int(x)
        Y = int(y)

        if self.my_num is not None:
            # Ma position
            self.paddle_d[self.my_num].pos = [X, Y]

    def get_my_blender_paddle_pos(self):
        """Retourne la position de ma paddle à envoyer au serveur"""

        [x, y] = TERRAIN.get_blender_coord(self.my_pad_pos)

        return [x, y]
