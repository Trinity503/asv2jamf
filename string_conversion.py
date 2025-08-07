import string
import sys

def replace_special_chars(text):
    replacements = {
        'ä': 'ae',
        'ö': 'oe',
        'ü': 'ue',
        'ß': 'ss',
        'Ä': 'Ae',
        'Ö': 'Oe',
        'Ü': 'Ue',
        'ç': 'c',
        'ć': 'c',
        'č': 'c',
        'Ç': 'C',
        'Č': 'C',
        'đ': 'd',
        'ş': 's',
        'š': 's',
        'Ş': 'S',
        'Ś': 'S',
        'ğ': 'g',
        'Ğ': 'G',
        'é': 'e',
        'è': 'e',
        'ê': 'e',
        'à': 'a',
        'á': 'a',
        'ñ': 'n',
        'ó': 'o',
        "'": "",
        ' ': '',
        # beliebig ergänzen
    }
    warnings = set()

    # Zuerst ersetzen wir alle bekannten Zeichen
    for src, target in replacements.items():
        text = text.replace(src, target)
    
    # Dann prüfen wir auf unbekannte Sonderzeichen
    allowed = set(string.ascii_letters + string.digits + string.whitespace + string.punctuation)
    for char in text:
        if char not in allowed:
            warnings.add(char)
    
    if warnings:
        print(f"❌❌❌❌❌❌❌❌ABBRUCH: Nicht ersetzte Sonderzeichen gefunden: {', '.join(warnings)} ❌❌❌❌❌❌❌❌")
        print(f"Nehmen Sie dieses Zeichen in die Datei \"string_conversion.py\" auf und führen Sie den Befehl dann erneut aus.")
        sys.exit("Programm wurde abgebrochen.")
    
    return text


def kuerze_string(s, max_len=20):
    return s[:max_len]

#Die Unterrichtselemente sind so aufgebaut Fach/Klasse. Das ist aber für die klassenübergreifenden Gruppen unpraktisch.
#Verwendung: Fach, Klasse = teile_string(s)
#def teile_string(s, trenner="/"):
#    return s.split(trenner, 1)

def teile_string(s, trenner="/"):
    teile = s.split(trenner, 2)  # nur zwei Splits, Rest bleibt ignoriert
    if len(teile) < 2:
        return teile[0], ""
    return teile[0], teile[1]