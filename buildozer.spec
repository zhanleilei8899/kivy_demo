[app]

title = NetCheck
package.name = netcheck
package.domain = org.netcheck

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.1

requirements = python3,kivy,requests

android.api = 33
android.ndk = 25b
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE

orientation = portrait

[buildozer]
log_level = 2
warn_on_root = 1
