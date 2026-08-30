# -*- coding: utf-8 -*-
import os
import csv
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.scrollview import MDScrollView
from kivy.metrics import dp

from constants import STATUTS, STATUT_COLORS
from util import fmt_montant, get_export_dir
from ui_helpers import show_message


def _hex_to_rgba(hex_color, alpha=1.0):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return (r, g, b, alpha)


class RapportsScreen(MDBoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.app = app
        self.db = app.db
        self._build()

    def _build(self):
        scroll = MDScrollView()
        content = MDBoxLayout(orientation="vertical", spacing=dp(12), padding=dp(14),
                                size_hint_y=None, adaptive_height=True)

        stats, total_general, total_n = self.db.stats()
        grid = MDGridLayout(cols=2, spacing=dp(10), size_hint_y=None, adaptive_height=True)
        grid.add_widget(self._stat_card("Total", str(total_n), f"{fmt_montant(total_general)} DT",
                                          "222222"))
        grid.add_widget(self._stat_card("En attente", str(stats["en_attente"]["n"]),
                                          f"{fmt_montant(stats['en_attente']['total'])} DT",
                                          STATUT_COLORS["en_attente"].lstrip("#")))
        grid.add_widget(self._stat_card("Payées", str(stats["payee"]["n"]),
                                          f"{fmt_montant(stats['payee']['total'])} DT",
                                          STATUT_COLORS["payee"].lstrip("#")))
        grid.add_widget(self._stat_card("Non payées", str(stats["non_payee"]["n"]),
                                          f"{fmt_montant(stats['non_payee']['total'])} DT",
                                          STATUT_COLORS["non_payee"].lstrip("#")))
        content.add_widget(grid)

        export_btn = MDRaisedButton(text="Exporter en CSV (Excel)", size_hint_x=1)
        export_btn.bind(on_release=lambda x: self._export_csv())
        content.add_widget(export_btn)

        content.add_widget(MDLabel(text="Toutes les traites", font_style="Subtitle1",
                                     size_hint_y=None, height=dp(30)))

        self.all_rows = self.db.list_traites()
        if not self.all_rows:
            content.add_widget(MDLabel(text="Aucune traite enregistrée.", theme_text_color="Hint",
                                         size_hint_y=None, height=dp(40)))
        else:
            for r in self.all_rows:
                content.add_widget(self._row_card(r))

        scroll.add_widget(content)
        self.add_widget(scroll)

    def _row_card(self, r):
        color = _hex_to_rgba(STATUT_COLORS.get(r["statut"], "#666666"))
        card = MDCard(orientation="vertical", padding=dp(8), size_hint_y=None, height=dp(64),
                       radius=[6], elevation=1)
        top = MDBoxLayout(size_hint_y=None, height=dp(22))
        top.add_widget(MDLabel(text=r["tireur_nom"] or "—", font_style="Body1"))
        top.add_widget(MDLabel(text=STATUTS.get(r["statut"], r["statut"]), theme_text_color="Custom",
                                 text_color=color, halign="right", size_hint_x=None, width=dp(90)))
        card.add_widget(top)
        card.add_widget(MDLabel(text=f"N° {r['num_cn'] or '—'}  •  {fmt_montant(r['montant'])} DT",
                                  theme_text_color="Hint", font_style="Caption",
                                  size_hint_y=None, height=dp(18)))
        return card

    def _stat_card(self, title, value, subtitle, hex_color):
        card = MDCard(orientation="vertical", padding=dp(12), spacing=dp(4),
                       size_hint_y=None, height=dp(90), radius=[10], elevation=1)
        card.add_widget(MDLabel(text=title, theme_text_color="Custom",
                                  text_color=_hex_to_rgba(hex_color), font_style="Caption",
                                  size_hint_y=None, height=dp(18)))
        card.add_widget(MDLabel(text=value, font_style="H5", size_hint_y=None, height=dp(32)))
        card.add_widget(MDLabel(text=subtitle, theme_text_color="Hint", font_style="Caption",
                                  size_hint_y=None, height=dp(18)))
        return card

    def _export_csv(self):
        try:
            out_dir = get_export_dir()
            path = os.path.join(out_dir, "recap_traites.csv")
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["N° CN", "Client", "Montant (DT)", "Montant en lettres",
                                  "Date création", "Échéance", "Statut", "Date paiement"])
                for r in self.all_rows:
                    writer.writerow([
                        r["num_cn"], r["tireur_nom"], r["montant"], r["montant_lettres"],
                        r["date_creation"], r["echeance"],
                        STATUTS.get(r["statut"], r["statut"]), r["date_paiement"] or "",
                    ])
            show_message(f"Export enregistré : {path}", duration=4)
        except Exception as e:
            show_message(f"Erreur : {e}", duration=4)
