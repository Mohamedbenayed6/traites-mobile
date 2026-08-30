# -*- coding: utf-8 -*-
"""Petites fonctions d'interface partagées entre les écrans."""

from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.label import MDLabel


def show_message(text, duration=3):
    """Affiche un message temporaire en bas de l'écran (confirmation, erreur...)."""
    MDSnackbar(
        MDLabel(text=text, theme_text_color="Custom", text_color=(1, 1, 1, 1)),
        duration=duration, y="20dp", pos_hint={"center_x": 0.5}, size_hint_x=0.9,
    ).open()
