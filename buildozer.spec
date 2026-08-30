[app]

title = Traites Bancaires
package.name = traitesbancaires
package.domain = org.benayed
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

requirements = python3,kivy==2.3.1,kivymd==1.2.0,reportlab,plyer,jnius,android

orientation = portrait

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 31
android.minapi = 21
android.sdk = 31
android.enable_androidx = True
android.accept_sdk_license = True
android.allow_backup = True
android.gradle_dependencies = 'androidx.core:core:1.9.0'

fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
