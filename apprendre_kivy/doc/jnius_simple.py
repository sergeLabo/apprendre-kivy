#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys  # C'est les seuls import que je fais en une ligne
from time import sleep

import kivy
kivy.require('1.11.1')

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.lang import Builder

# Bidouille pour que python trouve java sur mon PC
platform = sys.platform
print("Platform = {}".format(platform))
if 'linux' in platform:
    # Valable pour openjdk 8 sur Debian Buster
    os.environ["JAVA_HOME"] = "/usr/lib/jvm/adoptopenjdk-8-hotspot-amd64"

from jnius import MetaJavaClass, JavaClass, JavaStaticMethod

"""
dir(jnius)
['HASHCODE_MAX', 'JavaClass', 'JavaException', 'JavaField', 'JavaMethod',
'JavaObject', 'MetaJavaClass', 'PythonJavaClass', 'PythonJavaClass_',
'__builtins__', '__cached__', '__doc__', '__file__', '__loader__', '__name__',
'__package__', '__path__', '__spec__', '__version__', 'autoclass', 'cast',
'detach', 'ensureclass', 'find_javaclass', 'java_method', 'os', 'reflect']
"""

Builder.load_string('''
<Main>:
    BoxLayout:
        Label:
            text: self.text
''')

class Hardware(JavaClass):
    __metaclass__ = MetaJavaClass
    __javaclass__ = 'org/renpy/android/Hardware'
    vibrate = JavaStaticMethod('(D)V')
    accelerometerEnable = JavaStaticMethod('(Z)V')
    accelerometerReading = JavaStaticMethod('()[F')
    getDPI = JavaStaticMethod('()I')


class Main(Screen):

    text = StringProperty("toto")

    def __init__(self):
        print('DPI is', Hardware.getDPI())

        Hardware.accelerometerEnable()
        for x in xrange(20):
            print(Hardware.accelerometerReading())
            self.text = Hardware.accelerometerReading()
            sleep(.1)

class JniusSimpleApp(App):
    def build(self):
        return Main()

if __name__ == '__main__':
    JniusSimpleApp().run()
