[app]

title = KivyDemo
package.name = kivydemo
package.domain = org.kivydemo

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.1

requirements = python3,kivy

android.api = 33
android.ndk = 25b
android.sdk = 24
android.permissions = INTERNET

orientation = portrait

[buildozer]
log_level = 2
warn_on_root = 1
