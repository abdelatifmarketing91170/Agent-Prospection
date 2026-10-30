# Brief — Prospection par email (A.S.Digital)

Ce fichier est le brief de référence pour toute action de prospection par email dans ce dépôt. À relire au début de chaque session touchant à la prospection. Les contrôles ci-dessous s'appliquent automatiquement, sans relecture humaine préalable de chaque mail — c'est à l'agent de les faire respecter.

## RÈGLE D'ÉTHIQUE PERMANENTE (prioritaire sur toute autre règle)

Exclusion stricte, jamais de premier mail ni de relance, pour tout prospect relevant de :
- alcool (caves, bars, vignobles, brasseries — NAF 47.25Z, 56.30Z, 46.34Z, 11.xx)
- tabac et vape (NAF 47.26Z)
- CBD
- jeux d'argent (NAF 92.00Z)
- voyance, astrologie, tarot, médiums
- prêt et crédit (NAF 64.92Z, 66.19B, courtiers en prêts)

Statut à appliquer : **"exclu (éthique)"**.

Restaurants et hôtels : autorisés, sauf bars, caves, pubs, brasseries, discothèques et tout établissement dont l'alcool est l'activité principale (exclus, statut "exclu (éthique)").

Gestion de patrimoine et investissement : exclus (statut "exclu (éthique)").

Assurance, banque : jamais de premier mail ni de relance sans validation explicite de l'utilisateur au préalable. Les mettre de côté (statut "en attente (cas gris, à trancher)") et signaler la liste à l'utilisateur.

Cette règle s'applique à tous les lots futurs, premiers mails comme relances, y compris dans les scripts de sourcing/filtrage (`filtrer_prospects*.py`, `personaliser.py`). Pas de colonne NAF disponible dans les fichiers de suivi actuels : filtrer sur les mots-clés du nom et du nom de domaine, et sur le NAF quand il est disponible dans les données sources.

## Identité

- Abdelatif Senhaji, consultant en publicité en ligne.
- A.S.Digital, SIREN 979 115 862.
- Adresse d'envoi dédiée : **asdigital.prospection@gmail.com**.
- **Règle permanente** : TOUS les envois, premiers mails et relances, IDF comme France, partent de **asdigital.prospection@gmail.com**. **Jamais** de abdelatif.marketing@gmail.com, qui ne sert plus qu'à lire les réponses reçues sur les anciens fils.
- Une relance est **toujours un nouveau fil** avec l'objet « Audit gratuit de présence en ligne — {NOM} » (nom avant la première parenthèse), **sans « Re: »**. Plus de suivi de thread_id nécessaire pour les relances.

## Ce qui peut être affirmé (preuves réelles, seules utilisables)

- **Google Ads Search** : pour une boutique de téléphonie en Essonne, CTR supérieur à 9 %, coût par clic réduit d'environ un tiers en quelques semaines, environ 1 clic sur 5 transformé en appel ou en demande d'itinéraire, avec suivi des conversions.
- **Meta Ads** : campagne locale de notoriété à faible coût par personne touchée.
- **TikTok Ads** : expérience sur plusieurs comptes (accroches, visuels, optimisation).
- **Shopify** : création de plusieurs boutiques. Jamais « j'ai accompagné des clients » — c'est une création personnelle, pas un accompagnement client.
- **WordPress** : refonte de la page d'accueil d'un site e-commerce (boutique de golf), conçue d'abord pour mobile.
- **Création de contenu** : visuels publicitaires et vidéos courtes avec outils d'IA.
- **Audit digital** : Google Business, réseaux, site, avec recommandations priorisées.

Utiliser uniquement ces formulations, mot pour mot. **Ne jamais citer de montants en euros, de nombres de contacts ou de budgets.**

## Ce qui n'est pas proposé (ne jamais le mentionner)

SEO technique, community management au quotidien, tournages, développement sur mesure par API.

## Choix de l'offre selon le prospect

- Site daté ou non adapté au mobile → refonte de page d'accueil (WordPress ou Shopify).
- Commerce local sans publicité visible → Google Ads local.
- Boutique en ligne → Shopify, Meta Ads, TikTok Ads.
- Toujours proposer : audit gratuit de la présence en ligne.

## Honnêteté — règles absolues

- Aucun résultat par secteur, aucune moyenne de secteur, aucune promesse.
- Jamais « nos clients », « nos dossiers », « nos campagnes » au pluriel (une seule personne, pas d'équipe).
- Jamais « j'ai regardé la présence Google Ads » ni « aucune campagne active » **sans vérification réelle** de l'observation correspondante.
- Jamais un libellé de secteur présenté comme une recherche Google.

## Observation (obligatoire avant tout envoi)

Une seule observation **vérifiée automatiquement** sur le site du prospect, parmi :
- HTTPS absent
- pas de version mobile
- copyright obsolète
- pas de formulaire de contact
- pas d'appel à l'action sur la page d'accueil

**Si rien n'est vérifiable sur le site → aucun envoi pour ce prospect.** Pas d'observation inventée, pas de supposition.

## Ciblage

Exclure : santé, funéraire, juridique, franchises et réseaux, grands groupes.
Garder uniquement des adresses professionnelles : exclure gmail, hotmail, yahoo, orange (adresses grand public).

## Doublons (vérification obligatoire avant tout envoi)

Vérifier l'adresse contre **suivi_envois.csv ET suivi_france.csv** (les deux campagnes précédentes, IDF et France) — jamais recontacter une entreprise déjà présente dans l'un ou l'autre fichier, même pour un nouveau lot ou une nouvelle liste.

## Envoi

- Montée en charge : 10 mails/jour les 3 premiers jours, 20/jour les 4 jours suivants, puis 30/jour (relances comprises).
- Jours d'envoi : du lundi au vendredi (jours ouvrés uniquement).
- Fenêtre horaire : 8h30–10h30.
- Espacement : 3 à 4 minutes entre deux envois.
- Mail court, vouvoiement, **75 à 100 mots (jamais moins de 70)**, ton sobre.
- Signature :
  ```
  Abdelatif Senhaji
  A.S.Digital — SIREN 979 115 862
  Pour ne plus recevoir de message, répondez STOP.
  ```
  Pas de numéro de téléphone.

## Format HTML

- Mise en forme HTML sobre : en-tête léger avec le nom A.S.Digital, signature avec mise en forme propre (gras/espacement, pas de tableau complexe).
- **Jamais d'image** : ni en pièce jointe, ni dans le corps du mail (dégrade la délivrabilité).
- Deux squelettes (un sobre, un plus visuel) validés par l'utilisateur avant toute application — ne pas improviser une troisième variante sans validation.

## Reprise sur interruption

Si une session s'arrête en cours de lot, le prochain lancement reprend **exactement** où il s'est arrêté (vérifier le dernier statut dans suivi_envois.csv). Jamais recompter depuis zéro, jamais redémarrer le quota du jour.

## Comptage quotidien

Le quota journalier (10/20/30) se compte sur les **envois réels de la date du jour calendaire**, jamais sur le total cumulé du fichier de suivi.

## Contrôles automatiques avant chaque envoi

Refuser d'envoyer si le mail contient une des expressions suivantes (ou un montant en euros) :
- « en général »
- « moyenne du secteur »
- « nos clients »
- « nos dossiers »
- « nos campagnes »
- « aucune campagne active »
- « j'ai regardé la présence »

## Arrêts automatiques

Tout stopper et écrire **ALERTE.txt** si :
- plus de 5 % de rebonds sur les 50 derniers envois
- un signalement de spam
- un avertissement ou une limitation de Gmail

## Objet du mail

Si le nom du prospect est un nom de personne ou une raison sociale peu parlante (ex. « GOUDY » pour cote-immobilier.com), utiliser le nom de domaine sans extension à la place du nom dans l'objet « Audit gratuit de présence en ligne — {NOM} ».

## Numéro de relance avant le message final

Avant d'envoyer le texte de relance 4 (dernier message), compter tous les mails déjà envoyés à ce prospect en vérifiant Gmail (pas seulement le statut du fichier de suivi, qui peut être erroné) — adresse par adresse, toutes boîtes confondues. N'envoyer le texte de relance 4 que si c'est réellement la 4e relance ; sinon envoyer le texte du numéro réellement dû.

## Réponses et suivi

- STOP, « désabonnez-moi », « ne plus recevoir » → ajouter l'adresse à la liste de désinscription, jamais recontactée.
- Réponses d'absence (auto-reply) → ignorer.
- Réponse positive ou question → **ne jamais répondre soi-même** ; écrire dans **A_TRAITER.txt** et arrêter les relances pour ce prospect.
- Rebonds → retirer l'adresse.
- Maximum 4 relances, dans le même fil, espacées de 4-5 jours, chacune avec un angle différent de la précédente.

## Fichiers de suivi

- **suivi_envois.csv** : colonnes nom, adresse, observation, date, statut. Vérifier avant chaque envoi pour éviter les doublons.
- **rapport_du_jour.txt** : à écrire chaque jour, en 5 lignes : envoyés, rebonds, STOP, réponses à traiter, alertes.

## Campagnes précédentes (ne pas toucher)

- **IDF** (`suivi_envois.csv`, `threads_suivi.json`) : 16 contacts, campagne terminée sauf GOLD NORD en attente d'audit.
- **France** (`suivi_france.csv`, `threads_suivi_france.json`) : 159 contacts, campagne terminée. Utilisait l'ancienne adresse abdelatif.marketing@gmail.com et des formulations désormais interdites par ce brief — ne pas réutiliser ces templates, ne pas relancer ces contacts en dehors des règles de relance déjà en place pour cette campagne.

Toute nouvelle prospection (nouvelle liste, nouveaux envois) doit suivre ce brief dans son intégralité, pas les anciens scripts/templates des campagnes IDF et France.
