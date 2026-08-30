[app]

# (str) Title of your application
title = Traites Bancaires

# (str) Package name
package.name = traitesbancaires

# (str) Package domain (needed for android/ios packaging)
package.domain = org.benayed

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py

# (str) Application versioning
version = 1.0

# (list) Application requirements
# kivymd est fixé à 1.2.0 (version stable, testée) plutôt que la dernière
# version -- voir le README pour plus de détails sur ce choix.
requirements = python3,kivy==2.3.1,kivymd==1.2.0,reportlab,pyjnius

# (str) Presplash / icon -- non fournis pour cette première version ;
# l'application utilise l'icône Kivy par défaut. Vous pourrez en ajouter
# une plus tard (voir README) sans que cela nécessite de changement de code.
#icon.filename = %(source.dir)s/icon.png

# (str) Supported orientation (portrait, landscape or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
# WRITE/READ_EXTERNAL_STORAGE : pour la copie (best-effort) du PDF dans le
# dossier Téléchargements public, plus facile à retrouver depuis Epson
# iPrint. Ce n'est jamais bloquant si la permission est refusée ou ne
# fonctionne pas sur une version d'Android donnée -- le PDF reste toujours
# disponible dans le dossier propre à l'application (voir util.py).
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (list) The Android archs to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (bool) If True, then skip trying to update Android sdk
# (useful when using a pre-configured environment via GitHub Actions)
#android.skip_update = False

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
