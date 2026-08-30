# -*- coding: utf-8 -*-
import os
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp

from constants import FIELDS, FIELD_ORDER, DEFAULT_CARD_OFFSET_X_MM, DEFAULT_CARD_OFFSET_Y_MM
from pdf_gen import generate_test_grid_pdf
from util import get_print_offsets, get_export_dir, try_save_to_public_downloads, share_pdf
from ui_helpers import show_message

STEPS = ["0.1", "0.5", "1.0"]


class CalibrationScreen(MDBoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.app = app
        self.db = app.db
        self.step = 0.1
        self.row_widgets = {}
        self._build()

    def _build(self):
        scroll = MDScrollView()
        col = MDBoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14),
                            size_hint_y=None, adaptive_height=True)

        info = MDLabel(text="Les positions ci-dessous sont déjà calées sur la kembyela réelle. "
                              "Ajustez seulement si besoin.",
                         theme_text_color="Hint", font_style="Caption",
                         size_hint_y=None, height=dp(40))
        col.add_widget(info)

        step_row = MDBoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        step_row.add_widget(MDLabel(text="Pas :", size_hint_x=None, width=dp(40)))
        self.step_btn = MDFlatButton(text="0.1 cm")
        self.step_btn.bind(on_release=self._open_step_menu)
        step_row.add_widget(self.step_btn)
        col.add_widget(step_row)

        # ---------------- Position sur la feuille A4 ----------------
        offset_card = MDCard(orientation="vertical", padding=dp(12), spacing=dp(8),
                               size_hint_y=None, adaptive_height=True, radius=[8], elevation=1)
        offset_card.add_widget(MDLabel(text="Position sur la feuille A4 (cm)", bold=True,
                                         size_hint_y=None, height=dp(24)))
        ox_mm, oy_mm = get_print_offsets(self.db)
        offset_row = MDBoxLayout(spacing=dp(8), size_hint_y=None, height=dp(52))
        self.f_offset_x = MDTextField(hint_text="X", text=f"{ox_mm/10:.2f}")
        self.f_offset_y = MDTextField(hint_text="Y", text=f"{oy_mm/10:.2f}")
        offset_row.add_widget(self.f_offset_x)
        offset_row.add_widget(self.f_offset_y)
        offset_card.add_widget(offset_row)
        offset_btns = MDBoxLayout(spacing=dp(8), size_hint_y=None, height=dp(40))
        offset_btns.add_widget(MDFlatButton(text="ENREGISTRER", on_release=lambda x: self._save_offset()))
        offset_btns.add_widget(MDFlatButton(text="RÉINITIALISER (haut-gauche)",
                                              on_release=lambda x: self._reset_offset()))
        offset_card.add_widget(offset_btns)
        col.add_widget(offset_card)

        # ---------------- Test print ----------------
        test_row = MDBoxLayout(spacing=dp(8), size_hint_y=None, height=dp(48))
        test_row.add_widget(MDRaisedButton(text="Grille de test", size_hint_x=1,
                                             on_release=lambda x: self._print_test_grid()))
        col.add_widget(test_row)

        col.add_widget(MDLabel(text="Champs imprimés", font_style="Subtitle1",
                                 size_hint_y=None, height=dp(30)))

        positions = self.db.get_field_positions()
        for key in FIELD_ORDER:
            pos = positions.get(key)
            if not pos:
                continue
            col.add_widget(self._field_row(key, pos))

        scroll.add_widget(col)
        self.add_widget(scroll)

    def _open_step_menu(self, button):
        items = [{"text": f"{s} cm", "on_release": lambda s=s: self._set_step(s)} for s in STEPS]
        MDDropdownMenu(caller=button, items=items, width_mult=3).open()

    def _set_step(self, s):
        self.step = float(s)
        self.step_btn.text = f"{s} cm"

    # ------------------------------------------------------------------
    def _field_row(self, key, pos):
        meta = FIELDS[key]
        card = MDCard(orientation="vertical", padding=dp(10), spacing=dp(6),
                       size_hint_y=None, adaptive_height=True, radius=[6], elevation=1)
        card.add_widget(MDLabel(text=meta["label"], font_style="Caption", bold=True,
                                  size_hint_y=None, height=dp(18)))

        row = MDBoxLayout(spacing=dp(6), size_hint_y=None, height=dp(48))
        x_cm = pos["x_mm"] / 10.0
        y_cm = pos["y_mm"] / 10.0
        f_x = MDTextField(hint_text="X (cm)", text=f"{x_cm:.2f}", size_hint_x=0.3)
        f_y = MDTextField(hint_text="Y (cm)", text=f"{y_cm:.2f}", size_hint_x=0.3)
        row.add_widget(f_x)
        left_btn = MDIconButton(icon="arrow-left", on_release=lambda x: self._nudge(key, f_x, -1))
        right_btn = MDIconButton(icon="arrow-right", on_release=lambda x: self._nudge(key, f_x, 1))
        up_btn = MDIconButton(icon="arrow-up", on_release=lambda x: self._nudge(key, f_y, -1))
        down_btn = MDIconButton(icon="arrow-down", on_release=lambda x: self._nudge(key, f_y, 1))
        row.add_widget(left_btn)
        row.add_widget(right_btn)
        row.add_widget(f_y)
        row.add_widget(up_btn)
        row.add_widget(down_btn)
        card.add_widget(row)

        apply_btn = MDFlatButton(text="Appliquer",
                                   on_release=lambda x: self._apply_row(key, f_x, f_y))
        card.add_widget(apply_btn)

        self.row_widgets[key] = {"x": f_x, "y": f_y}
        return card

    def _nudge(self, key, field, direction):
        try:
            current = float(field.text.replace(",", "."))
        except ValueError:
            current = 0.0
        new_val = max(0.0, round(current + direction * self.step, 2))
        field.text = f"{new_val:.2f}"
        widgets = self.row_widgets[key]
        self._apply_row(key, widgets["x"], widgets["y"])

    def _apply_row(self, key, f_x, f_y):
        try:
            x_cm = float(f_x.text.replace(",", "."))
            y_cm = float(f_y.text.replace(",", "."))
        except ValueError:
            show_message("X et Y doivent être des nombres.")
            return
        self.db.update_field_position(key, x_mm=x_cm * 10, y_mm=y_cm * 10)

    # ------------------------------------------------------------------
    def _save_offset(self):
        try:
            ox_cm = float(self.f_offset_x.text.replace(",", "."))
            oy_cm = float(self.f_offset_y.text.replace(",", "."))
        except ValueError:
            show_message("La position doit être un nombre (cm).")
            return
        self.db.set_setting("offset_x_mm", str(ox_cm * 10))
        self.db.set_setting("offset_y_mm", str(oy_cm * 10))
        show_message("Position enregistrée.")

    def _reset_offset(self):
        self.f_offset_x.text = f"{DEFAULT_CARD_OFFSET_X_MM/10:.2f}"
        self.f_offset_y.text = f"{DEFAULT_CARD_OFFSET_Y_MM/10:.2f}"
        self._save_offset()

    def _current_offsets_mm(self):
        try:
            ox_cm = float(self.f_offset_x.text.replace(",", "."))
            oy_cm = float(self.f_offset_y.text.replace(",", "."))
        except ValueError:
            ox_cm, oy_cm = DEFAULT_CARD_OFFSET_X_MM / 10, DEFAULT_CARD_OFFSET_Y_MM / 10
        return ox_cm * 10, oy_cm * 10

    def _print_test_grid(self):
        try:
            ox, oy = self._current_offsets_mm()
            out_dir = get_export_dir()
            path = os.path.join(out_dir, "grille_test.pdf")
            generate_test_grid_pdf(self.db.get_field_positions(), path,
                                     offset_x_mm=ox, offset_y_mm=oy)
            public_path = try_save_to_public_downloads(path, "grille_test.pdf")
            shared = share_pdf(path)
            if shared:
                show_message("Grille de test envoyée.", duration=4)
            elif public_path:
                show_message("Grille dans Téléchargements/Traites — ouvrez Epson iPrint.", duration=5)
            else:
                show_message(f"Grille enregistrée : {path}", duration=5)
        except Exception as e:
            show_message(f"Erreur : {e}", duration=4)
