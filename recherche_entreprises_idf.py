"""
Recherche d'entreprises franciliennes via l'API publique gratuite
recherche-entreprises.api.gouv.fr, et export des résultats en CSV.

Critères appliqués :
- Région          : Île-de-France (code région INSEE "11")
- Effectif salarié : 3 à 19 salariés (codes INSEE "02", "03", "11")
- Catégorie        : PME
- État             : entreprises actives uniquement

Aucune valeur ci-dessus n'est devinée : elles ont été vérifiées dans le code
source de l'API (fichiers app/labels/regions.json et
app/labels/tranches-effectifs.json du repo annuaire-entreprises-data-gouv-fr/search-api),
car cette API utilise des codes précis et non des bornes libres.
"""

import csv
import time

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://recherche-entreprises.api.gouv.fr/search"

# L'API renvoie parfois une erreur 400 si aucun User-Agent "de navigateur"
# n'est fourni. On imite donc un vrai navigateur.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

REGION_ILE_DE_FRANCE = "11"
CATEGORIE_ENTREPRISE = "PME"
ETAT_ADMINISTRATIF_ACTIF = "A"

# "3 à 19 salariés" ne correspond pas à un seul code INSEE : il faut combiner
# trois tranches. On interroge donc l'API séparément pour chacune, puis on
# fusionne les résultats (l'API ne documentant pas officiellement le
# passage de plusieurs codes en une seule requête, on évite de le supposer).
TRANCHES_EFFECTIF_3_A_19 = {
    "02": "3 à 5 salariés",
    "03": "6 à 9 salariés",
    "11": "10 à 19 salariés",
}

PER_PAGE = 25          # taille de page utilisée dans les exemples officiels de l'API
MAX_ENTREPRISES = 300  # on veut "plusieurs centaines" de résultats, pas la totalité
PAUSE_ENTRE_REQUETES = 0.3  # secondes, par courtoisie envers l'API publique
NB_TENTATIVES_MAX = 3

CSV_FIELDNAMES = [
    "siren",
    "nom",
    "adresse",
    "code_naf",
    "tranche_effectif_salarie_code",
    "tranche_effectif_salarie_libelle",
]

FICHIER_SORTIE = "entreprises_idf_pme_3_19_salaries.csv"


def appeler_api(params):
    """
    Appelle l'API avec les paramètres donnés et renvoie le JSON de réponse.
    Réessaie automatiquement en cas d'erreur réseau ou de réponse serveur
    temporaire (5xx), car ce sont les seuls cas où retenter a du sens.
    """
    derniere_erreur = None
    for tentative in range(1, NB_TENTATIVES_MAX + 1):
        try:
            reponse = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
            if reponse.status_code >= 500:
                raise requests.HTTPError(f"Erreur serveur {reponse.status_code}")
            reponse.raise_for_status()
            return reponse.json()
        except requests.RequestException as erreur:
            derniere_erreur = erreur
            attente = 2 * tentative
            print(f"  Échec de la requête ({erreur}), nouvelle tentative dans {attente}s...")
            time.sleep(attente)
    raise RuntimeError(f"L'API n'a pas répondu après {NB_TENTATIVES_MAX} tentatives : {derniere_erreur}")


def recuperer_entreprises_pour_tranche(tranche_code, entreprises_par_siren):
    """
    Récupère, page par page, toutes les entreprises correspondant à une
    tranche d'effectif donnée, et les ajoute au dictionnaire
    entreprises_par_siren (clé = SIREN, ce qui élimine les doublons entre
    les différentes tranches interrogées).
    S'arrête dès que MAX_ENTREPRISES est atteint, ou quand l'API n'a plus
    de résultats.
    """
    page = 1
    while True:
        if len(entreprises_par_siren) >= MAX_ENTREPRISES:
            return

        params = {
            "region": REGION_ILE_DE_FRANCE,
            "categorie_entreprise": CATEGORIE_ENTREPRISE,
            "etat_administratif": ETAT_ADMINISTRATIF_ACTIF,
            "tranche_effectif_salarie": tranche_code,
            "page": page,
            "per_page": PER_PAGE,
        }

        data = appeler_api(params)
        resultats_page = data.get("results", [])
        total_pages = data.get("total_pages", page)

        print(
            f"  Tranche {tranche_code} ({TRANCHES_EFFECTIF_3_A_19[tranche_code]}) "
            f"- page {page}/{total_pages} - {len(resultats_page)} entreprises reçues"
        )

        if not resultats_page:
            break

        for entreprise in resultats_page:
            siren = entreprise.get("siren")
            if siren and siren not in entreprises_par_siren:
                entreprises_par_siren[siren] = entreprise
                if len(entreprises_par_siren) >= MAX_ENTREPRISES:
                    break

        if page >= total_pages:
            break

        page += 1
        time.sleep(PAUSE_ENTRE_REQUETES)


def extraire_ligne_csv(entreprise):
    """
    Transforme un résultat brut de l'API (structure JSON complexe) en une
    ligne "plate" prête pour le CSV, avec uniquement les champs demandés.
    """
    siege = entreprise.get("siege") or {}

    adresse = siege.get("adresse") or ""

    # La tranche d'effectif est en général présente au niveau de l'unité
    # légale ; on se rabat sur celle du siège si elle manque.
    tranche_code = entreprise.get("tranche_effectif_salarie") or siege.get("tranche_effectif_salarie") or ""

    return {
        "siren": entreprise.get("siren", ""),
        "nom": entreprise.get("nom_complet") or entreprise.get("nom_raison_sociale") or "",
        "adresse": adresse,
        "code_naf": entreprise.get("activite_principale", ""),
        "tranche_effectif_salarie_code": tranche_code,
        "tranche_effectif_salarie_libelle": TRANCHES_EFFECTIF_3_A_19.get(tranche_code, ""),
    }


def main():
    entreprises_par_siren = {}

    for tranche_code in TRANCHES_EFFECTIF_3_A_19:
        if len(entreprises_par_siren) >= MAX_ENTREPRISES:
            break
        recuperer_entreprises_pour_tranche(tranche_code, entreprises_par_siren)

    lignes = [extraire_ligne_csv(e) for e in entreprises_par_siren.values()]

    with open(FICHIER_SORTIE, "w", newline="", encoding="utf-8") as fichier_csv:
        writer = csv.DictWriter(fichier_csv, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(lignes)

    print(f"\n{len(lignes)} entreprises exportées dans {FICHIER_SORTIE}")


if __name__ == "__main__":
    main()
