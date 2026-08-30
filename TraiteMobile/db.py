# -*- coding: utf-8 -*-
"""Couche d'accès à la base de données SQLite locale de l'application."""

import sqlite3
import os
from constants import FIELDS

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    adresse TEXT,
    rib TEXT,
    telephone TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS traites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    num_cn TEXT,
    tireur_nom TEXT,
    tireur_adresse TEXT,
    client_id INTEGER REFERENCES clients(id) ON DELETE SET NULL,
    tire_nom TEXT,
    tire_adresse TEXT,
    tire_rib TEXT,
    tire_code_etab TEXT,
    tire_code_agence TEXT,
    tire_num_compte TEXT,
    tire_cle TEXT,
    nom_cedant TEXT,
    montant REAL NOT NULL DEFAULT 0,
    montant_lettres TEXT,
    lieu_creation TEXT,
    date_creation TEXT,
    echeance TEXT,
    domiciliation TEXT,
    valeur_en TEXT,
    protestable TEXT DEFAULT '',
    statut TEXT DEFAULT 'en_attente',
    date_paiement TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS field_positions (
    field_name TEXT PRIMARY KEY,
    x_mm REAL,
    y_mm REAL,
    font_size REAL,
    align TEXT DEFAULT 'left',
    enabled INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE INDEX IF NOT EXISTS idx_traites_num_cn ON traites(num_cn);
CREATE INDEX IF NOT EXISTS idx_traites_statut ON traites(statut);
CREATE INDEX IF NOT EXISTS idx_clients_nom ON clients(nom);
"""


class Database:
    def __init__(self, path):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        self._migrate()
        self._seed_field_positions()

    def _migrate(self):
        """Ajoute les colonnes manquantes si la base existait avant leur ajout
        (permet de mettre à jour l'application sans perdre les données)."""
        cols = {row["name"] for row in self.conn.execute("PRAGMA table_info(traites)")}
        if "protestable" not in cols:
            self.conn.execute("ALTER TABLE traites ADD COLUMN protestable TEXT DEFAULT ''")
            self.conn.commit()

        # Le RIB du Tiré était auparavant une seule case découpée en supposant
        # des longueurs fixes (2+3+13+2 chiffres). Comme ces longueurs peuvent
        # varier en pratique, chaque partie est maintenant saisie séparément
        # par l'utilisateur -> on ajoute les colonnes correspondantes.
        for col in ("tire_code_etab", "tire_code_agence", "tire_num_compte", "tire_cle"):
            if col not in cols:
                self.conn.execute(f"ALTER TABLE traites ADD COLUMN {col} TEXT DEFAULT ''")
        self.conn.commit()

        # Avant le passage au format "feuille A4 complète", le décalage
        # d'impression par défaut était (0,0). Cette ancienne valeur, si elle a
        # été enregistrée, resterait stockée et empêcherait le nouveau calcul
        # automatique (coin bas-droit) de s'appliquer -> tout le texte
        # apparaîtrait près du coin haut-gauche de la feuille au lieu du coin
        # bas-droit. On supprime ce réglage obsolète une seule fois.
        old_x = self.get_setting("offset_x_mm")
        old_y = self.get_setting("offset_y_mm")
        if old_x == "0" and old_y == "0":
            self.conn.execute("DELETE FROM settings WHERE key IN ('offset_x_mm', 'offset_y_mm')")
            self.conn.commit()

    # ---------- setup ----------
    def _seed_field_positions(self):
        """Insère la position par défaut de chaque champ défini dans
        constants.FIELDS qui n'existe pas encore dans la base -- couvre à la
        fois une toute nouvelle installation ET une mise à jour qui ajoute de
        nouveaux champs (ex: séparation d'un champ combiné en deux champs
        indépendants)."""
        existing = {row["field_name"] for row in
                    self.conn.execute("SELECT field_name FROM field_positions")}
        for key, f in FIELDS.items():
            if key in existing:
                continue
            self.conn.execute(
                "INSERT INTO field_positions (field_name, x_mm, y_mm, font_size, align, enabled) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (key, f["x"], f["y"], f["size"], f["align"], 1 if f["default_on"] else 0),
            )
        self.conn.commit()

    # ---------- settings ----------
    def get_setting(self, key, default=None):
        row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        self.conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        self.conn.commit()

    # ---------- field positions ----------
    def get_field_positions(self):
        rows = self.conn.execute("SELECT * FROM field_positions").fetchall()
        return {r["field_name"]: dict(r) for r in rows}

    def update_field_position(self, field_name, x_mm=None, y_mm=None, font_size=None,
                               align=None, enabled=None):
        current = self.conn.execute(
            "SELECT * FROM field_positions WHERE field_name=?", (field_name,)
        ).fetchone()
        if not current:
            return
        vals = dict(current)
        if x_mm is not None:
            vals["x_mm"] = x_mm
        if y_mm is not None:
            vals["y_mm"] = y_mm
        if font_size is not None:
            vals["font_size"] = font_size
        if align is not None:
            vals["align"] = align
        if enabled is not None:
            vals["enabled"] = 1 if enabled else 0
        self.conn.execute(
            "UPDATE field_positions SET x_mm=?, y_mm=?, font_size=?, align=?, enabled=? "
            "WHERE field_name=?",
            (vals["x_mm"], vals["y_mm"], vals["font_size"], vals["align"], vals["enabled"], field_name),
        )
        self.conn.commit()

    # ---------- clients ----------
    def add_client(self, nom, adresse="", rib="", telephone="", notes=""):
        cur = self.conn.execute(
            "INSERT INTO clients (nom, adresse, rib, telephone, notes) VALUES (?, ?, ?, ?, ?)",
            (nom.strip(), adresse.strip(), rib.strip(), telephone.strip(), notes.strip()),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_client(self, client_id, nom, adresse="", rib="", telephone="", notes=""):
        self.conn.execute(
            "UPDATE clients SET nom=?, adresse=?, rib=?, telephone=?, notes=? WHERE id=?",
            (nom.strip(), adresse.strip(), rib.strip(), telephone.strip(), notes.strip(), client_id),
        )
        self.conn.commit()

    def delete_client(self, client_id):
        self.conn.execute("DELETE FROM clients WHERE id=?", (client_id,))
        self.conn.commit()

    def find_client_by_name(self, nom):
        return self.conn.execute(
            "SELECT * FROM clients WHERE nom = ? COLLATE NOCASE", (nom.strip(),)
        ).fetchone()

    def list_clients(self, search=""):
        if search:
            like = f"%{search}%"
            rows = self.conn.execute(
                "SELECT * FROM clients WHERE nom LIKE ? OR rib LIKE ? ORDER BY nom COLLATE NOCASE",
                (like, like),
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM clients ORDER BY nom COLLATE NOCASE").fetchall()
        return rows

    def get_client(self, client_id):
        return self.conn.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()

    def get_or_create_client(self, nom, adresse="", rib="", telephone=""):
        """Utilisé lors de la création d'une traite : réutilise un client existant
        (même nom) ou en crée un nouveau automatiquement."""
        nom = (nom or "").strip()
        if not nom:
            return None
        existing = self.find_client_by_name(nom)
        if existing:
            # met à jour les coordonnées si elles ont été complétées/modifiées
            if adresse or rib or telephone:
                self.update_client(
                    existing["id"],
                    nom=nom,
                    adresse=adresse or existing["adresse"] or "",
                    rib=rib or existing["rib"] or "",
                    telephone=telephone or existing["telephone"] or "",
                )
            return existing["id"]
        return self.add_client(nom, adresse, rib, telephone)

    # ---------- traites ----------
    def add_traite(self, data: dict):
        fields = [
            "num_cn", "tireur_nom", "tireur_adresse", "client_id", "tire_nom", "tire_adresse",
            "tire_rib", "tire_code_etab", "tire_code_agence", "tire_num_compte", "tire_cle",
            "nom_cedant", "montant", "montant_lettres", "lieu_creation",
            "date_creation", "echeance", "domiciliation", "valeur_en", "protestable", "statut",
            "date_paiement", "notes",
        ]
        values = [data.get(f) for f in fields]
        placeholders = ",".join(["?"] * len(fields))
        cur = self.conn.execute(
            f"INSERT INTO traites ({','.join(fields)}) VALUES ({placeholders})", values
        )
        self.conn.commit()
        return cur.lastrowid

    def update_traite(self, traite_id, data: dict):
        fields = [
            "num_cn", "tireur_nom", "tireur_adresse", "client_id", "tire_nom", "tire_adresse",
            "tire_rib", "tire_code_etab", "tire_code_agence", "tire_num_compte", "tire_cle",
            "nom_cedant", "montant", "montant_lettres", "lieu_creation",
            "date_creation", "echeance", "domiciliation", "valeur_en", "protestable", "statut",
            "date_paiement", "notes",
        ]
        set_clause = ", ".join([f"{f}=?" for f in fields])
        values = [data.get(f) for f in fields] + [traite_id]
        self.conn.execute(
            f"UPDATE traites SET {set_clause}, updated_at=datetime('now') WHERE id=?", values
        )
        self.conn.commit()

    def delete_traite(self, traite_id):
        self.conn.execute("DELETE FROM traites WHERE id=?", (traite_id,))
        self.conn.commit()

    def get_traite(self, traite_id):
        return self.conn.execute("SELECT * FROM traites WHERE id=?", (traite_id,)).fetchone()

    def set_statut(self, traite_id, statut, date_paiement=None):
        self.conn.execute(
            "UPDATE traites SET statut=?, date_paiement=?, updated_at=datetime('now') WHERE id=?",
            (statut, date_paiement, traite_id),
        )
        self.conn.commit()

    def list_traites(self, search="", statut=None, client_id=None):
        query = "SELECT * FROM traites WHERE 1=1"
        params = []
        if search:
            query += " AND (num_cn LIKE ? OR tireur_nom LIKE ? OR nom_cedant LIKE ?)"
            like = f"%{search}%"
            params += [like, like, like]
        if statut:
            query += " AND statut=?"
            params.append(statut)
        if client_id:
            query += " AND client_id=?"
            params.append(client_id)
        query += " ORDER BY date_creation DESC, id DESC"
        return self.conn.execute(query, params).fetchall()

    def stats(self):
        rows = self.conn.execute(
            "SELECT statut, COUNT(*) n, COALESCE(SUM(montant),0) total FROM traites GROUP BY statut"
        ).fetchall()
        result = {s: {"n": 0, "total": 0.0} for s in ("en_attente", "payee", "non_payee")}
        for r in rows:
            result[r["statut"]] = {"n": r["n"], "total": r["total"]}
        total_general = sum(v["total"] for v in result.values())
        total_n = sum(v["n"] for v in result.values())
        return result, total_general, total_n

    def close(self):
        self.conn.close()
