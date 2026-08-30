# -*- coding: utf-8 -*-
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, ThreeLineListItem
from kivy.metrics import dp

from constants import STATUTS, STATUT_COLORS
from util import fmt_montant


def _hex_to_rgba(hex_color, alpha=1.0):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return (r, g, b, alpha)


class DashboardScreen(MDBoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.app = app
        self.db = app.db
        self._build()

    def _build(self):
        scroll = MDScrollView()
        content = MDBoxLayout(orientation="vertical", spacing=dp(12), padding=dp(12),
                               size_hint_y=None, adaptive_height=True)

        btn = MDRaisedButton(text="+ Nouvelle traite", size_hint_x=1,
                              on_release=lambda x: self.app.show_screen("nouvelle_traite"))
        content.add_widget(btn)

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

        content.add_widget(MDLabel(text="Traites récentes", font_style="Subtitle1",
                                     size_hint_y=None, height=dp(30)))

        rows = self.db.list_traites()[:15]
        if not rows:
            content.add_widget(MDLabel(text="Aucune traite enregistrée pour le moment.",
                                         theme_text_color="Hint", size_hint_y=None, height=dp(40)))
        else:
            mlist = MDList(size_hint_y=None, adaptive_height=True)
            for r in rows:
                statut_label = STATUTS.get(r["statut"], r["statut"])
                item = ThreeLineListItem(
                    text=f"{r['tireur_nom'] or '—'}  ({statut_label})",
                    secondary_text=f"N° CN: {r['num_cn'] or '—'}   |   {fmt_montant(r['montant'])} DT",
                    tertiary_text=f"Échéance : {r['echeance'] or '—'}",
                    on_release=self._make_open_handler(r["id"]),
                )
                mlist.add_widget(item)
            content.add_widget(mlist)

        scroll.add_widget(content)
        self.add_widget(scroll)

    def _make_open_handler(self, traite_id):
        def handler(*args):
            self.app.edit_traite(traite_id)
        return handler

    def _stat_card(self, title, value, subtitle, hex_color):
        card = MDCard(orientation="vertical", padding=dp(12), spacing=dp(4),
                       size_hint_y=None, height=dp(90), radius=[10],
                       md_bg_color=(1, 1, 1, 1), elevation=1)
        card.add_widget(MDLabel(text=title, theme_text_color="Custom",
                                  text_color=_hex_to_rgba(hex_color), font_style="Caption",
                                  size_hint_y=None, height=dp(18)))
        card.add_widget(MDLabel(text=value, font_style="H5", size_hint_y=None, height=dp(32)))
        card.add_widget(MDLabel(text=subtitle, theme_text_color="Hint", font_style="Caption",
                                  size_hint_y=None, height=dp(18)))
        return card
