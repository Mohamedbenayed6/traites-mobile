# -*- coding: utf-8 -*-
"""
Définition des champs imprimables sur la Lettre de Change (kembyela) tunisienne.

Ces positions reproduisent EXACTEMENT le fichier de référence validé par
l'utilisateur (mesures à la règle + ajustements testés en conditions
réelles). Système de mesure (en cm, depuis les bords de la carte) :
    x = distance entre le bord DROIT de la carte et le bord GAUCHE de la
        zone où l'on peut écrire
    y = distance entre le bord HAUT de la carte et le bord HAUT de la zone
    k = largeur de la zone (s'étend vers la DROITE depuis le point x)
    a = hauteur de la zone (s'étend vers le BAS depuis le point y)

Conversion : la zone va, depuis le bord GAUCHE de la carte, de (17.4 - x) à
(17.4 - x + k) horizontalement. Vérifié : les 4 cases du RIB s'emboîtent
bout à bout avec cette formule.

Ancrage sur la feuille A4 : la kembyela est imprimée collée au coin
HAUT-GAUCHE de la feuille A4 (aucun décalage) -- confirmé par les tests
réels de l'utilisateur (une kembyela seule, sans feuille A4 autour,
s'aligne sur le repère haut-gauche de l'imprimante).
"""

CARD_WIDTH_CM = 17.4
CARD_HEIGHT_CM = 11.5
CARD_WIDTH_MM = CARD_WIDTH_CM * 10
CARD_HEIGHT_MM = CARD_HEIGHT_CM * 10

A4_WIDTH_MM = 210.0
A4_HEIGHT_MM = 297.0

# Position de la kembyela sur la feuille A4 : collée au coin HAUT-GAUCHE.
DEFAULT_CARD_OFFSET_X_MM = 0.0
DEFAULT_CARD_OFFSET_Y_MM = 0.0


def _zone(x_cm, y_cm, k_cm, a_cm):
    """Convertit (x, y, k, a) mesurés en cm (système de l'utilisateur) en
    (x_mm, y_mm, width_mm, height_mm) mesurés depuis le coin HAUT-GAUCHE,
    tel qu'utilisé par le moteur d'impression."""
    left_mm = CARD_WIDTH_MM - (x_cm * 10)
    top_mm = y_cm * 10
    width_mm = k_cm * 10
    height_mm = a_cm * 10
    return {"x": round(left_mm, 1), "y": round(top_mm, 1),
            "width_mm": round(width_mm, 1), "height_mm": round(height_mm, 1)}


# mode :
#   "single"    -> une seule ligne, la police RÉTRÉCIT automatiquement pour
#                  toujours tenir dans la case (comme le fichier de référence)
#   "multiline" -> texte qui peut retourner à la ligne dans la largeur
#   "cross"     -> dessine une croix (X) graphique, pas de texte

FIELDS = {
    "montant_chiffres": {
        "label": "Montant (chiffres)",
        **_zone(x_cm=4.0, y_cm=2.62, k_cm=4.1, a_cm=0.6),
        "size": 10, "align": "left", "mode": "single", "bold": True, "default_on": True,
    },
    "montant_chiffres_2": {
        "label": "Montant (chiffres) — 2e case",
        **_zone(x_cm=4.0, y_cm=4.12, k_cm=4.1, a_cm=0.5),
        "size": 10, "align": "left", "mode": "single", "bold": True, "default_on": True,
    },
    "lieu_creation": {
        "label": "Lieu de création",
        **_zone(x_cm=8.85, y_cm=1.1, k_cm=3.0, a_cm=0.4),
        "size": 9, "align": "left", "mode": "single", "default_on": True,
    },
    "date_creation": {
        "label": "Date de création",
        **_zone(x_cm=8.85, y_cm=1.6, k_cm=3.0, a_cm=0.4),
        "size": 9, "align": "left", "mode": "single", "default_on": True,
    },
    "echeance": {
        "label": "Échéance",
        **_zone(x_cm=12.6, y_cm=1.4, k_cm=3.2, a_cm=0.7),
        "size": 9, "align": "left", "mode": "single", "default_on": True,
    },
    "tire_code_etab": {
        "label": "Code étab. (RIB Tiré)",
        **_zone(x_cm=12.6, y_cm=2.3, k_cm=1.1, a_cm=0.7),
        "size": 8, "align": "center", "mode": "single", "default_on": True,
    },
    "tire_code_agence": {
        "label": "Code agence (RIB Tiré)",
        **_zone(x_cm=11.5, y_cm=2.3, k_cm=1.1, a_cm=0.7),
        "size": 8, "align": "center", "mode": "single", "default_on": True,
    },
    "tire_num_compte": {
        "label": "N° de compte (RIB Tiré)",
        # NB: la valeur du fichier de référence (x=9.7, k=5.1) chevauchait la
        # case "Clé" de 1 cm -> corrigé avec la valeur mesurée à la règle qui
        # s'emboîte exactement entre "Code agence" et "Clé".
        **_zone(x_cm=10.4, y_cm=2.3, k_cm=4.4, a_cm=0.7),
        "size": 8, "align": "center", "mode": "single", "default_on": True,
    },
    "tire_cle": {
        "label": "Clé RIB (Tiré)",
        **_zone(x_cm=5.6, y_cm=2.3, k_cm=0.9, a_cm=0.7),
        "size": 8, "align": "center", "mode": "single", "default_on": True,
    },
    "protestable_oui": {
        "label": "Croix « Oui » (Protestable)",
        **_zone(x_cm=8.4, y_cm=3.6, k_cm=0.2, a_cm=0.2),
        "size": 8, "align": "center", "mode": "cross", "default_on": True,
    },
    "protestable_non": {
        "label": "Croix « Non » (Protestable)",
        **_zone(x_cm=9.0, y_cm=3.6, k_cm=0.2, a_cm=0.2),
        "size": 8, "align": "center", "mode": "cross", "default_on": True,
    },
    "tireur_nom_adresse": {
        "label": "Nom du Tireur (client)",
        **_zone(x_cm=17.1, y_cm=3.6, k_cm=4.1, a_cm=1.1),
        "size": 9, "align": "left", "mode": "multiline", "default_on": True,
    },
    "nom_cedant": {
        "label": "Payer à l'ordre de",
        **_zone(x_cm=12.6, y_cm=4.3, k_cm=8.1, a_cm=0.4),
        "size": 9, "align": "left", "mode": "single", "default_on": True,
    },
    "montant_lettres": {
        "label": "Montant en lettres",
        **_zone(x_cm=16.8, y_cm=5.0, k_cm=16.5, a_cm=0.36),
        "size": 9, "align": "left", "mode": "single", "bold": True, "default_on": True,
    },
    "lieu_creation_2": {
        "label": "Lieu de création — 2e case",
        **_zone(x_cm=17.1, y_cm=5.8, k_cm=2.7, a_cm=0.65),
        "size": 9, "align": "left", "mode": "single", "default_on": True,
    },
    "date_creation_2": {
        "label": "Date de création — 2e case",
        **_zone(x_cm=14.4, y_cm=5.8, k_cm=2.65, a_cm=0.65),
        "size": 9, "align": "left", "mode": "single", "default_on": True,
    },
    "echeance_2": {
        "label": "Échéance — 2e case",
        **_zone(x_cm=11.8, y_cm=5.8, k_cm=2.75, a_cm=0.65),
        "size": 9, "align": "left", "mode": "single", "default_on": True,
    },
    "domiciliation": {
        "label": "Domiciliation",
        # NB: la valeur du fichier de référence (x=4.3, k=6.5) dépassait le
        # bord droit de la carte de 2.2 cm -> corrigé avec la valeur mesurée
        # à la règle qui reste bien dans les limites de la carte.
        **_zone(x_cm=5.8, y_cm=6.9, k_cm=5.5, a_cm=1.2),
        "size": 9, "align": "left", "mode": "multiline", "default_on": True,
    },
    "valeur_en": {
        "label": "Valeur en",
        **_zone(x_cm=8.5, y_cm=6.65, k_cm=1.9, a_cm=0.33),
        "size": 9, "align": "left", "mode": "single", "default_on": True,
    },
    "tire_code_etab_2": {
        "label": "Code étab. (RIB Tiré) — 2e case",
        **_zone(x_cm=17.1, y_cm=6.82, k_cm=0.7, a_cm=0.7),
        "size": 8, "align": "center", "mode": "single", "default_on": True,
    },
    "tire_code_agence_2": {
        "label": "Code agence (RIB Tiré) — 2e case",
        **_zone(x_cm=16.4, y_cm=6.82, k_cm=0.95, a_cm=0.7),
        "size": 8, "align": "center", "mode": "single", "default_on": True,
    },
    "tire_num_compte_2": {
        "label": "N° de compte (RIB Tiré) — 2e case",
        # Même correction que ci-dessus : la valeur du fichier de référence
        # (x=14.7, k=5.5) chevauchait la case "Clé" de 0.7 cm.
        **_zone(x_cm=15.4, y_cm=6.82, k_cm=4.65, a_cm=0.7),
        "size": 8, "align": "center", "mode": "single", "default_on": True,
    },
    "tire_cle_2": {
        "label": "Clé RIB (Tiré) — 2e case",
        **_zone(x_cm=10.7, y_cm=6.82, k_cm=0.7, a_cm=0.7),
        "size": 8, "align": "center", "mode": "single", "default_on": True,
    },
    "tire_nom": {
        "label": "Nom / Raison sociale du Tiré (vous)",
        **_zone(x_cm=9.5, y_cm=7.7, k_cm=4.5, a_cm=0.5),
        "size": 8, "align": "left", "mode": "single", "default_on": True,
    },
    "tire_adresse": {
        "label": "Adresse du Tiré (vous)",
        **_zone(x_cm=9.5, y_cm=8.2, k_cm=4.5, a_cm=1.5),
        "size": 8, "align": "left", "mode": "multiline", "default_on": True,
    },
    "num_cn": {
        "label": "N° CN (déjà imprimé sur le papier — désactivé par défaut)",
        "x": 140.0, "y": 10.0, "width_mm": 30.0, "height_mm": 5.0,
        "size": 8, "align": "left", "mode": "single", "default_on": False,
    },
}

# Champs "en double" -> valeur copiée automatiquement depuis le champ principal
DUPLICATE_FIELDS = {
    "montant_chiffres_2": "montant_chiffres",
    "lieu_creation_2": "lieu_creation",
    "date_creation_2": "date_creation",
    "echeance_2": "echeance",
    "tire_code_etab_2": "tire_code_etab",
    "tire_code_agence_2": "tire_code_agence",
    "tire_num_compte_2": "tire_num_compte",
    "tire_cle_2": "tire_cle",
}

FIELD_ORDER = [
    "montant_chiffres", "montant_chiffres_2",
    "lieu_creation", "lieu_creation_2", "date_creation", "date_creation_2",
    "echeance", "echeance_2",
    "tire_code_etab", "tire_code_etab_2", "tire_code_agence", "tire_code_agence_2",
    "tire_num_compte", "tire_num_compte_2", "tire_cle", "tire_cle_2",
    "protestable_oui", "protestable_non", "tireur_nom_adresse", "nom_cedant",
    "montant_lettres", "domiciliation", "valeur_en", "tire_nom", "tire_adresse", "num_cn",
]

STATUTS = {
    "en_attente": "En attente",
    "payee": "Payée",
    "non_payee": "Non payée",
}

STATUT_COLORS = {
    "en_attente": "#d68a00",
    "payee": "#1a8f3c",
    "non_payee": "#c0392b",
}

APP_TITLE = "Gestion des Traites Bancaires"
