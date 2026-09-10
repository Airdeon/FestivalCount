# Application d'enregistrement des visiteurs par département — Festival Photo

## Contexte et objectif

Application web permettant, lors d'un festival photo, d'enregistrer rapidement le département (ou pays) d'origine de chaque visiteur en un ou deux clics depuis une tablette ou un téléphone, puis de consulter des statistiques et graphiques sur la fréquentation.

L'application est conçue pour être réutilisable par **plusieurs festivals différents**, hébergés depuis une même installation (architecture multi-tenant), chaque festival gérant ses propres éditions, ses propres bénévoles et ses propres statistiques, de façon totalement isolée des autres festivals.

## Stack technique

- **Django** (dernière version stable, 5.x), Python 3.12+.
- Une seule app Django principale (`checkin`) — le projet ne justifie pas un découpage en plusieurs apps.
- **Base de données SQLite** par défaut. Suffisant pour ce volume de données, aucune dépendance externe à installer. Le mode d'hébergement définitif (serveur local sur place ou hébergement cloud) n'est pas encore arrêté ; la configuration Django reste simple et ne présuppose pas l'un ou l'autre.
- **Frontend** : templates Django + CSS responsive mobile-first (gros boutons tactiles, contrastes marqués pour une lisibilité en extérieur) + JavaScript vanilla (fetch API) pour l'interactivité (retour instantané après un clic, bouton « annuler », auto-refresh des statistiques). Pas de framework JS.
- **Graphiques** : [Chart.js](https://www.chartjs.org/), fichier hébergé localement dans les static files Django (pas de CDN), pour garantir le fonctionnement même sans accès internet sur place.
- **Carte de France** : fichier SVG statique de la carte des départements français (chemins identifiés par code département), colorié dynamiquement en JavaScript selon les données. Pas de librairie cartographique ni de tuiles à charger.
- **Authentification** : système d'auth Django standard (`django.contrib.auth`).
- **Tests** : `pytest` + `pytest-django`.

## Modèle de données

### `Festival`
- `nom` (CharField)
- `slug` (SlugField, unique — utilisé dans les URLs, ex. `/f/festival-photo-tignecourt/…`)

Création réservée au développeur/administrateur technique via l'admin Django. C'est une opération rare et ponctuelle, qui inclut aussi la création du tout premier compte `User` et du `Membership` (rôle `organisateur`) associés au nouveau festival. *(Piste d'amélioration future, hors scope de cette version : permettre à un Organisateur de créer directement un nouveau festival depuis l'interface.)*

### `Edition`
- `festival` (FK → `Festival`)
- `nom` (CharField, ex. « Édition 2026 »)
- `date_debut` (DateField)
- `date_fin` (DateField)

Une édition par an, sur un week-end. Créée et gérée par les Organisateurs du festival concerné via un formulaire dédié dans l'application (pas besoin de l'admin Django). Une fois `date_fin` dépassée, l'édition passe automatiquement en lecture seule : plus aucun enregistrement de visiteur n'est possible dessus. Cette règle est appliquée par une simple vérification `date_debut ≤ aujourd'hui ≤ date_fin`, sans champ de verrouillage manuel.

### `Membership`
- `user` (FK → `User`)
- `festival` (FK → `Festival`)
- `role` (CharField avec choix : `organisateur` / `benevole`)

Lie un compte utilisateur à un festival avec un rôle. Un même compte peut être associé à plusieurs festivals, avec des rôles potentiellement différents sur chacun.

### `Origin`
Référentiel des origines possibles (départements, DOM-TOM, pays), **partagé entre tous les festivals** — donnée universelle, non dupliquée par festival.
- `code` (CharField, ex. « 75 », « BE » pour la Belgique, « AUTRE »)
- `nom` (CharField)
- `type` (CharField avec choix : `departement` / `dom_tom` / `pays` / `autre`)
- `groupe` (CharField — regroupement utilisé pour la navigation en 2 clics, voir ci-dessous)
- `ordre_affichage` (IntegerField)

Rempli une fois via une fixture Django (`loaddata`) : les 101 départements français, les DOM-TOM, une dizaine de pays limitrophes, et une entrée générique « Autre pays ».

### `Visit`
- `edition` (FK → `Edition`)
- `origin` (FK → `Origin`)
- `precision_libre` (CharField, optionnel — utilisé si `origin` = « Autre pays », saisie manuelle du pays)
- `horodatage` (DateTimeField, auto)
- `enregistre_par` (FK → `User`)

Un enregistrement = un clic = une ligne. L'annulation ne nécessite pas de champ dédié : le bouton « Annuler » du dernier clic supprime simplement le `Visit` dont l'identifiant a été renvoyé par le serveur juste après sa création.

## Rôles et permissions

Deux rôles, définis par festival via `Membership` :

- **Bénévole** : accès uniquement à la page d'enregistrement de l'édition en cours de son/ses festival(s).
- **Organisateur** : accès à l'enregistrement, aux statistiques, à la création/gestion des éditions, et à la gestion des comptes bénévoles de son/ses festival(s).

Toutes les vues vérifient à la fois l'authentification et l'existence d'un `Membership` valide pour le festival ciblé par l'URL (`/f/<festival_slug>/…`). Un bénévole ou organisateur du festival A n'a aucun accès (lecture ou écriture) aux données du festival B.

**Connexion** : après authentification, si l'utilisateur n'a de `Membership` que sur un seul festival, il y est redirigé directement (vers l'enregistrement pour un bénévole, vers un tableau de bord simple enregistrement/stats pour un organisateur). S'il a des `Membership` sur plusieurs festivals, un écran de sélection du festival s'affiche.

## Page d'enregistrement

URL : `/f/<festival_slug>/enregistrement/`

1. Détermination automatique de l'édition active du festival (celle dont les dates couvrent le jour courant). S'il n'y en a aucune, affichage d'un message clair (« Aucune édition en cours actuellement ») à la place de la grille — aucun enregistrement possible en dehors des dates prévues.
2. **Écran 1 — Choix du groupe** : gros boutons tactiles pour chaque groupe d'origines :
   - Départements 01–19
   - Départements 2A/2B, 21–39
   - Départements 40–59
   - Départements 60–79
   - Départements 80–95
   - DOM-TOM (971–976)
   - Étranger

   (Les bornes exactes des groupes numériques seront ajustées dans la fixture `Origin` pour répartir les 101 départements en groupes équilibrés d'une vingtaine d'entrées chacun ; les plages ci-dessus sont indicatives.)
3. **Écran 2 — Choix précis** : grille des départements/pays du groupe sélectionné, gros boutons numérotés. Pour le groupe « Étranger » : une dizaine de pays proches (Belgique, Suisse, Allemagne, Italie, Espagne, Luxembourg, Pays-Bas, Royaume-Uni, Portugal, Monaco) + un bouton « Autre » ouvrant un champ de saisie libre. Un bouton « ← Retour » permet de revenir au choix du groupe.
4. **Clic sur un département/pays** : requête `fetch` en arrière-plan, sans navigation ni rechargement de page. Un message de confirmation apparaît brièvement en haut de l'écran (« Département 75 enregistré ✓ ») avec un bouton **Annuler** actif pendant quelques secondes. L'écran revient à l'écran 1 (choix du groupe) pour l'entrée suivante.
5. Interface pensée pour un usage tactile en extérieur : gros boutons, contrastes marqués, pas d'interaction nécessitant un survol (hover).

### Gestion des erreurs (page d'enregistrement)
- **Double-clic / clics rapprochés** : désactivation du bouton pendant ~1 seconde après un clic, pour éviter les doublons accidentels.
- **Échec réseau** (requête `fetch` en échec) : message d'erreur explicite affiché à l'écran ; aucun changement silencieux d'état côté interface.

## Page de statistiques

URL : `/f/<festival_slug>/stats/` — accessible aux Organisateurs uniquement.

- **Sélecteur d'édition** en haut de page (menu déroulant), listant toutes les éditions du festival. L'édition en cours est pré-sélectionnée par défaut ; n'importe quelle édition passée peut être consultée pour comparaison.
- **Chiffres clés** : total de visiteurs, nombre de départements représentés, nombre de pays représentés.
- **Carte de France chloroplèthe** : chaque département coloré selon son nombre de visiteurs pour l'édition sélectionnée.
- **Classement / histogramme** : départements triés du plus au moins représenté, avec le nombre exact de visiteurs.
- **Évolution dans le temps** : graphique du nombre d'enregistrements par heure sur la durée de l'édition, pour repérer les pics d'affluence.
- **Auto-refresh** léger (`fetch` toutes les 30 secondes, sans rechargement de page) uniquement lorsque l'édition consultée est l'édition en cours — utile pour un écran affiché en direct pendant le festival. Aucun refresh automatique sur une édition passée (données figées).

## Gestion des bénévoles

Page réservée aux Organisateurs, listant les comptes bénévoles (`Membership` avec `role = benevole`) du festival, avec :
- un formulaire de création d'un nouveau compte bénévole (nom d'utilisateur + mot de passe) — les identifiants sont ensuite communiqués par l'Organisateur à la personne concernée via un canal externe (oral, SMS…), pas d'envoi d'e-mail automatique ;
- une action pour retirer l'accès d'un bénévole (suppression du `Membership` associé, sans suppression du compte `User` lui-même).

## Gestion des erreurs (transverse)

- **Édition hors dates** : traité au niveau de la page d'enregistrement (voir plus haut).
- **Accès non autorisé** (bénévole tentant d'atteindre les statistiques, utilisateur sans `Membership` sur le festival ciblé par l'URL) : redirection avec message clair plutôt qu'une erreur technique brute.

## Tests

`pytest` + `pytest-django`, couvrant notamment :
- création et annulation d'un `Visit` ;
- calcul des statistiques agrégées (chiffres clés, classement, évolution temporelle) ;
- blocage de l'enregistrement en dehors des dates de l'édition active ;
- restriction d'accès par rôle (bénévole vs organisateur) et par festival (étanchéité totale entre les données de deux festivals différents).

## Évolutions futures possibles (hors scope de cette version)

- Permettre à un Organisateur de créer lui-même un nouveau `Festival` depuis l'interface, sans passer par l'admin Django.
