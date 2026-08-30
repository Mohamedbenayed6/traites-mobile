# -*- coding: utf-8 -*-
"""
Génère un PDF au format d'une feuille A4 complète (la feuille réellement
chargée dans l'imprimante), avec le texte positionné dans le coin HAUT-GAUCHE
où se trouve la kembyela (17.4 x 11.5 cm) sur cette feuille -- confirmé par
les tests réels de l'utilisateur (une kembyela seule s'aligne sur le repère
haut-gauche de l'imprimante).
Ce PDF est destiné à être imprimé directement sur le papier pré-imprimé de
la traite bancaire (le papier fourni par la banque reste inchangé, seul le
texte des champs est ajouté par-dessus).
"""

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

from constants import (CARD_WIDTH_MM, CARD_HEIGHT_MM, FIELDS, DUPLICATE_FIELDS,
                       A4_WIDTH_MM, A4_HEIGHT_MM,
                       DEFAULT_CARD_OFFSET_X_MM, DEFAULT_CARD_OFFSET_Y_MM)

FONT_NAME = "Helvetica"
FONT_NAME_BOLD = "Helvetica-Bold"
MIN_FONT_SIZE = 6.0


def _wrap_text(text, font_name, font_size, max_width_pt):
    """Découpe le texte en lignes qui tiennent dans max_width_pt (points).
    Respecte les retours à la ligne explicites (\\n) comme des coupures
    forcées ; à l'intérieur de chaque ligne, découpe aux espaces si trop
    large pour la case."""
    if not text:
        return []
    all_lines = []
    for paragraph in str(text).split("\n"):
        words = paragraph.split()
        if not words:
            all_lines.append("")
            continue
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if stringWidth(candidate, font_name, font_size) <= max_width_pt or not current:
                current = candidate
            else:
                all_lines.append(current)
                current = word
        if current:
            all_lines.append(current)
    return all_lines


def _shrink_font_to_fit(text, font_name, start_size, max_width_pt, min_size=MIN_FONT_SIZE):
    size = start_size
    while size > min_size and stringWidth(text, font_name, size) > max_width_pt:
        size -= 0.5
    return max(size, min_size)


# ----------------------------------------------------------------------
# Construction des données imprimables à partir d'une ligne de traite (DB)
# ----------------------------------------------------------------------

def _split_rib(rib_raw):
    """Découpe un RIB tunisien en 4 parties en SUPPOSANT des longueurs fixes
    (2+3+13+2 chiffres). N'est utilisé que pour les anciennes traites créées
    avant l'ajout des 4 champs séparés (voir build_print_fields) -- ce n'est
    plus la méthode principale, car ces longueurs peuvent varier en réalité."""
    digits = "".join(ch for ch in (rib_raw or "") if ch.isdigit())
    code_etab = digits[0:2]
    code_agence = digits[2:5]
    num_compte = digits[5:18]
    cle = digits[18:20]
    return code_etab, code_agence, num_compte, cle


def build_print_fields(traite_row):
    """
    Transforme une ligne de traite (dict-like, colonnes de la table `traites`)
    en dictionnaire {clé_de_champ_imprimable: texte} prêt pour generate_traite_pdf.
    """
    t = dict(traite_row)

    # Chaque partie du RIB est saisie séparément par l'utilisateur (les
    # longueurs réelles peuvent varier, donc pas de découpage automatique).
    code_etab = (t.get("tire_code_etab") or "").strip()
    code_agence = (t.get("tire_code_agence") or "").strip()
    num_compte = (t.get("tire_num_compte") or "").strip()
    cle = (t.get("tire_cle") or "").strip()
    if not any([code_etab, code_agence, num_compte, cle]) and t.get("tire_rib"):
        # Compatibilité avec une traite créée avant l'ajout des champs séparés
        code_etab, code_agence, num_compte, cle = _split_rib(t.get("tire_rib"))

    tire_nom = (t.get("tire_nom") or "").strip()
    tire_adresse = (t.get("tire_adresse") or "").strip()
    tireur_nom = (t.get("tireur_nom") or "").strip()

    protestable = (t.get("protestable") or "").strip().lower()

    data = {
        # Format identique au fichier de référence : f"{montant:,.3f} DT"
        "montant_chiffres": "{:,.3f} DT".format(float(t.get("montant") or 0)),
        "lieu_creation": t.get("lieu_creation") or "",
        "date_creation": t.get("date_creation") or "",
        "echeance": t.get("echeance") or "",
        "tire_code_etab": code_etab,
        "tire_code_agence": code_agence,
        "tire_num_compte": num_compte,
        "tire_cle": cle,
        # Une croix ne s'imprime QUE si l'utilisateur a explicitement coché
        # Oui ou Non. "Non défini" -> aucune croix nulle part.
        "protestable_oui": "1" if protestable == "oui" else "",
        "protestable_non": "1" if protestable == "non" else "",
        "tireur_nom_adresse": tireur_nom,
        "nom_cedant": t.get("nom_cedant") or "",
        "montant_lettres": t.get("montant_lettres") or "",
        "domiciliation": t.get("domiciliation") or "",
        "valeur_en": t.get("valeur_en") or "",
        "tire_nom": tire_nom,
        "tire_adresse": tire_adresse,
        "num_cn": t.get("num_cn") or "",
    }

    # Les cases "en double" de la kembyela reprennent automatiquement la même
    # valeur que leur champ principal (voir DUPLICATE_FIELDS dans constants.py)
    for dup_key, source_key in DUPLICATE_FIELDS.items():
        data[dup_key] = data.get(source_key, "")

    return data


# ----------------------------------------------------------------------
# Génération du PDF
# ----------------------------------------------------------------------

def generate_traite_pdf(traite_row, field_positions: dict, output_path: str,
                         offset_x_mm: float = None, offset_y_mm: float = None,
                         show_crosshairs: bool = False, raw_fields: dict = None):
    """
    traite_row: ligne de traite brute (dict-like, colonnes de la table `traites`).
        Ignoré si raw_fields est fourni directement (utilisé par la grille de test).
    field_positions: dict {field_key: {x_mm, y_mm, font_size, align, enabled}}
    offset_x_mm/offset_y_mm: position de la kembyela sur la feuille A4 (+ réglage
        fin éventuel selon l'imprimante). Par défaut : collée au coin haut-gauche
        de la feuille A4, comme confirmé par les tests réels.
    show_crosshairs: dessine des repères sur les 4 coins de la kembyela (pas de
        la feuille A4) pour vérifier l'alignement en tenant la page contre une
        vraie traite.
    """
    if offset_x_mm is None:
        offset_x_mm = DEFAULT_CARD_OFFSET_X_MM
    if offset_y_mm is None:
        offset_y_mm = DEFAULT_CARD_OFFSET_Y_MM

    width_pt = A4_WIDTH_MM * mm
    height_pt = A4_HEIGHT_MM * mm

    print_data = raw_fields if raw_fields is not None else build_print_fields(traite_row)

    c = canvas.Canvas(output_path, pagesize=(width_pt, height_pt))

    for key, meta in FIELDS.items():
        pos = field_positions.get(key)
        if not pos or not pos.get("enabled"):
            continue
        value = print_data.get(key, "")
        if value is None or str(value).strip() == "":
            continue

        x_mm = pos["x_mm"] + offset_x_mm
        y_mm = pos["y_mm"] + offset_y_mm
        font_size = pos.get("font_size") or meta["size"]
        align = pos.get("align") or meta.get("align", "left")
        mode = meta.get("mode", "single")
        bold = meta.get("bold", False)
        width_mm = meta.get("width_mm", 100)
        height_mm = meta.get("height_mm", 5)
        font_name = FONT_NAME_BOLD if bold else FONT_NAME

        x_pt = x_mm * mm
        y_top_pt = height_pt - (y_mm * mm)  # conversion : y mesuré depuis le HAUT
        w_pt = width_mm * mm
        h_pt = height_mm * mm

        if mode == "cross":
            _draw_cross(c, x_pt, y_top_pt, w_pt, h_pt)
            continue

        if mode == "multiline":
            lines = _wrap_text(value, font_name, font_size, w_pt)
            line_height = font_size * 1.2
            max_lines = max(1, int(h_pt / line_height))
            lines = lines[:max_lines]
            block_height = len(lines) * line_height
            y_cursor = y_top_pt - (h_pt - block_height) / 2 - font_size * 0.85
            c.setFont(font_name, font_size)
            for line in lines:
                _draw_aligned(c, line, x_pt, y_cursor, align, font_size, w_pt)
                y_cursor -= line_height
        else:  # "single" -> rétrécit automatiquement pour toujours tenir
            fitted_size = _shrink_font_to_fit(str(value), font_name, font_size, w_pt)
            c.setFont(font_name, fitted_size)
            # Centrage vertical dans la hauteur de la case (comme le modèle validé)
            text_y = y_top_pt - h_pt / 2 + fitted_size / 3
            _draw_aligned(c, str(value), x_pt, text_y, align, fitted_size, w_pt)

    if show_crosshairs:
        _draw_registration_marks(c, height_pt, offset_x_mm, offset_y_mm)

    c.showPage()
    c.save()
    return output_path


def _draw_aligned(c, text, x_pt, y_pt, align, font_size, w_pt):
    if align == "center":
        c.drawCentredString(x_pt + w_pt / 2, y_pt, text)
    elif align == "right":
        c.drawRightString(x_pt + w_pt, y_pt, text)
    else:
        c.drawString(x_pt, y_pt, text)


def _draw_cross(c, x_pt, y_top_pt, w_pt, h_pt):
    """Dessine une croix (X) graphique dans la case, comme sur le modèle validé."""
    x1, y1 = x_pt, y_top_pt
    x2, y2 = x_pt + w_pt, y_top_pt - h_pt
    c.setLineWidth(1)
    c.line(x1, y1, x2, y2)
    c.line(x2, y1, x1, y2)


def _draw_registration_marks(c, page_height_pt, card_offset_x_mm, card_offset_y_mm):
    """Dessine des repères + le contour de la kembyela à sa position sur la
    feuille A4, pour vérifier l'alignement en tenant la page imprimée contre
    une vraie traite."""
    x_left_pt = card_offset_x_mm * mm
    x_right_pt = (card_offset_x_mm + CARD_WIDTH_MM) * mm
    y_top_pt = page_height_pt - (card_offset_y_mm * mm)
    y_bottom_pt = page_height_pt - ((card_offset_y_mm + CARD_HEIGHT_MM) * mm)

    c.setLineWidth(0.5)
    size = 4 * mm
    corners = [(x_left_pt, y_bottom_pt), (x_right_pt, y_bottom_pt),
               (x_left_pt, y_top_pt), (x_right_pt, y_top_pt)]
    for cx, cy in corners:
        c.line(cx - size, cy, cx + size, cy)
        c.line(cx, cy - size, cx, cy + size)
    c.rect(x_left_pt, y_bottom_pt, x_right_pt - x_left_pt, y_top_pt - y_bottom_pt)


def generate_test_grid_pdf(field_positions: dict, output_path: str,
                            offset_x_mm: float = None, offset_y_mm: float = None):
    """Génère une page de test (taille A4 complète) affichant le NOM de chaque
    champ à sa position calibrée + le contour de la kembyela, pour vérifier
    l'alignement sur papier blanc avant d'imprimer une vraie traite."""
    sample_data = {}
    for key, meta in FIELDS.items():
        sample_data[key] = "X" if meta.get("mode") == "cross" else meta["label"]
    return generate_traite_pdf(
        None, field_positions, output_path, offset_x_mm=offset_x_mm,
        offset_y_mm=offset_y_mm, show_crosshairs=True, raw_fields=sample_data,
    )
