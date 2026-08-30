# -*- coding: utf-8 -*-
"""Point d'entrée de l'application mobile de gestion des traites."""

import os
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.navigationdrawer import MDNavigationDrawer, MDNavigationLayout
from kivymd.uix.list import MDList, OneLineIconListItem, IconLeftWidget
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivy.metrics import dp

from db import Database

APP_TITLE = "Gestion des Traites"

NAV_ITEMS = [
    ("dashboard", "view-dashboard", "Tableau de bord"),
    ("nouvelle_traite", "plus-circle", "Nouvelle traite"),
    ("archive", "archive", "Archive"),
    ("clients", "account-group", "Clients"),
    ("rapports", "chart-bar", "Rapports"),
    ("calibrage", "printer-settings", "Calibrage impression"),
]


def get_data_dir():
    """Dossier de données de l'application (persistant entre les lancements)."""
    try:
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        base = app.user_data_dir  # ex: /storage/emulated/0/Android/data/<pkg>/files
    except Exception:
        base = os.path.join(os.path.expanduser("~"), "TraiteMobileApp")
    os.makedirs(base, exist_ok=True)
    return base


class TraiteApp(MDApp):
    def build(self):
        self.title = APP_TITLE
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Orange"

        self.data_dir = get_data_dir()
        self.db = Database(os.path.join(self.data_dir, "traite.db"))

        # traite en cours de modification (transmis entre écrans)
        self.editing_traite_id = None

        root = MDNavigationLayout()

        self.sm = MDScreenManager()
        self._screen_cache = {}
        root.add_widget(self.sm)

        self.nav_drawer = MDNavigationDrawer(padding=[0, 0, 0, 16])
        self._build_drawer()
        root.add_widget(self.nav_drawer)

        self.toolbar = None
        self._content_container = None
        self._build_main_screen(root)

        self.show_screen("dashboard")
        return root

    # ------------------------------------------------------------------
    def _build_drawer(self):
        box = MDBoxLayout(orientation="vertical")
        header = MDBoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(90),
            padding=(dp(16), dp(16)), md_bg_color=self.theme_cls.primary_color,
        )
        header.add_widget(MDLabel(text="Traites Bancaires", theme_text_color="Custom",
                                    text_color=(1, 1, 1, 1), font_style="H6"))
        header.add_widget(MDLabel(text="Gestion & impression", theme_text_color="Custom",
                                    text_color=(1, 1, 1, 0.85), font_style="Caption"))
        box.add_widget(header)

        nav_list = MDList()
        self._nav_widgets = {}
        for key, icon, label in NAV_ITEMS:
            item = OneLineIconListItem(text=label, on_release=self._make_nav_handler(key))
            item.add_widget(IconLeftWidget(icon=icon))
            nav_list.add_widget(item)
            self._nav_widgets[key] = item
        box.add_widget(nav_list)

        self.nav_drawer.add_widget(box)

    def _make_nav_handler(self, key):
        def handler(*args):
            self.nav_drawer.set_state("close")
            self.show_screen(key)
        return handler

    def _build_main_screen(self, root):
        screen = MDScreen(name="main")
        outer = MDBoxLayout(orientation="vertical")
        self.toolbar = MDTopAppBar(
            title="Tableau de bord",
            left_action_items=[["menu", lambda x: self.nav_drawer.set_state("open")]],
            elevation=4,
        )
        outer.add_widget(self.toolbar)

        self._content_container = MDBoxLayout(orientation="vertical")
        outer.add_widget(self._content_container)

        screen.add_widget(outer)
        self.sm.add_widget(screen)

    # ------------------------------------------------------------------
    def show_screen(self, key, **kwargs):
        """Affiche l'écran demandé, en le (re)construisant à chaque fois
        pour être sûr d'avoir des données à jour (comme sur l'application
        de bureau)."""
        titles = {label_key: label for label_key, _, label in NAV_ITEMS}
        self.toolbar.title = titles.get(key, APP_TITLE)

        self._content_container.clear_widgets()

        if key == "dashboard":
            from screens.dashboard_screen import DashboardScreen
            widget = DashboardScreen(self)
        elif key == "nouvelle_traite":
            from screens.traite_form_screen import TraiteFormScreen
            widget = TraiteFormScreen(self, traite_id=kwargs.get("traite_id"))
        elif key == "archive":
            from screens.archive_screen import ArchiveScreen
            widget = ArchiveScreen(self)
        elif key == "clients":
            from screens.clients_screen import ClientsScreen
            widget = ClientsScreen(self)
        elif key == "rapports":
            from screens.rapports_screen import RapportsScreen
            widget = RapportsScreen(self)
        elif key == "calibrage":
            from screens.calibration_screen import CalibrationScreen
            widget = CalibrationScreen(self)
        else:
            return

        self._content_container.add_widget(widget)
        self.current_screen_key = key

    def edit_traite(self, traite_id):
        self.show_screen("nouvelle_traite", traite_id=traite_id)

    def on_stop(self):
        try:
            self.db.close()
        except Exception:
            pass


if __name__ == "__main__":
    TraiteApp().run()
