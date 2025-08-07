===== asv2jamf =====
==== Beschreibung ====
In JAMF school lässt sich eine CSV-Datei mit dem Benutzerdaten importieren. Diese Datei kann die Gruppen enthalten, in denen der jeweilige/die jeweilige Schüler oder Schüler in ist.

Ein direkter Export der benötigten Unterrichte aus der ASV ist mir nicht gelungen. Dieses Tool wandelt die Daten aus "Export für eine Notenverwaltung" entsprechend um, wie wir sie an unserer Schule brauchen. Jede Schule wird ein wenig andere Anforderungen haben, aber dann ist dieser Code als Basis vielleicht hilfreich.

ACHTUNG: Die ASV wird im August 2025 eine neue Schnittstelle "Export für eine Notenverwaltung" veröffentlichen. Dann wird dieses Programm umprogrammiert werden müssen. Vielleicht noch schnell mit der alten "Export für eine Notenverwaltung" einen Export machen.

==== Verwendung ====
  * Export für eine Notenverwaltung durchführen.
  * Die dabei entstehende ZIP-Datei mithilfe des generierten Passworts in Schritt 1 entpacken.
  * Diese export.xml in den Ordner kopieren, in der die asv2jamf.py liegt.
  * Benötigte Bibliotheken installieren. Siehe requirements.txt
  * Im Terminal: python3 asv2jamf.py 
  * Fehlermeldungen überprüfen.
  * Die Datei schuelerdaten.csv in JAMF importieren.