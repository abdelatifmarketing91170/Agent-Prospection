"""
Prépare (ou met à jour) l'état de la recherche de sites web et découpe
les entreprises restant à chercher en lots pour des agents de recherche
web à budget frais.

Reprise automatique : contrairement à la 1ère campagne (où il avait
fallu que l'utilisateur redemande une "2e passe" pour les ~110
entreprises non traitées faute de quota), ce script lit l'état déjà
connu (FICHIER_ETAT) et ne redonne à chercher QUE les entreprises encore
au statut "a_chercher" — qu'elles viennent d'un 1er lancement ou d'un
lot précédent coupé par un quota. Il suffit de relancer ce script après
avoir fusionné les résultats (fusionner_resultats_recherche.py) : s'il
reste des entreprises "a_chercher", il regénère de nouveaux lots pour
elles ; sinon il le dit et il n'y a plus rien à faire.

Usage : python3 preparer_lots_recherche.py [fichier_csv] [taille_lot]
"""

import csv
import json
import os
import sys

FICHIER_ETAT = "recherche_sites_etat.json"
DOSSIER_LOTS = "lots_recherche"
TAILLE_LOT_DEFAUT = 40  # reste large sous le quota de ~200 requêtes/agent


def charger_etat():
    if os.path.exists(FICHIER_ETAT):
        with open(FICHIER_ETAT, encoding="utf-8") as f:
            return json.load(f)
    return {}


def sauvegarder_etat(etat):
    with open(FICHIER_ETAT, "w", encoding="utf-8") as f:
        json.dump(etat, f, ensure_ascii=False, indent=2)


def initialiser_depuis_csv(etat, fichier_csv):
    """Ajoute à l'état les entreprises du CSV source qui n'y figurent pas
    encore (nouvelle campagne ou nouvelles entreprises), sans jamais
    toucher aux entrées déjà connues (donc sans perdre un résultat déjà
    trouvé)."""
    with open(fichier_csv, encoding="utf-8-sig", newline="") as f:
        lignes = list(csv.DictReader(f, delimiter=";"))

    ajoutees = 0
    for ligne in lignes:
        siren = ligne["siren"]
        if siren not in etat:
            etat[siren] = {
                "nom": ligne["nom"],
                "adresse": ligne["adresse"],
                "statut": "a_chercher",
                "site_web": "",
            }
            ajoutees += 1
    if ajoutees:
        print(f"{ajoutees} nouvelles entreprises ajoutées à l'état (depuis {fichier_csv}).")
    return etat


def main():
    fichier_csv = sys.argv[1] if len(sys.argv) > 1 else "entreprises_idf_pme_3_19_salaries.csv"
    taille_lot = int(sys.argv[2]) if len(sys.argv) > 2 else TAILLE_LOT_DEFAUT

    etat = charger_etat()
    if os.path.exists(fichier_csv):
        etat = initialiser_depuis_csv(etat, fichier_csv)
        sauvegarder_etat(etat)

    a_chercher = [
        {"siren": siren, "nom": info["nom"], "adresse": info["adresse"]}
        for siren, info in etat.items()
        if info["statut"] == "a_chercher"
    ]

    trouves = sum(1 for i in etat.values() if i["statut"] == "trouve")
    non_trouves = sum(1 for i in etat.values() if i["statut"] == "non_trouve")

    print(f"État : {len(etat)} entreprises au total — {trouves} trouvées, "
          f"{non_trouves} cherchées sans résultat, {len(a_chercher)} restent à chercher.")

    if not a_chercher:
        print("\nRien à faire : toutes les entreprises ont déjà été cherchées.")
        return

    os.makedirs(DOSSIER_LOTS, exist_ok=True)
    # Nettoie les anciens lots pour ne pas en traiter un obsolète par erreur.
    for nom_fichier in os.listdir(DOSSIER_LOTS):
        if nom_fichier.startswith("lot_") and nom_fichier.endswith(".json"):
            os.remove(os.path.join(DOSSIER_LOTS, nom_fichier))

    nb_lots = (len(a_chercher) + taille_lot - 1) // taille_lot
    for i in range(nb_lots):
        lot = a_chercher[i * taille_lot:(i + 1) * taille_lot]
        chemin = os.path.join(DOSSIER_LOTS, f"lot_{i}.json")
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(lot, f, ensure_ascii=False, indent=2)
        print(f"  {chemin} : {len(lot)} entreprises")

    print(f"\n{len(a_chercher)} entreprises à chercher, réparties en {nb_lots} lot(s) dans {DOSSIER_LOTS}/.")
    print("Chaque lot doit être confié à un agent de recherche avec un budget WebSearch frais,")
    print("qui doit écrire son résultat dans lots_recherche/resultat_<i>.json au même format que")
    print("le lot, en ajoutant pour CHAQUE entreprise : site_web (\"\" si rien trouvé) ET")
    print("recherche_effectuee (true/false — false UNIQUEMENT si le quota a coupé avant de la traiter).")
    print("Ensuite : python3 fusionner_resultats_recherche.py, puis relancer ce script pour voir s'il")
    print("reste des lots à traiter (reprise automatique, sans repartir de zéro).")


if __name__ == "__main__":
    main()
