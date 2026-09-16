# Inscription libre et création/adhésion de festival en self-service

## Contexte et objectif

Jusqu'ici, la création d'un compte `User` se faisait exclusivement via l'admin Django (premier organisateur) ou par un organisateur créant directement un compte bénévole depuis l'application. Cette évolution ajoute une inscription libre : n'importe qui peut créer un compte, puis soit créer son propre festival (devenant automatiquement son Organisateur), soit demander à rejoindre un festival existant en tant que Bénévole, sous réserve de validation par un Organisateur de ce festival.

Cette fonctionnalité était explicitement identifiée comme une évolution future dans la spec initiale (*« permettre à un Organisateur de créer lui-même un nouveau Festival depuis l'interface »*) ; elle est maintenant mise en œuvre. Elle inclut également l'ajout d'un bouton de déconnexion, absent de la version précédente (découvert lors d'une vérification manuelle : Django 6.1.1 exige une requête POST pour se déconnecter, et aucun formulaire ne l'exposait).

## Modèle de données

### `MembershipRequest` (nouveau)
- `user` (FK → `User`)
- `festival` (FK → `Festival`)
- `created_at` (DateTimeField, auto)

Représente une demande d'un utilisateur pour rejoindre un festival en tant que **Bénévole** (aucun champ `role` : une demande ne concerne jamais le rôle Organisateur, qui s'obtient uniquement en créant son propre festival). Contrainte d'unicité `(user, festival)` : un utilisateur ne peut avoir qu'une seule demande en attente par festival. La création d'une demande est refusée si l'utilisateur a déjà un `Membership` pour ce festival.

Accepter une demande crée le `Membership` (rôle Bénévole) correspondant et supprime la demande. Refuser une demande la supprime simplement, sans conserver de statut ni empêcher une nouvelle demande ultérieure.

Les modèles `Festival`, `Edition`, `Membership`, `Origin` et `Visit` ne changent pas.

## Inscription

Réutilisation maximale des briques d'authentification fournies par Django plutôt que de les réécrire : `django.contrib.auth.views.LoginView`/`LogoutView` sont déjà en place depuis le début du projet et ne changent pas. Django ne fournit en revanche pas de vue d'inscription clé en main (`RegisterView` n'existe pas dans `django.contrib.auth.views` — c'est un choix délibéré du framework, l'inscription étant jugée trop spécifique à chaque projet) ; la brique réutilisable est `django.contrib.auth.forms.UserCreationForm`, qui gère la validation du nom d'utilisateur, du mot de passe et de sa confirmation via les `AUTH_PASSWORD_VALIDATORS` déjà configurés. Seule une vue fonctionnelle minimale (utilisant ce formulaire puis `django.contrib.auth.login()`) est écrite pour l'assembler.

URL : `/inscription/` (nom `checkin:signup`), accessible sans connexion.

Formulaire basé sur `django.contrib.auth.forms.UserCreationForm` (nom d'utilisateur + mot de passe + confirmation, validé par les `AUTH_PASSWORD_VALIDATORS` déjà configurés). À la soumission valide : création du `User`, connexion automatique, redirection vers `checkin:select_festival`. La page de connexion (`/login/`) affiche un lien vers cette page. Un utilisateur déjà connecté visitant `/inscription/` est directement redirigé vers `checkin:select_festival` (la page n'a pas de sens pour lui).

## Page `select_festival` (tableau de bord)

La vue existante est étendue : en plus de la liste des `Membership` de l'utilisateur (comportement actuel inchangé, y compris l'auto-redirection quand il n'y en a qu'un seul), la page affiche désormais **en permanence** deux actions, qu'il ait déjà des accès ou non :

- **Créer un festival** → `checkin:festival_create`
- **Rejoindre un festival** → `checkin:festival_search`

Cela remplace le message « vous n'avez accès à aucun festival » quand la liste est vide, et reste disponible même quand elle ne l'est pas (un bénévole d'un festival peut vouloir en créer ou en rejoindre un second).

## Création d'un festival

URL : `checkin:festival_create`, accessible à tout utilisateur connecté.

Formulaire ne demandant que le **nom** du festival. Le `slug` est généré automatiquement (`slugify(nom)`), avec ajout d'un suffixe numérique (`-2`, `-3`, …) en cas de collision avec un slug existant. À la soumission valide : création du `Festival`, création d'un `Membership` (rôle Organisateur) pour l'utilisateur courant, redirection vers la page de statistiques du festival nouvellement créé.

## Rejoindre un festival existant

URL : `checkin:festival_search`, accessible à tout utilisateur connecté.

Champ de recherche par nom (`nom__icontains`). Les résultats excluent les festivals où l'utilisateur a déjà un `Membership`. Pour chaque résultat, un bouton « Demander à rejoindre » (POST vers `checkin:membership_request_create`) crée la `MembershipRequest` — sauf si une demande est déjà en attente pour ce festival, auquel cas le bouton est remplacé par le texte « Demande envoyée ». Toute tentative de demande en double (double-clic, contrainte d'unicité) est traitée sans erreur visible pour l'utilisateur.

## Traitement des demandes par l'organisateur

La page « Bénévoles » (`checkin:volunteer_list`) existante gagne une section « Demandes en attente », listant les `MembershipRequest` du festival avec, pour chacune, deux boutons POST :

- **Accepter** (`checkin:membership_request_accept`) : crée le `Membership` Bénévole, supprime la demande.
- **Refuser** (`checkin:membership_request_reject`) : supprime la demande.

Les deux actions sont réservées aux `Membership.ROLE_ORGANISATEUR` du festival concerné (même décorateur `membership_required` que le reste de la page). Si la demande a déjà été traitée entre-temps (double-clic, autre organisateur), l'action est silencieusement sans effet et l'utilisateur est simplement redirigé vers la page.

La création directe d'un compte bénévole par l'organisateur (fonctionnalité existante) reste inchangée, affichée sur la même page en dessous de ces deux nouvelles sections.

## Déconnexion

Ajout d'un formulaire POST (bouton « Se déconnecter », déjà `checkin:logout`) dans `checkin/base.html`, visible sur toutes les pages lorsque `user.is_authenticated`.

## Gestion des erreurs

- Nom d'utilisateur déjà pris à l'inscription : géré nativement par `UserCreationForm`.
- Demande d'adhésion en double ou sur un festival déjà rejoint : bloquée côté vue avant tout accès à la base, avec message clair.
- Acceptation/refus d'une demande déjà traitée : no-op silencieux, pas d'erreur affichée.

## Tests

`pytest` + `pytest-django`, couvrant :
- Inscription : création du compte et connexion automatique ; rejet si nom d'utilisateur déjà pris.
- Création de festival : `Membership` Organisateur créé ; génération d'un slug unique en cas de collision de nom.
- Recherche de festival : exclusion des festivals déjà rejoints ; état « Demande envoyée » si une demande est en attente.
- Création de demande : succès nominal ; rejet si demande déjà en attente ; rejet si déjà membre.
- Acceptation : `Membership` Bénévole créé, demande supprimée, réservé aux Organisateurs du festival concerné.
- Refus : demande supprimée, réservé aux Organisateurs du festival concerné.
- Déconnexion : le bouton apparaît pour un utilisateur connecté, la requête POST déconnecte effectivement.
