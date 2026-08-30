# -*- coding: utf-8 -*-
"""Fonctions utilitaires partagées (export PDF, dates, formatage)."""

import os
import shutil
import datetime

from constants import DEFAULT_CARD_OFFSET_X_MM, DEFAULT_CARD_OFFSET_Y_MM

# Sur Android (une fois construit avec Buildozer), ces modules sont
# disponibles. En développement sur PC, ils ne le sont pas -> ANDROID=False
# et l'application utilise un dossier local classique à la place, ce qui
# permet de tester toute la logique sans avoir de téléphone sous la main.
try:
    from jnius import autoclass
    ANDROID = True
except Exception:
    ANDROID = False


def get_print_offsets(db):
    """Lit le décalage d'impression enregistré (position de la kembyela sur
    la feuille A4 + réglage fin), avec comme valeur par défaut le coin
    haut-gauche de la feuille A4."""
    ox = float(db.get_setting("offset_x_mm", str(DEFAULT_CARD_OFFSET_X_MM))
               or DEFAULT_CARD_OFFSET_X_MM)
    oy = float(db.get_setting("offset_y_mm", str(DEFAULT_CARD_OFFSET_Y_MM))
               or DEFAULT_CARD_OFFSET_Y_MM)
    return ox, oy


def today_str():
    return datetime.date.today().strftime("%d/%m/%Y")


def add_days_str(base_ddmmyyyy, days):
    try:
        d = datetime.datetime.strptime(base_ddmmyyyy, "%d/%m/%Y").date()
    except (ValueError, TypeError):
        d = datetime.date.today()
    return (d + datetime.timedelta(days=days)).strftime("%d/%m/%Y")


def fmt_montant(value):
    try:
        return f"{float(value):,.3f}".replace(",", " ").replace(".", ",")
    except (TypeError, ValueError):
        return str(value)


# ----------------------------------------------------------------------
# Export / impression (Android)
# ----------------------------------------------------------------------

def get_export_dir():
    """Dossier où sont sauvegardées les traites générées, TOUJOURS
    accessible sans permission spéciale (dossier externe propre à
    l'application). C'est l'emplacement fiable et garanti ; voir
    try_save_to_public_downloads() ci-dessous pour une copie optionnelle
    dans le dossier Téléchargements public (plus facile à retrouver depuis
    Epson iPrint, mais pas garanti sur toutes les versions d'Android)."""
    if ANDROID:
        try:
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity
            ext_dir = activity.getExternalFilesDir(None)
            path = os.path.join(ext_dir.getAbsolutePath(), "Traites")
            os.makedirs(path, exist_ok=True)
            return path
        except Exception:
            pass
    # Développement sur PC (test de l'application avant compilation en APK)
    path = os.path.join(os.path.expanduser("~"), "TraiteMobileApp", "Traites")
    os.makedirs(path, exist_ok=True)
    return path


def try_save_to_public_downloads(src_path, filename):
    """Tentative BEST-EFFORT de copier aussi le fichier dans le dossier
    Téléchargements public (plus simple à retrouver depuis Epson iPrint).
    Selon la version d'Android du téléphone, ceci peut fonctionner ou non
    -- ce n'est jamais grave si ça échoue, le fichier reste de toute façon
    disponible à l'emplacement garanti (voir get_export_dir). Retourne le
    chemin public si réussi, sinon None."""
    if not ANDROID:
        return None
    try:
        from android.permissions import request_permissions, Permission, check_permission
        needed = [Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE]
        if not all(check_permission(p) for p in needed):
            request_permissions(needed)
            return None  # la réponse à la demande de permission est asynchrone
        Environment = autoclass("android.os.Environment")
        downloads = Environment.getExternalStoragePublicDirectory(
            Environment.DIRECTORY_DOWNLOADS
        ).getAbsolutePath()
        dest_dir = os.path.join(downloads, "Traites")
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, filename)
        shutil.copyfile(src_path, dest_path)
        return dest_path
    except Exception:
        return None


def share_pdf(path):
    """Tentative BEST-EFFORT d'ouvrir directement le sélecteur de partage
    Android pour envoyer le PDF vers une autre application (Epson iPrint,
    etc.). Retourne True si la tentative a été lancée, False sinon -- dans
    ce cas, le fichier reste disponible dans le(s) dossier(s) ci-dessus
    pour être ouvert manuellement depuis Epson iPrint."""
    if not ANDROID:
        return False
    try:
        from jnius import cast
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        File = autoclass("java.io.File")
        FileProvider = autoclass("androidx.core.content.FileProvider")

        activity = PythonActivity.mActivity
        java_file = File(path)
        authority = f"{activity.getPackageName()}.fileprovider"
        uri = FileProvider.getUriForFile(activity, authority, java_file)

        intent = Intent(Intent.ACTION_SEND)
        intent.setType("application/pdf")
        intent.putExtra(Intent.EXTRA_STREAM, cast("android.os.Parcelable", uri))
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

        chooser = Intent.createChooser(intent, "Imprimer avec...")
        activity.startActivity(chooser)
        return True
    except Exception:
        return False
