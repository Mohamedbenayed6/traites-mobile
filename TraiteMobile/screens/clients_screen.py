# -*- coding: utf-8 -*-
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, TwoLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.card import MDCard
from kivy.metrics import dp


class ClientsScreen(MDBoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.app = app
        self.db = app.db
        self.dialog = None
        self._build()

    def _build(self):
        search_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56),
                                   padding=(dp(12), dp(6)), spacing=dp(8))
        self.search_field = MDTextField(hint_text="Rechercher un client...")
        self.search_field.bind(text=lambda inst, val: self._refresh())
        search_row.add_widget(self.search_field)
        self.add_widget(search_row)

        new_btn = MDRaisedButton(text="+ Nouveau client", size_hint_x=1,
                                   pos_hint={"center_x": 0.5})
        new_btn.bind(on_release=lambda x: self._open_dialog())
        btn_row = MDBoxLayout(size_hint_y=None, height=dp(48), padding=(dp(12), 0))
        btn_row.add_widget(new_btn)
        self.add_widget(btn_row)

        self.scroll = MDScrollView()
        self.list_box = MDBoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12),
                                      size_hint_y=None, adaptive_height=True)
        self.scroll.add_widget(self.list_box)
        self.add_widget(self.scroll)

        self._refresh()

    def _refresh(self):
        self.list_box.clear_widgets()
        clients = self.db.list_clients(self.search_field.text.strip())
        if not clients:
            self.list_box.add_widget(MDLabel(text="Aucun client trouvé.", theme_text_color="Hint",
                                               size_hint_y=None, height=dp(40)))
            return
        for c in clients:
            self.list_box.add_widget(self._client_card(c))

    def _client_card(self, c):
        card = MDCard(orientation="horizontal", padding=dp(10), spacing=dp(6),
                       size_hint_y=None, height=dp(70), radius=[8], elevation=1)
        info = MDBoxLayout(orientation="vertical")
        info.add_widget(MDLabel(text=c["nom"], font_style="Subtitle1", size_hint_y=None, height=dp(26)))
        sub = c["adresse"] or c["telephone"] or "—"
        info.add_widget(MDLabel(text=sub, theme_text_color="Hint", font_style="Caption",
                                  size_hint_y=None, height=dp(20)))
        card.add_widget(info)
        edit_btn = MDIconButton(icon="pencil")
        edit_btn.bind(on_release=lambda x, cid=c["id"]: self._open_dialog(cid))
        card.add_widget(edit_btn)
        return card

    # ------------------------------------------------------------------
    def _open_dialog(self, client_id=None):
        client = self.db.get_client(client_id) if client_id else None
        self.editing_client_id = client_id

        self.f_nom = MDTextField(hint_text="Nom *", text=client["nom"] if client else "")
        self.f_adresse = MDTextField(hint_text="Adresse", text=client["adresse"] if client else "")
        self.f_rib = MDTextField(hint_text="RIB / RIP", text=client["rib"] if client else "")
        self.f_tel = MDTextField(hint_text="Téléphone", text=client["telephone"] if client else "")

        content = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None,
                                adaptive_height=True, padding=(0, dp(20), 0, dp(10)))
        for f in (self.f_nom, self.f_adresse, self.f_rib, self.f_tel):
            content.add_widget(f)

        buttons = [
            MDFlatButton(text="ANNULER", on_release=lambda x: self.dialog.dismiss()),
            MDRaisedButton(text="ENREGISTRER", on_release=lambda x: self._save_client()),
        ]
        if client_id:
            buttons.insert(0, MDFlatButton(text="SUPPRIMER", theme_text_color="Custom",
                                             text_color=(0.75, 0.2, 0.2, 1),
                                             on_release=lambda x: self._delete_client()))

        self.dialog = MDDialog(
            title="Modifier le client" if client else "Nouveau client",
            type="custom", content_cls=content, buttons=buttons,
        )
        self.dialog.open()

    def _save_client(self):
        nom = self.f_nom.text.strip()
        if not nom:
            self.f_nom.error = True
            return
        if self.editing_client_id:
            self.db.update_client(self.editing_client_id, nom, self.f_adresse.text.strip(),
                                    self.f_rib.text.strip(), self.f_tel.text.strip())
        else:
            self.db.add_client(nom, self.f_adresse.text.strip(), self.f_rib.text.strip(),
                                 self.f_tel.text.strip())
        self.dialog.dismiss()
        self._refresh()

    def _delete_client(self):
        if self.editing_client_id:
            self.db.delete_client(self.editing_client_id)
        self.dialog.dismiss()
        self._refresh()
