"""
Conversion de nombres en toutes lettres (français), et formatage du montant
en dinars et millimes tel qu'il doit apparaître sur une lettre de change
tunisienne (ex: "Mille deux cents dinars et cinq cent soixante-sept millimes").
"""

UNITS = [
    "zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
    "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize",
    "dix-sept", "dix-huit", "dix-neuf",
]

_DIZAINES = {2: "vingt", 3: "trente", 4: "quarante", 5: "cinquante", 6: "soixante"}


def _deux_chiffres(n: int, is_terminal: bool) -> str:
    """n in 0..99"""
    if n < 20:
        return UNITS[n]
    dizaine, unite = divmod(n, 10)
    if dizaine in (7, 9):
        base = "soixante" if dizaine == 7 else "quatre-vingt"
        if dizaine == 7 and unite == 1:
            return f"{base}-et-onze"
        return f"{base}-{UNITS[10 + unite]}"
    if dizaine == 8:
        if unite == 0:
            return "quatre-vingts" if is_terminal else "quatre-vingt"
        return f"quatre-vingt-{UNITS[unite]}"
    base = _DIZAINES[dizaine]
    if unite == 0:
        return base
    if unite == 1:
        return f"{base}-et-un"
    return f"{base}-{UNITS[unite]}"


def _trois_chiffres(n: int, is_terminal: bool) -> str:
    """n in 0..999"""
    centaine, reste = divmod(n, 100)
    parts = []
    if centaine > 0:
        if centaine == 1:
            parts.append("cent")
        else:
            suffix = "s" if (reste == 0 and is_terminal) else ""
            parts.append(f"{UNITS[centaine]} cent{suffix}")
    if reste > 0:
        parts.append(_deux_chiffres(reste, is_terminal))
    return " ".join(parts)


_SCALES = [
    (10**9, "milliard", "milliards"),
    (10**6, "million", "millions"),
    (10**3, "mille", "mille"),  # "mille" is invariable
]


def nombre_en_lettres(n: int) -> str:
    """Convertit un entier positif (0 à 999 999 999 999) en toutes lettres françaises."""
    if n < 0:
        return "moins " + nombre_en_lettres(-n)
    if n == 0:
        return "zéro"

    remaining = n
    parsed = []
    for scale_val, sing, plur in _SCALES:
        group_val = remaining // scale_val
        remaining %= scale_val
        parsed.append((group_val, sing, plur))
    parsed.append((remaining, None, None))  # units group (0-999)

    nonzero_idx = [i for i, (v, _, _) in enumerate(parsed) if v > 0]
    last_nonzero_idx = max(nonzero_idx)

    words = []
    for i, (val, sing, plur) in enumerate(parsed):
        if val == 0:
            continue
        is_terminal_group = (i == last_nonzero_idx)
        if sing is None:
            words.append(_trois_chiffres(val, is_terminal_group))
        elif sing == "mille":
            if val == 1:
                words.append("mille")
            else:
                words.append(f"{_trois_chiffres(val, False)} mille")
        else:
            word_group = _trois_chiffres(val, False)
            scale_word = sing if val == 1 else plur
            words.append(f"{word_group} {scale_word}")
    return " ".join(words)


def montant_en_lettres(montant: float) -> str:
    """
    Formate un montant en dinars/millimes tunisiens en toutes lettres,
    ex: 1250.500 -> "Mille deux cent cinquante dinars et cinq cents millimes"
    Le montant peut comporter jusqu'à 3 décimales (millimes).
    """
    montant = round(float(montant), 3)
    dinars = int(montant)
    millimes = int(round((montant - dinars) * 1000))
    if millimes >= 1000:
        dinars += 1
        millimes -= 1000

    dinar_mot = "un" if dinars == 1 else nombre_en_lettres(dinars)
    dinar_unit = "dinar" if dinars == 1 else "dinars"

    millime_mot = "un" if millimes == 1 else nombre_en_lettres(millimes)
    millime_unit = "millime" if millimes == 1 else "millimes"

    phrase = f"{dinar_mot} {dinar_unit} et {millime_mot} {millime_unit}"
    return phrase[0].upper() + phrase[1:]


if __name__ == "__main__":
    tests = [0, 1, 2, 15, 20, 21, 30, 71, 79, 80, 81, 90, 91, 99, 100, 101, 199,
              200, 201, 280, 300, 999, 1000, 1001, 1200, 1999, 2000, 2020,
              10000, 21000, 80000, 100000, 200000, 999999, 1000000, 1000001,
              2000000, 1500000]
    for t in tests:
        print(t, "->", nombre_en_lettres(t))
    print("---")
    for m in [0.0, 1.0, 1.001, 1250.5, 999.999, 1000.0, 15000.750, 280.0, 80.0, 100000.000]:
        print(m, "->", montant_en_lettres(m))
