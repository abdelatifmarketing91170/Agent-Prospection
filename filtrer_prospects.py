"""
Filtre brouillons_emails.txt pour ne garder que des contacts commerciaux
valables sur des PME réellement indépendantes.

Deux filtres appliqués :
1. Adresse email générique non-commerciale (dpo@, privacy@, recrutement@,
   rh@, juridique@) : détection automatique par préfixe.
2. Franchise d'un réseau national ou filiale d'un grand groupe : jugé au
   cas par cas sur ces 30 entreprises précises (nom de l'entreprise ou
   domaine de l'email évoquant une marque/réseau connu plutôt qu'une PME
   indépendante) — un filtre générique n'aurait pas de sens ici, donc la
   liste ci-dessous est explicite et justifiée ligne par ligne.
"""

import re

FICHIER_ENTREE = "brouillons_emails.txt"
FICHIER_SORTIE = "brouillons_emails_filtres.txt"

PREFIXES_INTERDITS = ("dpo@", "privacy@", "recrutement@", "rh@", "juridique@")

# siren -> raison de l'exclusion (franchise / filiale de grand groupe)
EXCLUS_FRANCHISE_OU_GROUPE = {
    "428616577": "EXA Infrastructure : filiale d'un grand groupe européen de télécoms/fibre",
    "811016948": "franchise Shiva (domaine shiva.fr)",
    "552082182": "marque nationale Blanc des Vosges (domaine blancdesvosges.fr)",
    "752413674": "franchise Shiva (domaine shiva.fr)",
    "399544246": "franchise Art & Fenêtres (domaine artetfenetres.fr)",
    "900623497": "réseau national Café Joyeux (domaine joyeux.fr)",
    "326802402": "marque internationale OSKA (domaine oska.com)",
    "838648244": "réseau/franchise multi-sites Padel Shot",
    "501905772": "franchise Art & Fenêtres (domaine artetfenetres.fr)",
    "784611857": "filiale Groupe Laveries (domaine groupe-laveries.fr)",
    "539329565": "filiale Groupe Signorini (domaine groupesignorini.com)",
    "951289537": "marque internationale Wycon Cosmetics (domaine wyconcosmetics.com)",
    "844075408": "exclu à la demande de l'utilisateur (réseau régional de centres d'imagerie, pas une PME isolée)",
}


def main():
    with open(FICHIER_ENTREE, encoding="utf-8") as f:
        contenu = f.read()

    blocs = contenu.strip().split("\n\n" + "=" * 60 + "\n\n")

    # On a besoin du siren pour croiser avec EXCLUS_FRANCHISE_OU_GROUPE :
    # on le retrouve via le CSV source (même ordre que la génération).
    import csv
    with open("entreprises_idf_pme_3_19_salaries_priorisees.csv", encoding="utf-8-sig", newline="") as f:
        lignes_csv = list(csv.DictReader(f, delimiter=";"))
    email_vers_siren = {l["email_contact"]: l["siren"] for l in lignes_csv if l.get("email_contact")}

    conserves = []
    for bloc in blocs:
        m = re.match(r"Destinataire : (.+) <(.+)>", bloc)
        nom, email = m.group(1), m.group(2)
        siren = email_vers_siren.get(email, "")

        if any(email.lower().startswith(p) for p in PREFIXES_INTERDITS):
            print(f"EXCLU (adresse générique)   : {nom} <{email}>")
            continue
        if siren in EXCLUS_FRANCHISE_OU_GROUPE:
            print(f"EXCLU (franchise/groupe)    : {nom} <{email}> — {EXCLUS_FRANCHISE_OU_GROUPE[siren]}")
            continue

        conserves.append((nom, email, bloc))

    with open(FICHIER_SORTIE, "w", encoding="utf-8") as f:
        f.write(("\n\n" + "=" * 60 + "\n\n").join(b for _, _, b in conserves))
        f.write("\n")

    print(f"\n{len(conserves)} destinataires conservés sur {len(blocs)}.")
    print(f"Résultat filtré : {FICHIER_SORTIE}")
    print("\nListe finale :")
    for nom, email, _ in conserves:
        print(f"  - {nom} <{email}>")


if __name__ == "__main__":
    main()
