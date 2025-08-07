#ToDo:
#unterrichtselemente und fächer als globale listen erstellen
#code cleanup

import pandas as pd
from lxml import etree
from string_conversion import replace_special_chars, kuerze_string, teile_string
import xml.etree.ElementTree as ET

import sys
from typing import List, Dict

#Variablen
debug = False
# Dateipfade - bitte anpassen!
xml_file = "export.xml"  # Ändern Sie dies zu Ihrem XML-Pfad
xsd_file = "notenverwaltung_1.01.xsd"  # Ändern Sie dies zu Ihrem XSD-Pfad
output_csv = "schuelerdaten.csv"

#Aufbau der E-Mail nach dem @-Zeichen
domain = "meine-schule.de"

#faecherliste = [...]  # Fächerliste

#Klassen, die nicht in JAMF angelegt werden sollen. Sogenannte "organisatorische Klassen"
ausgeschlossene_klassen = {'Neu', 'AufnPr','AUS', '#Wdh/Vers', '11X'}
#Kurzbezeichnung der Fächer, die innerhalb eine Klasse nie geteilt sind und für die keine eigene Gruppe angelegt werden muss. z. B. B (Biologie)
ungeteile_faecher = {'M', 'BwR', 'Ph' , 'C', 'WR', 'F', 'PuG', 'B', 'Mu', 'D', 'G', 'Geo', 'Ku', 'Sm', 'Smw', 'Sw', 'E'}
#Jetzt gibt es Klassen, in denen nur eine Klassengruppe besteht. Die folgenden Fächer sollen dann auch wie "ungeteilte Fächer" behandelt werden:
#ungeteile_faecher_bei_einer_klassengruppe = {'M', 'Ph', 'Ch', 'BwR'}

#Alle Fächer, in denen klassenübergreifende Koppeln existieren und für die Gruppen in JAMF angelegt werden sollen (Sport habe ich deshalb hier weggelassen).
gekoppelte_faecher = {'K', 'Ev', 'Eth'}

def validate_xml_with_xsd(xml_file, xsd_file):
    """Validiert XML gegen XSD mit Namespace-Unterstützung"""
    try:
        print(f"🔍 Lade XSD-Datei: {xsd_file}")
        with open(xsd_file, 'rb') as f:
            xsd_schema = etree.XMLSchema(etree.parse(f))

        print(f"🔍 Lade XML-Datei: {xml_file}")
        parser = etree.XMLParser(strip_cdata=False, remove_blank_text=True, recover=True)
        xml_doc = etree.parse(xml_file, parser)

        # Namespace-Handling
        ns = xml_doc.getroot().nsmap
        if ns:
            if debug == True: print("🔹 Gefundene Namespaces:", ns)
            # Registriere Namespaces für XPath
            for prefix, uri in ns.items():
                if prefix:
                    etree.register_namespace(prefix, uri)
                else:
                    etree.register_namespace('default', uri)

        print("🔍 Starte Validierung...")
        if xsd_schema.validate(xml_doc):
            print("✅ XML ist gültig gegen die XSD.")
        else:
            print("⚠️ XML enthält Validierungsfehler (maxLength wird ignoriert):")
            for error in xsd_schema.error_log:
                if "maxLength" not in str(error.message):
                    print(f"  ❌ Fehler: {error.message}")

        return xml_doc

    except Exception as e:
        print(f"❌ Fehler bei der Validierung: {str(e)}")
        return None


# Namespaces definieren
NAMESPACES = {
    'asv': 'http://www.asv.bayern.de/import',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

def parse_faecher_from_xml(xml_file: str) -> list:
    faecher_list = []
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        for schule in root.findall('.//asv:schule', NAMESPACES):
            faecher = schule.find('asv:faecher', NAMESPACES)
            if faecher is None:
                continue  # Überspringen, falls kein <faecher>-Element vorhanden

            for fach in faecher.findall('asv:fach', NAMESPACES):
                try:
                    # XML-Daten extrahieren
                    xml_id = fach.findtext('asv:xml_id', '', NAMESPACES)
                    if not xml_id:  # Überspringen, falls keine ID vorhanden
                        continue

                    # Dictionary erstellen
                    fach_dict = {
                        'xml_id': int(xml_id),
                        'kurzform': fach.findtext('asv:kurzform', '', NAMESPACES),
                        'anzeigeform': fach.findtext('asv:anzeigeform', '', NAMESPACES),
                        'langform': fach.findtext('asv:langform', '', NAMESPACES),
                        'ist_selbst_erstellt': fach.findtext('asv:ist_selbst_erstellt', 'false', NAMESPACES).lower() == 'true',
                        'asd_fach': fach.findtext('asv:asd_fach', '', NAMESPACES)
                    }

                    # Nur gültige Dictionaries hinzufügen
                    if fach_dict['xml_id'] is not None:
                        faecher_list.append(fach_dict)

                except Exception as e:
                    print(f"Fehler beim Parsen eines Fachs: {e}")
                    continue  # Überspringen, falls ein Fehler auftritt

    except Exception as e:
        print(f"Fehler beim Parsen der XML-Datei: {e}")

    return faecher_list

def get_kurzform_by_id(faecherliste: list, id: int) -> str:
    #print(faecherliste)
    faecherliste = [fach for fach in faecherliste if isinstance(fach, dict)]
    for fach in faecherliste:
        #print(fach)
        #print(fach['xml_id'])
        if fach['xml_id'] == id:
            return fach['kurzform'] 
        #else:
        #    return "Fach nicht gefunden."

def parse_unterrichte_from_xml(xml_file: str) -> list:
    unterrichtselemente_list = []
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        for schule in root.findall('.//asv:schule', NAMESPACES):
            unterrichtselemente = schule.find('asv:unterrichtselemente', NAMESPACES)
            if unterrichtselemente is None:
                continue  # Überspringen, falls kein <unterrichtselemente>-Element vorhanden

            for unterrichtselement in unterrichtselemente.findall('asv:unterrichtselement', NAMESPACES):
                try:
                    # XML-Daten extrahieren
                    xml_id = unterrichtselement.findtext('asv:xml_id', '', NAMESPACES)
                    if not xml_id:  # Überspringen, falls keine ID vorhanden
                        continue

                    # Dictionary erstellen
                    unterrichtselement_dict = {
                        'xml_id': int(xml_id),
                        'fach_id': unterrichtselement.findtext('asv:fach_id', '', NAMESPACES),
                        'bezeichnung': unterrichtselement.findtext('asv:bezeichnung', '', NAMESPACES)
                    }

                    # Nur gültige Dictionaries hinzufügen
                    if unterrichtselement_dict['xml_id'] is not None:
                        unterrichtselemente_list.append(unterrichtselement_dict)

                except Exception as e:
                    print(f"Fehler beim Parsen eines Unterrichtselements: {e}")
                    continue  # Überspringen, falls ein Fehler auftritt

    except Exception as e:
        print(f"Fehler beim Parsen der XML-Datei: {e}")

    return unterrichtselemente_list

def get_bezeichnung_by_id(unterrichtselementeliste : list, id: int) -> str:
    #print(unterrichtselementeliste)
    unterrichtselementeliste = [unterrichtselement for unterrichtselement in unterrichtselementeliste if isinstance(unterrichtselement, dict)]
    for unterrichtselement in unterrichtselementeliste:
        #print(unterrichtselement)
        #print(unterrichtselement['xml_id'])
        if unterrichtselement['xml_id'] == id:
            return unterrichtselement['bezeichnung'] 
        #else:
        #    return "Unterrichtselement nicht gefunden."


def extract_data(faecherliste:list,unterrichtselementeliste:list,xml_doc):
    """Extrahiert Daten mit Namespace-Unterstützung"""
    
    data = []
    ns = {'ns': 'http://www.asv.bayern.de/import'}  # Standard-Namespace

    try:
        print("🔍 Beginne Datenextraktion...")

        # Versuche verschiedene XPath-Varianten für Schulen
        schulen_paths = [
            '//ns:schule',  # Mit Namespace
            '//schule',     # Ohne Namespace
            '/ns:asv_export/ns:schulen/ns:schule',
            '/asv_export/schulen/schule'
        ]

        schulen = None
        for path in schulen_paths:
            schulen = xml_doc.xpath(path, namespaces=ns)
            if schulen:
                if debug == True: print(f"🔹 Schulen gefunden mit XPath: {path}")
                break

        if not schulen:
            print("❌ Keine Schulen gefunden! Versuche alternative Suche...")
            # Alternative Suche nach allen Elementen
            all_elements = xml_doc.xpath('//*')
            print(f"🔹 Gefundene Elemente: {len(all_elements)}")
            for elem in all_elements[:5]:  # Zeige erste 5 Elemente
                print(f"  - {elem.tag}: {elem.text[:50]}...")
            return data

        if debug == True: print(f"🔹 Gefunden: {len(schulen)} Schule(n)")

        for schule in schulen:
            # Daten mit Namespace extrahieren
            schulnummer = schule.xpath('ns:schulnummer/text()', namespaces=ns)
            schuljahr = schule.xpath('ns:schuljahr/text()', namespaces=ns)
            schulart = schule.xpath('ns:schulart/text()', namespaces=ns)

            if not schulnummer or not schuljahr:
                print(f"⚠️ Ungültige Schuldaten gefunden (Nummer: {schulnummer}, Jahr: {schuljahr})")
                continue

            schulnummer = schulnummer[0]
            schuljahr = schuljahr[0]
            schulart = schulart[0] if schulart else 'Unbekannt'

            print(f"🔹 Verarbeite Schule: {schulnummer} ({schuljahr})")

            # Klassen suchen (mit Namespace)
            klassen_paths = [
                'ns:klassen/ns:klasse',
                'klassen/klasse',
                'ns:klasse',
                'klasse'
            ]

            klassen = None
            for path in klassen_paths:
                klassen = schule.xpath(path, namespaces=ns)
                if klassen:
                    #print(f"🔹 Klassen gefunden mit XPath: {path}")
                    break

            if not klassen:
                print(f"⚠️ Keine Klassen in Schule {schulnummer} gefunden")
                continue

            print(f"🔹 Gefunden: {len(klassen)} Klasse(n)")

            for klasse in klassen:
                klassenname = klasse.xpath('ns:klassenname/text()', namespaces=ns)   
                if not klassenname:
                    klassenname = klasse.xpath('klassenname/text()')
                if not klassenname:
                    print("⚠️ Klasse ohne Namen gefunden")
                    continue
                klassenname = klassenname[0].replace(" ", "")

                if klassenname in ausgeschlossene_klassen:
                    continue 
                
                
            # Klassengruppen suchen (mit Namespace)
                klassengruppen_paths = [
                    'ns:klassengruppen/ns:klassengruppe',
                    'klassengruppen/klassengruppe',
                    'ns:klasse',
                    'klasse'
                ]

                klassengruppen = None
                for path in klassengruppen_paths:
                    klassengruppen = klasse.xpath(path, namespaces=ns)
                    if klassengruppen:
                        #print(f"🔹 Klassengruppen gefunden mit XPath: {path}")
                        break

                if not klassengruppen:
                    print(f"⚠️ Keine Klassengruppen in Schule {schulnummer} gefunden")
                    continue

                print(f"🔹 Gefunden: {len(klassengruppen)} Klassengruppe(n)")

                for klassengruppe in klassengruppen:
                    kennung = klassengruppe.xpath('ns:kennung/text()', namespaces=ns)
                    if not kennung:
                        kennung = klasse.xpath('kennung/text()')
                    if not kennung:
                        print("⚠️ Klassengruppe ohne Kennung gefunden")
                        continue
                    kennung = kennung[0]

                     

                    # Schüler suchen
                    schueler_paths = [
                        'ns:schuelerliste/ns:schuelerin',
                        'schuelerliste/schuelerin',
                        'ns:schulerliste',  
                        'schuelerin'
                    ]

                    schueler_list = None
                    for path in schueler_paths:
                        schueler_list = klassengruppe.xpath(path, namespaces=ns)
                        if schueler_list:
                            #print(f"🔹 SchülerIn gefunden mit XPath: {path}")
                            break

                    if not schueler_list:
                        print(f"⚠️ Keine SchülerIn in Klasse {klassenname} gefunden")
                        continue

                    print(f"🔹 Gefunden: {len(schueler_list)} SchülerInnen in Klasse {klassenname}_{kennung}")

                    for schueler in schueler_list:
                        try:
                            # Grunddaten extrahieren
                            familienname = schueler.xpath('ns:familienname/text()', namespaces=ns)
                            if not familienname:
                                familienname = schueler.xpath('familienname/text()')
                            if not familienname:
                                familienname = schueler.xpath('ns:name/text()', namespaces=ns)
                            if not familienname:
                                familienname = schueler.xpath('name/text()')

                            rufname = schueler.xpath('ns:rufname/text()', namespaces=ns)
                            if not rufname:
                                rufname = schueler.xpath('rufname/text()')

                            if not familienname or not rufname:
                                print(f"⚠️ Ungültige Schülerdaten in Klasse {klassenname}")
                                continue

                            familienname = familienname[0]
                            rufname = rufname[0]
                            username = kuerze_string(replace_special_chars(familienname) + "." + replace_special_chars(rufname))
                            email = username +"@" +domain
                            # Klassengruppen
                            #gruppennamen = schueler.xpath('ns:klassengruppen/ns:gruppe/text()', namespaces=ns)
                            #if not gruppennamen:
                            #    gruppennamen = schueler.xpath('klassengruppen/gruppe/text()')
                            #klassengruppen = ', '.join(gruppennamen) if gruppennamen else ''
                            klassengruppe = klassenname + "_" + kennung
                            
                            
                            
                            #groups ist die Liste aller Gruppen, in denen die SuS in JAMF enthalten sein sollen. Die oberste Gruppe ist natürlich die Klasse.
                            groups = klassenname
                            if len(klassengruppen) > 1:
                                groups = groups + "," + klassenname + "_" + kennung


                            # Besuchte Fächer
                            besuchte_faecher = []
                            unterrichtselemente = []
                            for fach in schueler.xpath('ns:besuchte_faecher/ns:besuchtes_fach', namespaces=ns):
                                fach_id = fach.xpath('ns:fach_id/text()', namespaces=ns)[0] if fach.xpath('ns:fach_id/text()', namespaces=ns) else 'Unbekannt'
                                
                                
                                #Pflichtfach? Nur Pflichtfächer werden verarbeitet
                                fach_art = fach.xpath('ns:unterrichtsart/text()', namespaces=ns)[0] if fach.xpath('ns:unterrichtsart/text()', namespaces=ns) else 'Unbekannt'
                                if fach_art != "P":
                                    continue
                                
                                #print(f"Fach-ID: {fach_id}")
                                kurzform = get_kurzform_by_id(faecherliste, int(fach_id))
                                #print(f"Kurzform: {kurzform}")
                                
                                #Nur geteilte Fächer werden verarbeitet.
                                if kurzform in ungeteile_faecher:
                                    continue
                                
                                unterrichtselement_id = fach.xpath('ns:unterrichtselemente/ns:unterrichtselement_id/text()', namespaces=ns)[0] if fach.xpath('ns:unterrichtselemente/ns:unterrichtselement_id/text()', namespaces=ns) else 0
                                #print(unterrichtselement_id)
                                
                                bezeichnung = get_bezeichnung_by_id(unterrichtselementeliste, int(unterrichtselement_id))
                                #print(bezeichnung)
                                if bezeichnung != None:
                                    bezeichnung = bezeichnung.replace(" ", "")
                                    UElementFach, UElementKlasse = teile_string(bezeichnung)
                                
                                
                                    #Wenn es nur eine Klassengruppe gibt, sollen manche Fächer übersprungen werden.
                                    #if len(klassengruppen) == 1:
                                    #    if kurzform in ungeteile_faecher_bei_einer_klassengruppe:
                                    #        continue
                                    
                                    #Bei den klassenübergreifenden Koppeln darf der Klassenname nicht in JAMF angehängt werden, sonst wird pro Klasse eine Gruppe erstellt und nicht eine Gruppe für alle Klassen.
                                    if kurzform in gekoppelte_faecher:
                                        if UElementKlasse != klassenname: #gekoppelte Fächer, hier wird die Jahsgangsstufe vorne angehängt. Wenn man jahrgangsstufenübergreifende Koppeln hat, löscht man das [:2] besser weg.
                                            unterrichtselemente.append(klassenname[:2] + "_" + UElementKlasse)
                                            groups = groups + "," + klassenname[:2] + "_" + UElementKlasse
                                        else:#Wenn z. B. Religion dann doch mal nicht gekoppelt ist.
                                            unterrichtselemente.append(UElementKlasse + "_" + UElementFach)  
                                            groups = groups + "," + UElementKlasse + "_" + UElementFach
                                    else:
                                        unterrichtselemente.append(UElementKlasse + "_" + UElementFach)
                                        groups = groups + "," + UElementKlasse + "_" + UElementFach
                                
                                #faecher.append(fachname)
                                # Zusätzliche Fachinformationen
                                #fach_details = {
                                #    'fach_id': fachname,
                                #    'unterrichtsart': fach.xpath('ns:unterrichtselemente/ns:unterrichtsart/text()', namespaces=ns)[0]
                                #                if fach.xpath('ns:unterrichtselemente/ns:unterrichtsart/text()', namespaces=ns) else '',
                                #    'belegungsart': fach.xpath('ns:unterrichtselemente/ns:belegungsart/text()', namespaces=ns)[0]
                                #                if fach.xpath('ns:unterrichtselemente/ns:belegungsart/text()', namespaces=ns) else ''
                                #}

                                #Kopplungsinformationen
                                #koppel = fach.xpath('ns:unterrichtselemente/ns:koppel/ns:kurzform/text()', namespaces=ns)
                                #if koppel:
                                #    fach_details['koppel'] = koppel[0]

                                besuchte_faecher.append(kurzform)
                            
                            
                            
                            
                            
                            
                            
                            
                            
                            
                            
                            
                            
                            
                            # Daten hinzufügen
                            data.append({
                                #'Schulnummer': schulnummer,
                                #'Schuljahr': schuljahr,
                                #'Schulart': schulart,
                                'Username': username,
                                'Email': email,
                                'FirstName': rufname,
                                'LastName': familienname,
                                'Groups': groups,
                                'TeacherGroups': 'Lehrkraefte',
                                'Password': '',                                
                            })
                            if debug == True:
                                data.append({
                                        'Klasse': klassenname,
                                        'Klassengruppe': klassengruppe, 
                                        'Faecher': besuchte_faecher,
                                        'Unterrichtselemente': unterrichtselemente
                                        
                                    })


                        except Exception as e:
                            print(f"⚠️ Fehler bei Schülerverarbeitung: {str(e)}")
                            continue

        print(f"🔹 Erfolgreich {len(data)} Datensätze extrahiert")
        return data

    except Exception as e:
        print(f"❌ Fehler bei Datenextraktion: {str(e)}")
        return []



def save_to_csv(data, output_file):
    """Speichert die Daten als CSV-Datei"""
    if not data:
        print("⚠️ Keine Daten zum Speichern vorhanden!")
        return False

    try:
        df = pd.DataFrame(data)
        df.to_csv(output_file, sep=';', index=False, encoding='utf-8-sig')
        print(f"📁 Daten erfolgreich nach {output_file} exportiert!")
        print(f"🔹 {len(df)} Datensätze geschrieben")
        return True
    except Exception as e:
        print(f"❌ Fehler beim CSV-Export: {str(e)}")
        return False

def main():
    print("🚀 Starte XML-zu-CSV-Konvertierung...")

    # 1. XML validieren
    xml_doc = validate_xml_with_xsd(xml_file, xsd_file)
    if not xml_doc:
        print("❌ Abbruch: Kein gültiges XML-Dokument erhalten")
        return

    #Fächer einlesen
    
    faecherliste = parse_faecher_from_xml(xml_file)
    print(f"Anzahl der Fächer: {len(faecherliste)}")

    #Unterrichtselemente einlesen
    unterrichtselementeliste = parse_unterrichte_from_xml(xml_file)
    print(f"Anzahl der Unterrichtselemente: {len(unterrichtselementeliste)}")


    # 2. Daten extrahieren
    data = extract_data(faecherliste,unterrichtselementeliste,xml_doc)
    if not data:
        print("❌ Abbruch: Keine Daten extrahiert")
        return
    
    

    # 3. Daten speichern
    if not save_to_csv(data, output_csv):
        print("❌ Fehler beim Speichern der CSV-Datei")

if __name__ == "__main__":
    main()
