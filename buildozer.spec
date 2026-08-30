[app]

# (str) Title of your application
title = Traites Bancaires

# (str) Package name
package.name = traitesbancaires

# (str) Package domain (needed for android/ios packaging)
package.domain = org.benayed

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (can be glob patterns)
source.include_exts = py,png,jpg,kv,atlas

# (list) Requirements (libraries)
requirements = python3,kivy==2.3.1,kivymd==1.2.0,reportlab,plyer,jnius,android

# (str) Presplash screen (image) – optional
# presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon (image) – optional
# icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of: landscape, portrait, all)
orientation = portrait

# (list) Permissions (android)
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (int) Target Android API level
android.api = 31

# (int) Minimum Android API level
android.minapi = 21

# (int) Android SDK version
android.sdk = 31

# (str) Android NDK version (optional)
# android.ndk = 23b

# (bool) Enable AndroidX (required for KivyMD 1.2.0)
android.enable_androidx = True

# (list) Gradle dependencies (to fix jnius issues)
android.gradle_dependencies = 'androidx.core:core:1.9.0'

# (str) Python for Android branch (use stable)
p4a.branch = stable

# (bool) Allow building with older SDK
android.allow_backup = True

# (bool) Fullscreen
fullscreen = 0

[buildozer]

# (int) Log level (0=error, 1=warning, 2=info, 3=debug)
log_level = 2

# (bool) WARN: show warnings
warn_on_root = 1
