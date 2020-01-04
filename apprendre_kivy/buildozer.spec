[app]

title = Apprendre Kivy

package.name = apprendrekivy
package.domain = org.test

source.dir = .

source.include_exts = py,png,jpg,kv,atlas

source.include_patterns = images/*.jpg,images/*.png

version.regex = __version__ = ['"](.*)['"]
version.filename = %(source.dir)s/main.py

requirements = python3,kivy,twisted

orientation = landscape

fullscreen = 0

android.permissions = INTERNET,CHANGE_WIFI_MULTICAST_STATE,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE

android.arch = armeabi-v7a

[buildozer]

log_level = 2

warn_on_root = 1
