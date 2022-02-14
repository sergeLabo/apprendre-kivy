#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import kivy
kivy.require('1.11.1')

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder

Builder.load_string('''
<Main>:
    BoxLayout:
        Button:
            text: "Go to settings"
            on_release: app.open_settings()
''')

class Main(Screen):
    pass

class MySettingsApp(App):

    def build(self):
        # Exemple d'ppel d'une valeur de la config
        self.freq = self.config.get('network', 'freq')

        return Main()

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
        settings.add_json_panel('MySettings', self.config, data=data)

    def on_config_change(self, config, section, key, value):
        """Si modification des options, fonction appelée automatiquement
        menu = self.screen_manager.get_screen("Main")
        """

        if config is self.config:  # du joli python rigoureux
            token = (section, key)

            # Frequency
            if token == ('network', 'freq'):
                # Le controle dy type est fait par Kivy
                # Ajouter des tests de valeurs
                self.freq = value
                # puis appliquer la nouvelle valeur
                print("Nouvelle fréquence", self.freq)



if __name__ == '__main__':
    MySettingsApp().run()
