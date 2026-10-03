"""
Fusionne les résultats des agents de recherche de sites web
(lots_recherche_france/resultat_*.json) dans l'état persistant
(recherche_sites_etat_france.json).

Règle clé pour la reprise automatique : une entreprise n'est marquée
"trouve" ou "non_trouve" QUE si l'agent indique recherche_effectuee=true.
Si recherche_effectuee=false (quota épuisé avant de l'avoir traitée),
son statut reste "a_chercher" — le prochain passage de
preparer_lots_recherche_france.py la remettra automatiquement dans un lot,
sans qu'on ait besoin de relire les comptes-rendus des agents à la main
pour deviner qui a vraiment été cherché (c'est cette relecture manuelle,
source d'erreur, que ce mécanisme remplace).

Usage : python3 fusionner_resultats_recherche.py
"""

import glob
import json
import os

FICHIER_ETAT = "recherche_sites_etat_france.json"
DOSSIER_LOTS = "lots_recherche_france"


def main():
    with open(FICHIER_ETAT, encoding="utf-8") as f:
        etat = json.load(f)

    fichiers_resultats = sorted(glob.glob(os.path.join(DOSSIER_LOTS, "resultat_*.json")))
    if not fichiers_resultats:
        print(f"Aucun fichier resultat_*.json trouvé dans {DOSSIER_LOTS}/.")
        return

    nb_trouves = 0
    nb_non_trouves = 0
    nb_non_recherches = 0
    nb_inconnus = 0

    for chemin in fichiers_resultats:
        with open(chemin, encoding="utf-8") as f:
            resultats = json.load(f)

        for item in resultats:
            siren = item.get("siren", "").strip()
            if siren not in etat:
                nb_inconnus += 1
                continue

            if not item.get("recherche_effectuee", False):
                nb_non_recherches += 1
                continue  # reste "a_chercher", repris automatiquement au prochain lot

            site_web = (item.get("site_web") or "").strip()
            etat[siren]["site_web"] = site_web
            etat[siren]["statut"] = "trouve" if site_web else "non_trouve"
            if site_web:
                nb_trouves += 1
            else:
                nb_non_trouves += 1

        print(f"  {chemin} : {len(resultats)} entrées fusionnées")
        os.rename(chemin, chemin + ".fusionne")

    with open(FICHIER_ETAT, "w", encoding="utf-8") as f:
        json.dump(etat, f, ensure_ascii=False, indent=2)

    restants = sum(1 for i in etat.values() if i["statut"] == "a_chercher")
    print(f"\nFusion terminée : {nb_trouves} sites trouvés, {nb_non_trouves} cherchés sans résultat, "
          f"{nb_non_recherches} non traitées (quota, remises en attente), {nb_inconnus} SIREN inconnus ignorés.")
    print(f"Il reste {restants} entreprise(s) à chercher." if restants
          else "Toutes les entreprises ont été cherchées.")
    print("Relancer preparer_lots_recherche_france.py pour générer les lots restants s'il y en a.")


if __name__ == "__main__":
    main()
