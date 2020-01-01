#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import kivy
kivy.require('1.8.0')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.carousel import Carousel
from kivy.clock import Clock

class Nothing:
    def print_some(self, some):
        print(some)

class MainScreen(Screen):
    pass

class Screen1(Screen, Nothing):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Cet objet (donc self!) hérite des méthodes et attributs de Nothing
        self.print_some("je suis le plus fort")

class Screen2(Screen):
    pass

SCREENS = { 0: (MainScreen,       "Menu"),
            1: (Screen1,          "Ecran 1"),
            2: (Screen2,          "Ecran 2")}

class Carousel_ExApp(App):

    def build(self):
        carousel = Carousel(direction='right')
        for i in range(3):
            carousel.add_widget(SCREENS[i][0](name=SCREENS[i][1]))
        return carousel

if __name__ == '__main__':
    Carousel_ExApp().run()
