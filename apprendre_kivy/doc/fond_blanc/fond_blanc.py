#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import kivy
kivy.require('1.11.1')

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty
from kivy.lang import Builder

Builder.load_string('''
<Main>:
    BoxLayout:
        canvas.before:
            Color:
                rgb: 1, 1, 1
            Rectangle:
                size: self.size
                pos: self.pos
        canvas:
            Rectangle:
                # self.size = taille du BoxLayout
                size: root.taille
                pos: 200, 200
                source: "labo.png"
''')

class Main(Screen):
    # Attibut de class accessible dans kv avec root.taille
    taille = ListProperty([200, 200])

    # taille peut être modifié ensuite avec l'attribut self.taille

class FondBlancApp(App):
    def build(self):
        return Main()

if __name__ == '__main__':
    FondBlancApp().run()
