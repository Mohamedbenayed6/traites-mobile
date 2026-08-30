# -*- coding: utf-8 -*-
import os
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import MDDialog
from kivy.metrics import dp

from constants import STATUTS
from num2words_fr import montant_en_lettres
from util import (today_str, add_days_str, get_print_offsets, get_export_dir,
                    try_save_to_public_downloads, share_pdf)
from pdf_gen import generate_traite_pdf
from ui_helpers import show_message

VALEUR_EN_OPTIONS = ["DINARS", "MILLIMES"]
PROTESTABLE_OPTIONS = [("", "Non défini"), ("oui", "Oui"), ("non", "Non")]


class SectionTitle(MDLabel):
    def __init__(self, text, **kwargs):
        super().__init__(text=text, font_style="Subtitle1", bold=True,
                          size_hint_y=None, height=dp(34), **kwargs)


class TraiteFormScreen(MDBoxLayout):
    def __init__(self, app, traite_id=None, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.app = app
        self.db = app.db
        self.traite_id = traite_id
        self.existing = self.db.get_traite(traite_id) if traite_id else None
        self._payer_ordre_manual = bool(self.existing)
        self.dialog = None
        self._build()
        if self.existing:
            self._load_existing()
        else:
            self._prefill_defaults()

    # ------------------------------------------------------------------
    def _field(self, hint, multiline=False, **kwargs):
        tf = MDTextField(hint_text=hint, multiline=multiline, **kwargs)
        if not multiline:
            tf.size_hint_y = None
            tf.height = dp(52)
        return tf

    def _build(self):
        scroll = MDScrollView()
        col = MDBoxLayout(orientation="vertical", spacing=dp(6), padding=dp(14),
                            size_hint_y=None, adaptive_height=True)

        # ---------------- Tiré = vos informations ----------------
        col.add_widget(SectionTitle("Tiré — vos informations (pré-remplies)"))
        self.e_tire_nom = self._field("Nom / Raison sociale")
        col.add_widget(self.e_tire_nom)
        self.txt_tire_adresse = self._field("Adresse", multiline=True, size_hint_y=None, height=dp(70))
        col.add_widget(self.txt_tire_adresse)

        rib_label = MDLabel(text="RIB (chaque case peut avoir une longueur différente)",
                              theme_text_color="Hint", font_style="Caption",
                              size_hint_y=None, height=dp(20))
        col.add_widget(rib_label)
        rib_row = MDGridLayout(cols=4, spacing=dp(6), size_hint_y=None, height=dp(52))
        self.e_code_etab = self._field("Étab.")
        self.e_code_agence = self._field("Agence")
        self.e_num_compte = self._field("N° compte")
        self.e_cle = self._field("Clé")
        for w in (self.e_code_etab, self.e_code_agence, self.e_num_compte, self.e_cle):
            rib_row.add_widget(w)
        col.add_widget(rib_row)

        # ---------------- Tireur = client ----------------
        col.add_widget(SectionTitle("Tireur — le client concerné"))
        self.e_tireur_nom = self._field("Nom du client")
        self.e_tireur_nom.bind(text=self._on_tireur_text)
        col.add_widget(self.e_tireur_nom)
        hint_lbl = MDLabel(text="« Payer à l'ordre de » reprend ce nom automatiquement",
                             theme_text_color="Hint", font_style="Caption",
                             size_hint_y=None, height=dp(20))
        col.add_widget(hint_lbl)

        # ---------------- Montant ----------------
        col.add_widget(SectionTitle("Montant"))
        montant_row = MDBoxLayout(spacing=dp(6), size_hint_y=None, height=dp(52))
        self.e_montant = self._field("Montant en chiffres (DT)")
        self.e_montant.bind(focus=self._on_montant_focus)
        montant_row.add_widget(self.e_montant)
        recalc_btn = MDFlatButton(text="Recalculer", on_release=lambda x: self._recalc_lettres())
        montant_row.add_widget(recalc_btn)
        col.add_widget(montant_row)
        self.txt_montant_lettres = self._field("Montant en lettres", multiline=True,
                                                  size_hint_y=None, height=dp(70))
        col.add_widget(self.txt_montant_lettres)

        # ---------------- Dates & lieu ----------------
        col.add_widget(SectionTitle("Dates & lieu"))
        self.e_lieu_creation = self._field("Lieu de création")
        col.add_widget(self.e_lieu_creation)
        self.e_date_creation = self._field("Date de création (jj/mm/aaaa)")
        col.add_widget(self.e_date_creation)
        self.e_echeance = self._field("Échéance (jj/mm/aaaa)")
        col.add_widget(self.e_echeance)
        quick_row = MDBoxLayout(spacing=dp(6), size_hint_y=None, height=dp(40))
        for jours in (30, 60, 90, 120):
            quick_row.add_widget(MDFlatButton(text=f"+{jours}j",
                                                on_release=lambda x, j=jours: self._set_echeance(j)))
        col.add_widget(quick_row)
        self.e_domiciliation = self._field("Domiciliation (banque/agence)")
        col.add_widget(self.e_domiciliation)

        self.valeur_en_btn = MDFlatButton(text="Valeur en : DINARS", size_hint_x=1)
        self.valeur_en_btn.bind(on_release=self._open_valeur_en_menu)
        col.add_widget(self.valeur_en_btn)
        self._valeur_en = "DINARS"

        # ---------------- Référence & statut ----------------
        col.add_widget(SectionTitle("Référence & statut"))
        self.e_num_cn = self._field("N° CN (déjà imprimé sur le papier)")
        col.add_widget(self.e_num_cn)

        self.statut_btn = MDFlatButton(text="Statut : En attente", size_hint_x=1)
        self.statut_btn.bind(on_release=self._open_statut_menu)
        col.add_widget(self.statut_btn)
        self._statut = "en_attente"

        self.e_nom_cedant = self._field("Payer à l'ordre de")
        self.e_nom_cedant.bind(text=self._on_payer_ordre_text)
        col.add_widget(self.e_nom_cedant)

        self.protestable_btn = MDFlatButton(text="Protestable : Non défini", size_hint_x=1)
        self.protestable_btn.bind(on_release=self._open_protestable_menu)
        col.add_widget(self.protestable_btn)
        self._protestable = ""

        self.txt_notes = self._field("Notes (optionnel)", multiline=True, size_hint_y=None, height=dp(70))
        col.add_widget(self.txt_notes)

        # ---------------- Actions ----------------
        actions1 = MDBoxLayout(spacing=dp(8), size_hint_y=None, height=dp(48), padding=(0, dp(10)))
        actions1.add_widget(MDRaisedButton(text="Enregistrer", on_release=lambda x: self._save()))
        actions1.add_widget(MDRaisedButton(text="Enregistrer + Imprimer", md_bg_color=(0.71, 0.2, 0.12, 1),
                                             on_release=lambda x: self._save_and_print()))
        col.add_widget(actions1)
        actions2 = MDBoxLayout(spacing=dp(8), size_hint_y=None, height=dp(48))
        actions2.add_widget(MDFlatButton(text="Aperçu PDF", on_release=lambda x: self._preview()))
        actions2.add_widget(MDFlatButton(text="Annuler",
                                           on_release=lambda x: self.app.show_screen("archive")))
        col.add_widget(actions2)
        if self.existing:
            col.add_widget(MDFlatButton(text="Supprimer cette traite", theme_text_color="Custom",
                                          text_color=(0.75, 0.2, 0.2, 1),
                                          on_release=lambda x: self._delete()))

        scroll.add_widget(col)
        self.add_widget(scroll)

    # ------------------------------------------------------------------
    def _open_valeur_en_menu(self, button):
        items = [{"text": v, "on_release": lambda v=v: self._set_valeur_en(v)} for v in VALEUR_EN_OPTIONS]
        MDDropdownMenu(caller=button, items=items, width_mult=3).open()

    def _set_valeur_en(self, v):
        self._valeur_en = v
        self.valeur_en_btn.text = f"Valeur en : {v}"

    def _open_statut_menu(self, button):
        items = [{"text": label, "on_release": lambda k=k, l=label: self._set_statut(k, l)}
                 for k, label in STATUTS.items()]
        MDDropdownMenu(caller=button, items=items, width_mult=3).open()

    def _set_statut(self, key, label):
        self._statut = key
        self.statut_btn.text = f"Statut : {label}"

    def _open_protestable_menu(self, button):
        items = [{"text": label, "on_release": lambda k=k, l=label: self._set_protestable(k, l)}
                 for k, label in PROTESTABLE_OPTIONS]
        MDDropdownMenu(caller=button, items=items, width_mult=3).open()

    def _set_protestable(self, key, label):
        self._protestable = key
        self.protestable_btn.text = f"Protestable : {label}"

    # ------------------------------------------------------------------
    def _prefill_defaults(self):
        self.e_tire_nom.text = self.db.get_setting("mon_nom_default", "")
        self.txt_tire_adresse.text = self.db.get_setting("mon_adresse_default", "")
        self.e_code_etab.text = self.db.get_setting("mon_code_etab_default", "")
        self.e_code_agence.text = self.db.get_setting("mon_code_agence_default", "")
        self.e_num_compte.text = self.db.get_setting("mon_num_compte_default", "")
        self.e_cle.text = self.db.get_setting("mon_cle_default", "")
        self.e_lieu_creation.text = self.db.get_setting("lieu_creation_default", "")
        self.e_domiciliation.text = self.db.get_setting("domiciliation_default", "")
        self._set_valeur_en(self.db.get_setting("valeur_en_default", "DINARS"))
        self.e_date_creation.text = today_str()

    def _load_existing(self):
        t = self.existing
        self.e_tire_nom.text = t["tire_nom"] or ""
        self.txt_tire_adresse.text = t["tire_adresse"] or ""
        code_etab = t["tire_code_etab"] or ""
        code_agence = t["tire_code_agence"] or ""
        num_compte = t["tire_num_compte"] or ""
        cle = t["tire_cle"] or ""
        if not any([code_etab, code_agence, num_compte, cle]) and t["tire_rib"]:
            digits = "".join(ch for ch in t["tire_rib"] if ch.isdigit())
            code_etab, code_agence, num_compte, cle = (
                digits[0:2], digits[2:5], digits[5:18], digits[18:20])
        self.e_code_etab.text = code_etab
        self.e_code_agence.text = code_agence
        self.e_num_compte.text = num_compte
        self.e_cle.text = cle
        self.e_tireur_nom.text = t["tireur_nom"] or ""
        self.e_nom_cedant.text = t["nom_cedant"] or ""
        self.e_montant.text = str(t["montant"]) if t["montant"] is not None else ""
        self.txt_montant_lettres.text = t["montant_lettres"] or ""
        self.e_lieu_creation.text = t["lieu_creation"] or ""
        self.e_date_creation.text = t["date_creation"] or ""
        self.e_echeance.text = t["echeance"] or ""
        self.e_domiciliation.text = t["domiciliation"] or ""
        self._set_valeur_en(t["valeur_en"] or "DINARS")
        self.e_num_cn.text = t["num_cn"] or ""
        self.txt_notes.text = t["notes"] or ""
        statut_key = t["statut"] or "en_attente"
        self._set_statut(statut_key, STATUTS.get(statut_key, STATUTS["en_attente"]))
        prot = t["protestable"] or ""
        label = dict(PROTESTABLE_OPTIONS).get(prot, "Non défini")
        self._set_protestable(prot, label)

    # ------------------------------------------------------------------
    def _set_echeance(self, jours):
        base = self.e_date_creation.text.strip() or today_str()
        self.e_echeance.text = add_days_str(base, jours)

    def _on_tireur_text(self, instance, value):
        self._sync_payer_ordre()

    def _sync_payer_ordre(self):
        if self._payer_ordre_manual:
            return
        self.e_nom_cedant.text = self.e_tireur_nom.text

    def _on_payer_ordre_text(self, instance, value):
        # Ne marque "modifié manuellement" que si le texte diverge de ce que
        # la synchronisation automatique aurait mis (évite de se déclencher
        # lors de la synchronisation elle-même).
        if value != self.e_tireur_nom.text:
            self._payer_ordre_manual = True

    def _on_montant_focus(self, instance, has_focus):
        if not has_focus:
            self._recalc_lettres(silent=True)

    def _recalc_lettres(self, silent=False):
        raw = self.e_montant.text.strip().replace(",", ".")
        if not raw:
            return
        try:
            montant = float(raw)
        except ValueError:
            if not silent:
                show_message("Le montant doit être un nombre (ex: 1250.500)")
            return
        self.txt_montant_lettres.text = montant_en_lettres(montant)

    # ------------------------------------------------------------------
    def _collect_data(self):
        raw_montant = self.e_montant.text.strip().replace(",", ".")
        try:
            montant = float(raw_montant) if raw_montant else 0.0
        except ValueError:
            show_message("Le montant doit être un nombre.")
            return None

        tireur_nom = self.e_tireur_nom.text.strip()
        num_cn = self.e_num_cn.text.strip()
        if not tireur_nom:
            show_message("Merci d'indiquer le nom du client (Tireur).")
            return None

        client_id = self.db.get_or_create_client(tireur_nom)
        code_etab = self.e_code_etab.text.strip()
        code_agence = self.e_code_agence.text.strip()
        num_compte = self.e_num_compte.text.strip()
        cle = self.e_cle.text.strip()

        data = {
            "num_cn": num_cn,
            "tireur_nom": tireur_nom,
            "tireur_adresse": "",
            "client_id": client_id,
            "tire_nom": self.e_tire_nom.text.strip(),
            "tire_adresse": self.txt_tire_adresse.text.strip(),
            "tire_rib": f"{code_etab}{code_agence}{num_compte}{cle}",
            "tire_code_etab": code_etab,
            "tire_code_agence": code_agence,
            "tire_num_compte": num_compte,
            "tire_cle": cle,
            "nom_cedant": self.e_nom_cedant.text.strip(),
            "montant": montant,
            "montant_lettres": self.txt_montant_lettres.text.strip(),
            "lieu_creation": self.e_lieu_creation.text.strip(),
            "date_creation": self.e_date_creation.text.strip(),
            "echeance": self.e_echeance.text.strip(),
            "domiciliation": self.e_domiciliation.text.strip(),
            "valeur_en": self._valeur_en,
            "protestable": self._protestable,
            "statut": self._statut,
            "date_paiement": self.existing["date_paiement"] if self.existing else None,
            "notes": self.txt_notes.text.strip(),
        }
        return data

    def _remember_defaults(self, data):
        self.db.set_setting("mon_nom_default", data["tire_nom"])
        self.db.set_setting("mon_adresse_default", data["tire_adresse"])
        self.db.set_setting("mon_code_etab_default", data["tire_code_etab"])
        self.db.set_setting("mon_code_agence_default", data["tire_code_agence"])
        self.db.set_setting("mon_num_compte_default", data["tire_num_compte"])
        self.db.set_setting("mon_cle_default", data["tire_cle"])
        self.db.set_setting("lieu_creation_default", data["lieu_creation"])
        self.db.set_setting("domiciliation_default", data["domiciliation"])
        self.db.set_setting("valeur_en_default", data["valeur_en"])

    def _save(self, silent=False):
        data = self._collect_data()
        if data is None:
            return None
        if self.existing:
            self.db.update_traite(self.traite_id, data)
            saved_id = self.traite_id
        else:
            saved_id = self.db.add_traite(data)
        self._remember_defaults(data)
        if not silent:
            show_message("Traite enregistrée avec succès.")
            self.app.show_screen("archive")
        return saved_id

    def _generate_pdf(self, saved_id):
        field_positions = self.db.get_field_positions()
        offset_x, offset_y = get_print_offsets(self.db)
        traite = self.db.get_traite(saved_id)
        out_dir = get_export_dir()
        safe_cn = (traite["num_cn"] or f"id{saved_id}").replace("/", "-").replace("\\", "-")
        filename = f"traite_{safe_cn}.pdf"
        out_path = os.path.join(out_dir, filename)
        generate_traite_pdf(dict(traite), field_positions, out_path,
                              offset_x_mm=offset_x, offset_y_mm=offset_y)
        return out_path, filename

    def _save_and_print(self):
        saved_id = self._save(silent=True)
        if saved_id is None:
            return
        try:
            out_path, filename = self._generate_pdf(saved_id)
            public_path = try_save_to_public_downloads(out_path, filename)
            shared = share_pdf(out_path)
            if shared:
                show_message("Traite enregistrée. Impression envoyée.", duration=4)
            elif public_path:
                show_message("Traite enregistrée. PDF dans Téléchargements/Traites — "
                              "ouvrez Epson iPrint.", duration=5)
            else:
                show_message(f"Traite enregistrée. PDF : {out_path}", duration=5)
        except Exception as e:
            show_message(f"Erreur : {e}", duration=4)
        self.app.show_screen("archive")

    def _preview(self):
        data = self._collect_data()
        if data is None:
            return
        try:
            field_positions = self.db.get_field_positions()
            offset_x, offset_y = get_print_offsets(self.db)
            out_dir = get_export_dir()
            out_path = os.path.join(out_dir, "apercu_temp.pdf")
            generate_traite_pdf(data, field_positions, out_path,
                                  offset_x_mm=offset_x, offset_y_mm=offset_y)
            share_pdf(out_path)
            show_message(f"Aperçu généré : {out_path}", duration=4)
        except Exception as e:
            show_message(f"Erreur : {e}", duration=4)

    def _delete(self):
        self.dialog = MDDialog(
            title="Confirmer",
            text="Supprimer définitivement cette traite ?",
            buttons=[
                MDFlatButton(text="ANNULER", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="SUPPRIMER", theme_text_color="Custom",
                              text_color=(0.75, 0.2, 0.2, 1),
                              on_release=lambda x: self._confirm_delete()),
            ],
        )
        self.dialog.open()

    def _confirm_delete(self):
        self.db.delete_traite(self.traite_id)
        self.dialog.dismiss()
        self.app.show_screen("archive")
