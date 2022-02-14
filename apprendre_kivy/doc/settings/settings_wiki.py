#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import kivy
kivy.require('1.11.1')

from kivy.app import App
from kivy.uix.button import Button

# Pour l'honneur des mangalores
GLOBAL_DICT = {}

class MyApp(App):
    def build(self):
        """Pas de kv !"""

        settings_button = Button(text='Options')
        settings_button.bind(on_press=self.open_settings)
        return settings_button

    def on_start(self):
        """Exécuté apres build()"""
        pass

    def build_config(self, config):
        """Excécuté en premier, avant build.
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
        les réglages Kivy sont par défaut.

        Cette méthode est appelée par app.open_settings() dans .kv,
        donc si Options est cliqué !
        Les types contrôlent les saisies, mais pas les desc ne contrôlent pas.
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
        settings.add_json_panel('ServerKivy', self.config, data=data)

    def on_config_change(self, config, section, key, value):
        """Si modification des options, fonction appelée automatiquement
        menu = self.screen_manager.get_screen("Main")
        """

        if config is self.config:  # du joli python rigoureux
            token = (section, key)

            # Frequency
            if token == ('network', 'freq'):
                GLOBAL_DICT["freq"] = int(token[1])

            # Cast
            if token == ('network', 'cast'):
                print("Nouveau réseau:", value)
                # TODO ... etc ...

    def do_quit(self):

        print("Je quitte proprement")

        # Kivy
        ServerKivyApp.get_running_app().stop()

        # Extinction forcée de tout, si besoin
        os._exit(0)



MyApp().run()
