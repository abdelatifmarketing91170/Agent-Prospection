"""
Filtre emails_france.json pour ne garder que des contacts commerciaux
valables sur des PME réellement indépendantes (même logique que
filtrer_prospects.py pour la campagne IDF, adaptée à l'échelle
nationale).

Deux filtres :
1. Adresse générique non-commerciale (dpo@, privacy@, recrutement@,
   rh@, juridique@) : détection automatique par préfixe.
2. Franchise d'un réseau national ou filiale d'un grand groupe : jugé
   au cas par cas, UNIQUEMENT quand le réseau/la marque est
   reconnaissable avec une confiance raisonnable (marque connue, ou
   plusieurs entités distinctes partageant le même domaine — preuve
   directe de réseau). Un simple désaccord entre le nom légal et le
   domaine n'est PAS en soi un motif d'exclusion (beaucoup de PME
   indépendantes utilisent un nom commercial différent) : on exclut
   seulement les cas où la marque/le réseau est identifié avec
   confiance, pour éviter d'écarter à tort des prospects valables.
"""

import json

FICHIER_ENTREE = "emails_france.json"
FICHIER_SORTIE = "emails_france_filtres.json"

PREFIXES_INTERDITS = ("dpo@", "privacy@", "recrutement@", "rh@", "juridique@", "rgpd@")

# siren -> raison de l'exclusion
EXCLUS_FRANCHISE_OU_GROUPE = {
    "428616577": "EXA Infrastructure : filiale d'un grand groupe européen de télécoms/fibre",
    "326802402": "marque internationale OSKA (domaine oska.com)",
    "784611857": "filiale Groupe Laveries (domaine groupe-laveries.fr)",
    "851677823": "réseau Sonance Audition (domaine partagé avec au moins 2 autres entités)",
    "441496726": "réseau Sonance Audition (domaine partagé avec au moins 2 autres entités)",
    "834539629": "réseau Sonance Audition (domaine partagé avec au moins 2 autres entités)",
    "404991069": "réseau DEKRA (nommé explicitement dans la raison sociale)",
    "525105615": "réseau Gem Dépannage (domaine partagé avec une autre entité)",
    "325783181": "réseau Gem Dépannage (domaine partagé avec une autre entité)",
    "501497218": "agent Allianz (page sur agents.allianz.fr)",
    "837723642": "filiale du groupe Vivalto Santé (cliniques privées)",
    "652047416": "réseau immobilier Primo (lesagencesprimo.com)",
    "326911369": "franchise (le nom de l'entreprise contient \"Franchise Distribution\")",
    "487862997": "réseau immobilier Swixim",
    "979239852": "filiale du groupe international Eurofins Scientific (laboratoires)",
    "493759880": "réseau Taxis du Haut Pays (domaine groupe-hautpays.fr)",
    "784655862": "mission diplomatique (Ambassade du Portugal), pas un prospect commercial",
    "538269002": "société d'économie mixte locale (entité publique-privée, pas une PME indépendante)",
    "490072337": "réseau immobilier CIMM Immobilier (nom commercial \"CIMM GESTION\")",
    "887703429": "centre de formation Formapi, réseau adossé aux Chambres de Commerce et d'Industrie (structure para-publique)",
}

# Contacts déjà présents dans la campagne IDF (threads_suivi.json) : l'extraction
# nationale n'exclut pas la région Île-de-France, donc certaines entreprises déjà
# démarchées et suivies individuellement (threads_suivi.json / suivi_envois.csv)
# réapparaissent dans le lot national. On ne les recontacte jamais depuis la
# campagne France.
FICHIER_THREADS_IDF = "threads_suivi.json"


def emails_deja_contactes_idf():
    try:
        with open(FICHIER_THREADS_IDF, encoding="utf-8") as f:
            return set(json.load(f).keys())
    except FileNotFoundError:
        return set()


def main():
    with open(FICHIER_ENTREE, encoding="utf-8") as f:
        emails = json.load(f)

    deja_contactes = emails_deja_contactes_idf()

    conserves = []
    for item in emails:
        if item["email"].lower().startswith(PREFIXES_INTERDITS):
            print(f"EXCLU (adresse générique) : {item['nom']} <{item['email']}>")
            continue
        if item["siren"] in EXCLUS_FRANCHISE_OU_GROUPE:
            print(f"EXCLU (franchise/groupe)  : {item['nom']} <{item['email']}> — {EXCLUS_FRANCHISE_OU_GROUPE[item['siren']]}")
            continue
        if item["email"] in deja_contactes:
            print(f"EXCLU (déjà en campagne IDF) : {item['nom']} <{item['email']}>")
            continue
        conserves.append(item)

    with open(FICHIER_SORTIE, "w", encoding="utf-8") as f:
        json.dump(conserves, f, ensure_ascii=False, indent=2)

    print(f"\n{len(conserves)} destinataires conservés sur {len(emails)}.")
    print(f"Résultat filtré : {FICHIER_SORTIE}")


if __name__ == "__main__":
    main()
