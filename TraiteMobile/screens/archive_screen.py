# -*- coding: utf-8 -*-
import os
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from ui_helpers import show_message
from kivy.metrics import dp
import datetime

from constants import STATUTS, STATUT_COLORS
from util import fmt_montant, get_print_offsets, get_export_dir, try_save_to_public_downloads, share_pdf
from pdf_gen import generate_traite_pdf


def _hex_to_rgba(hex_color, alpha=1.0):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return (r, g, b, alpha)


class ArchiveScreen(MDBoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.app = app
        self.db = app.db
        self.statut_filter = None
        self.dialog = None
        self._build()

    def _build(self):
        search_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56),
                                   padding=(dp(12), dp(6)), spacing=dp(8))
        self.search_field = MDTextField(hint_text="Rechercher (N° CN, client)...")
        self.search_field.bind(text=lambda inst, val: self._refresh())
        search_row.add_widget(self.search_field)
        self.add_widget(search_row)

        filter_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44),
                                   padding=(dp(12), 0), spacing=dp(6))
        self.filter_btn = MDFlatButton(text="Statut : Tous")
        self.filter_btn.bind(on_release=self._open_filter_menu)
        filter_row.add_widget(self.filter_btn)
        self.add_widget(filter_row)

        self.scroll = MDScrollView()
        self.list_box = MDBoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12),
                                      size_hint_y=None, adaptive_height=True)
        self.scroll.add_widget(self.list_box)
        self.add_widget(self.scroll)

        self._refresh()

    def _open_filter_menu(self, button):
        items = [{"text": "Tous", "on_release": lambda: self._set_filter(None, "Tous")}]
        for key, label in STATUTS.items():
            items.append({"text": label, "on_release": lambda k=key, l=label: self._set_filter(k, l)})
        self.menu = MDDropdownMenu(caller=button, items=items, width_mult=4)
        self.menu.open()

    def _set_filter(self, key, label):
        self.statut_filter = key
        self.filter_btn.text = f"Statut : {label}"
        self.menu.dismiss()
        self._refresh()

    def _refresh(self):
        self.list_box.clear_widgets()
        rows = self.db.list_traites(search=self.search_field.text.strip(),
                                      statut=self.statut_filter)
        if not rows:
            self.list_box.add_widget(MDLabel(text="Aucune traite trouvée.", theme_text_color="Hint",
                                               size_hint_y=None, height=dp(40)))
            return
        for r in rows:
            self.list_box.add_widget(self._traite_card(r))

    def _traite_card(self, r):
        color = _hex_to_rgba(STATUT_COLORS.get(r["statut"], "#666666"))
        card = MDCard(orientation="vertical", padding=dp(10), spacing=dp(4),
                       size_hint_y=None, height=dp(96), radius=[8], elevation=1)
        top = MDBoxLayout(size_hint_y=None, height=dp(24))
        top.add_widget(MDLabel(text=r["tireur_nom"] or "—", font_style="Subtitle1"))
        top.add_widget(MDLabel(text=STATUTS.get(r["statut"], r["statut"]), theme_text_color="Custom",
                                 text_color=color, halign="right", size_hint_x=None, width=dp(90)))
        card.add_widget(top)
        card.add_widget(MDLabel(text=f"N° CN {r['num_cn'] or '—'}  •  {fmt_montant(r['montant'])} DT  "
                                       f"•  Échéance {r['echeance'] or '—'}",
                                  theme_text_color="Hint", font_style="Caption",
                                  size_hint_y=None, height=dp(20)))

        actions = MDBoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4))
        actions.add_widget(MDFlatButton(text="OUVRIR", on_release=lambda x, i=r["id"]: self.app.edit_traite(i)))
        actions.add_widget(MDFlatButton(text="IMPRIMER", on_release=lambda x, i=r["id"]: self._print(i)))
        actions.add_widget(MDFlatButton(text="STATUT", on_release=lambda x, i=r["id"]: self._open_status_dialog(i)))
        card.add_widget(actions)
        return card

    # ------------------------------------------------------------------
    def _open_status_dialog(self, traite_id):
        buttons = []
        for key, label in STATUTS.items():
            buttons.append(MDFlatButton(text=label,
                                          on_release=lambda x, k=key, i=traite_id: self._set_statut(i, k)))
        self.dialog = MDDialog(title="Changer le statut", type="simple",
                                 items=[], buttons=buttons + [
                                    MDFlatButton(text="ANNULER", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()

    def _set_statut(self, traite_id, statut):
        date_paiement = datetime.date.today().strftime("%d/%m/%Y") if statut == "payee" else None
        self.db.set_statut(traite_id, statut, date_paiement)
        self.dialog.dismiss()
        self._refresh()

    def _print(self, traite_id):
        traite = self.db.get_traite(traite_id)
        field_positions = self.db.get_field_positions()
        offset_x, offset_y = get_print_offsets(self.db)
        out_dir = get_export_dir()
        safe_cn = (traite["num_cn"] or f"id{traite_id}").replace("/", "-").replace("\\", "-")
        filename = f"traite_{safe_cn}.pdf"
        out_path = os.path.join(out_dir, filename)
        try:
            generate_traite_pdf(dict(traite), field_positions, out_path,
                                  offset_x_mm=offset_x, offset_y_mm=offset_y)
            public_path = try_save_to_public_downloads(out_path, filename)
            shared = share_pdf(out_path)
            if shared:
                msg = "Impression envoyée."
            elif public_path:
                msg = f"PDF enregistré dans Téléchargements/Traites. Ouvrez Epson iPrint pour imprimer."
            else:
                msg = f"PDF enregistré : {out_path}. Ouvrez Epson iPrint pour imprimer."
            show_message(msg, duration=4)
        except Exception as e:
            show_message(f"Erreur : {e}", duration=4)
