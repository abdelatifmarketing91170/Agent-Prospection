"""
Génère 30 emails de prospection courts et personnalisés à partir du CSV
trié par score de priorité, et les exporte dans brouillons_emails.txt.

Sélection des destinataires : les emails de prospection étant destinés à
être réellement envoyés, on prend les 30 entreprises au score de
priorité le plus élevé PARMI celles qui ont un email_contact (impossible
d'envoyer un email à une entreprise dont on n'a pas l'adresse — les
scores les plus hauts du fichier correspondent justement à des
entreprises sans aucun site, donc sans email trouvé).

Conséquence : toutes les entreprises retenues ont déjà un site ET un
email (sinon elles n'auraient pas d'email_contact), donc leur point
faible n'est jamais "pas de site" mais l'absence de campagne Google Ads
visible — c'est cet angle qui est utilisé dans l'accroche.

Le secteur (à partir du code NAF) et le type de preuve à mettre en avant
(Google Ads pour le commerce/service local, Shopify pour le commerce de
produits qui se prête à une boutique en ligne) sont déterminés au cas
par cas pour ces 30 entreprises précises, car un mapping générique
NAF -> secteur/preuve n'aurait pas de sens sur un jeu aussi restreint.
"""

import csv
import re

FICHIER_ENTREE = "entreprises_idf_pme_3_19_salaries_priorisees.csv"
FICHIER_SORTIE = "brouillons_emails.txt"
NB_DESTINATAIRES = 30

# siren -> (secteur au format court, "ads" ou "shopify")
SECTEUR_ET_PREUVE = {
    "821917671": ("intermédiaire de commerce", "ads"),          # ACCEDONS
    "850768029": ("commerce de lunetterie/optique", "shopify"),  # CONSCIOUS EYEWEAR
    "808770812": ("boulangerie-pâtisserie", "ads"),              # ETVOILA (ARCHIBALD)
    "428616577": ("infrastructure télécoms", "ads"),             # EXA INFRASTRUCTURE FRANCE
    "492735741": ("bijouterie", "shopify"),                      # GOLD NORD
    "811016948": ("ménage à domicile", "ads"),                   # HEV SERVICES
    "552082182": ("linge de maison", "shopify"),                 # HOME TISSAGES
    "752413674": ("ménage à domicile", "ads"),                   # HOUSEWORK & CO
    "399544246": ("menuiserie/isolation", "ads"),                # ISOPROTECT
    "900623497": ("restauration rapide", "ads"),                 # JOYEUX INSIDE
    "353347222": ("stationnement/parking", "ads"),               # LEVAPARC
    "822160990": ("coworking", "ads"),                           # LMDC
    "326802402": ("prêt-à-porter", "shopify"),                   # OSKA PARIS
    "838648244": ("club de padel", "ads"),                       # PADEL SHOT
    "495235368": ("conseil financier", "ads"),                   # PLURIFINANCES
    "501905772": ("menuiserie/fenêtres", "ads"),                 # QUAL'ISO
    "844075408": ("imagerie médicale", "ads"),                   # RESEAU FRANCILIEN D'IMAGERIE
    "420848673": ("voyages scolaires", "ads"),                   # SARL GECTURE (SCOL'VOYAGES)
    "784611857": ("laverie automatique", "ads"),                 # SELF BLANC DRUG
    "849239587": ("solutions logicielles", "ads"),               # SNAPDESK
    "539329565": ("épicerie fine/produits gastronomiques", "shopify"),  # ST FRANCE
    "789895968": ("courtage en assurance", "ads"),               # SYNALP FINANCE
    "324684190": ("loisirs/divertissement", "ads"),              # UNIVERS-LOISIRS
    "951289537": ("cosmétiques/parfumerie", "shopify"),          # WYCON FRANCE
    "523167658": ("analyses et contrôles techniques", "ads"),    # ADC
    "523448371": ("formation professionnelle", "ads"),           # AFC GROUPE
    "445278542": ("conseil financier", "ads"),                   # AVICAP
    "844980763": ("ingénierie BIM/architecture", "ads"),         # BIM ARCHI TECH
    "388116170": ("garage automobile", "ads"),                   # C.2.P.
    "840340525": ("contrôle technique/inspection", "ads"),       # C.E.S PRO CONSULT
}

ACCROCHES = [
    "En regardant {nom}, je ne vois pas de campagne Google Ads active sur des recherches comme « {secteur} {ville} ».",
    "J'ai cherché « {secteur} {ville} » sur Google : {nom} n'apparaît dans aucune publicité, seuls des concurrents avec des Ads sont visibles en premier.",
    "Sur les recherches « {secteur} {ville} », {nom} n'a pas de présence publicitaire visible sur Google.",
]

PREUVES_ADS = [
    "Sur des dossiers {secteur}, nos campagnes Google Ads Search tournent à 8-9% de CTR, contre 2-3% de moyenne sur le secteur.",
    "En {secteur}, on obtient en général 8-9% de CTR sur Search, contre 2-3% pour la moyenne du secteur.",
]

PREUVES_SHOPIFY = [
    "On a accompagné plusieurs boutiques {secteur} sur Shopify, avec catalogue et paiement en ligne opérationnels en 2-3 semaines.",
    "Notre expérience Shopify sur des boutiques {secteur} permet de lancer une vitrine en ligne complète (catalogue + paiement) en 2-3 semaines.",
]

PROPOSITIONS = [
    "Je vous propose un audit digital gratuit (fiche Google Business, réseaux sociaux, site) pour repérer concrètement où vous perdez des clients.",
    "Un audit gratuit de votre présence digitale (Google Business, réseaux, site) montrerait rapidement où partent vos prospects.",
]

CTA = [
    "Un appel de 15 minutes cette semaine pour en discuter ?",
    "15 minutes cette semaine pour en parler ?",
]

DESINSCRIPTION = "Pour vous désabonner de ces emails, répondez « STOP » à ce message."
SIGNATURE = "A.S.Digital"


def extraire_ville(adresse):
    match = re.search(r"\d{5}\s+(.+)$", adresse)
    return match.group(1).title() if match else ""


def generer_email(index, ligne):
    siren = ligne["siren"]
    secteur, type_preuve = SECTEUR_ET_PREUVE[siren]
    nom = ligne["nom"]
    ville = extraire_ville(ligne["adresse"])

    accroche = ACCROCHES[index % len(ACCROCHES)].format(nom=nom, secteur=secteur, ville=ville)
    if type_preuve == "shopify":
        preuve = PREUVES_SHOPIFY[index % len(PREUVES_SHOPIFY)].format(secteur=secteur)
    else:
        preuve = PREUVES_ADS[index % len(PREUVES_ADS)].format(secteur=secteur)
    proposition = PROPOSITIONS[index % len(PROPOSITIONS)]
    cta = CTA[index % len(CTA)]

    corps = "\n".join([
        f"Bonjour,",
        accroche,
        preuve,
        proposition,
        cta,
        "",
        SIGNATURE,
        "",
        DESINSCRIPTION,
    ])
    return corps


def main():
    with open(FICHIER_ENTREE, encoding="utf-8-sig", newline="") as f:
        lignes = list(csv.DictReader(f, delimiter=";"))

    avec_email = [ligne for ligne in lignes if ligne.get("email_contact")]
    destinataires = avec_email[:NB_DESTINATAIRES]

    if len(destinataires) < NB_DESTINATAIRES:
        print(f"Attention : seulement {len(destinataires)} entreprises avec email disponibles.")

    manquants = [l["siren"] for l in destinataires if l["siren"] not in SECTEUR_ET_PREUVE]
    if manquants:
        raise SystemExit(f"Secteur non renseigné pour : {manquants}")

    blocs = []
    for i, ligne in enumerate(destinataires):
        entete = f"Destinataire : {ligne['nom']} <{ligne['email_contact']}>"
        corps = generer_email(i, ligne)
        blocs.append(entete + "\n\n" + corps)

    with open(FICHIER_SORTIE, "w", encoding="utf-8") as f:
        f.write(("\n\n" + "=" * 60 + "\n\n").join(blocs))
        f.write("\n")

    print(f"{len(destinataires)} emails générés dans {FICHIER_SORTIE}")


if __name__ == "__main__":
    main()
