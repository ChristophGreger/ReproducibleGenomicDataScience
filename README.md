# Reproducible Genomic Data Science

Dieses Repository enthält die Materialien und den Code für die Reproduktion von AlterNet im Rahmen des Seminars.

## AlterNet-Code

Der Ordner [`AlterNetCode/`](AlterNetCode/) enthält eine lokale Kopie des gesamten versionierten Inhalts von [bionetslab/alternet](https://github.com/bionetslab/alternet/tree/main). Die Dateien wurden direkt in dieses Projekt kopiert, ohne die Git-Historie zu übernehmen. Der Ordner ist kein Submodul und kein eigenständiges Git-Repository.

Damit bleiben die Verwaltung und die Versionskontrolle möglichst einfach: Der AlterNet-Code wird zusammen mit den übrigen Projektdateien in diesem Repository verwaltet. Anpassungen, die für die Reproduktion nötig sind, können direkt in `AlterNetCode/` vorgenommen und gemeinsam mit den anderen Änderungen committet werden. Änderungen am Original-Repository werden nicht automatisch übernommen.

Stand der übernommenen Kopie:

- Quelle: [bionetslab/alternet](https://github.com/bionetslab/alternet)
- Branch: `main`
- Commit: [`ce1d35b827f02917d0ceaf19eee037e5fb06d396`](https://github.com/bionetslab/alternet/commit/ce1d35b827f02917d0ceaf19eee037e5fb06d396)
- Kopiert am: 8. November 2026

Beim Import wurden in `AlterNetCode/.gitignore` Ausnahmen für die beiden mitgelieferten Dateien `data/appris_data.appris.txt` und `data/digger_data.csv` ergänzt, damit diese auch in diesem Repository regulär versioniert werden können. Alle übrigen Dateien wurden unverändert übernommen.

Die ursprüngliche Dokumentation mit Informationen zur Installation und Verwendung befindet sich in [`AlterNetCode/README.md`](AlterNetCode/README.md).
