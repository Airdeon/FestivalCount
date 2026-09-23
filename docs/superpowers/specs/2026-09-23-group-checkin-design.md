# Enregistrement de groupes en un seul écran

## Contexte et objectif

Aujourd'hui, enregistrer plusieurs visiteurs du même département arrivés ensemble demande de refaire tout le parcours (groupe → département) pour chaque personne. Ce travail ajoute une façon rapide d'enregistrer plusieurs personnes de la même origine en une seule action, sans ralentir le cas le plus fréquent (une personne seule), et sans changer le modèle de données existant (chaque personne reste une ligne `Visit` distincte, donc aucun impact sur les statistiques, le classement, la carte ou les graphiques).

Direction validée avec l'utilisateur via le compagnon visuel de brainstorming (maquettes comparatives du bouton fusionné, de l'icône, et du sélecteur de nombre).

## Bouton d'origine : deux zones fusionnées

Chaque bouton d'origine de type `departement`, `dom_tom` ou `pays` (pas `autre`, voir plus bas) devient une capsule à deux zones visuellement soudées — même ombre, même arrondi extérieur, un seul conteneur avec `overflow: hidden` pour que les deux zones intérieures n'aient pas leurs propres coins arrondis :

```css
.origin-unit {
    display: flex;
    border-radius: var(--radius-md);
    overflow: hidden;
    box-shadow: var(--shadow-button);
}

.origin-button {
    flex: 1;
    min-height: 88px;
    font-size: 1.15rem; /* légèrement réduit vs 1.25rem actuel : la zone principale perd 46px
                            de largeur au profit de la zone groupe, testé visuellement pendant
                            le brainstorming pour que le texte tienne bien sur les libellés longs */
    /* reprend le reste des styles actuels de .origin-button, sans son propre
       border-radius/box-shadow (portés par .origin-unit) */
}

.origin-group-button {
    width: 46px;
    min-height: 88px;
    border: none;
    border-left: 1px solid rgba(255, 255, 255, 0.25);
    background: var(--color-accent-end);
    color: var(--color-accent-text);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
```

- Zone principale (gauche, large) : comportement strictement inchangé — un tap enregistre immédiatement 1 personne, exactement comme aujourd'hui.
- Zone groupe (droite, 46px) : fond bleu plein (`--color-accent-end`, pas un dégradé ni une couleur sombre proche du fond — testé et corrigé pendant le brainstorming visuel car un premier essai plus sombre se confondait avec l'arrière-plan). Une fine bordure la sépare de la zone principale pour rester repérable au doigt sans casser l'effet "un seul bouton".
- Icône : SVG inline (pas d'emoji, rendu identique sur tous les appareils), 3 personnes stylisées, tête = cercle + corps = rectangle à coins très arrondis (pas un cercle simplement coupé net, qui donnait un rendu peu net) :

```html
<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
    <rect x="-1" y="12" width="12" height="10" rx="5"/>
    <circle cx="5" cy="8.5" r="3"/>
    <rect x="13" y="12" width="12" height="10" rx="5"/>
    <circle cx="19" cy="8.5" r="3"/>
    <rect x="4" y="10.5" width="16" height="12" rx="6"/>
    <circle cx="12" cy="7.2" r="3.8"/>
</svg>
```

## Sélecteur de nombre

Tap sur la zone groupe d'une origine → remplace l'écran des boutons d'origine (`#screen-origins`) par un nouvel écran `#screen-group-count`, dans le même esprit que la bascule actuelle groupes/origines (une section HTML de plus, montrée/cachée via l'attribut `hidden`, pas une vraie navigation ni une modale superposée — cohérent avec l'architecture existante, pas de gestion de fond assombri/piège de focus à ajouter).

Contenu de cet écran :
- Un bouton « ← Retour » (même traitement que le back-button existant) qui revient à `#screen-origins` sans rien enregistrer.
- Le nom de l'origine sélectionnée en titre.
- Une grille de boutons numérotés de **1 à 10** (pas de choix "10+" : cas jugé assez rare pour, le cas échéant, recommencer une seconde fois — améliorable plus tard si besoin).
- **Un tap sur un nombre enregistre immédiatement ce nombre de personnes** — pas de bouton « Valider » séparé, cohérent avec la philosophie « un tap = une action » du reste de l'application.

## Backend : création groupée

`checkin:visit_create` (POST JSON) accepte un champ optionnel `count` (entier, 1 à 10, défaut 1 si absent — rétrocompatible avec les appels existants qui n'envoient pas ce champ).

- Validation : `count` absent → 1. `count` présent mais pas un entier entre 1 et 10 → 400 `{"error": "Nombre invalide."}`.
- Création : une boucle simple appelant `Visit.objects.create(...)` `count` fois (pas `bulk_create`, qui ne déclenche pas `auto_now_add` de la même façon — la boucle reproduit exactement le comportement actuel, juste répété).
- Réponse : `{"id": <premier id créé>, "ids": [<tous les ids créés>], "origin_nom": "..."}`. Le champ `id` est conservé tel quel pour ne pas casser les tests existants sur le cas `count=1` ; `ids` est le nouveau champ utilisé par le front pour gérer l'annulation groupée.
- `precision_libre` continue de fonctionner uniquement pour l'origine `autre`, appliqué identiquement à toutes les lignes créées si jamais elle était fournie (cas qui ne se produit pas dans l'UI actuelle puisque `autre` n'aura pas de bouton groupe).

## Frontend : `register.js`

- `showScreenOrigins` : pour chaque origine non-`autre`, génère la capsule à deux boutons (`.origin-button` + `.origin-group-button`) au lieu d'un bouton unique. Le bouton `autre` garde son unique bouton actuel, inchangé.
- Nouvelle fonction `showScreenGroupCount(origin)` : affiche `#screen-group-count`, injecte le titre et les 10 boutons numérotés, chacun appelant `submitVisit(origin.code, "", n)` au clic.
- `submitVisit(originCode, precisionLibre, count)` : le corps JSON envoyé inclut désormais `count`. En cas de succès, `lastVisitIds` (tableau, remplace l'actuel `lastVisitId` singulier) est mis à jour avec `data.ids`.
- Bannière de confirmation : si `count === 1`, texte inchangé (« *Origine* enregistré ✓ ») ; si `count > 1`, « `<N> × <Origine> enregistrés ✓` ».
- Bouton « Annuler » : annule **tout le groupe d'un coup** (décision validée avec l'utilisateur — une action de l'utilisateur = une annulation possible). Implémentation : une requête `visit_cancel` par id de `lastVisitIds` (endpoint existant, aucun changement backend nécessaire pour l'annulation), envoyées en parallèle ; la bannière se ferme quand toutes ont réussi.
- Après un enregistrement (1 ou plusieurs personnes), retour à l'écran des groupes (`showScreenGroups()`), comportement identique à aujourd'hui.

## Origine « Autre pays » : non concernée

Le seul type d'origine à saisie libre (`autre`) garde son comportement actuel (1 personne, texte libre, pas de bouton groupe) — décision prise pendant le brainstorming : cas jugé assez rare pour ne pas complexifier la saisie texte + nombre maintenant, amélioration possible plus tard si le besoin apparaît.

## Gestion des erreurs

- `count` invalide envoyé au serveur (ne devrait pas arriver via l'UI, seulement en cas d'appel direct à l'API) : 400, aucune ligne créée.
- Échec réseau pendant la création groupée : bannière d'erreur existante (« Échec de l'enregistrement... »), rien n'est créé côté serveur si la requête n'aboutit pas (comportement identique à aujourd'hui, juste appliqué à un `count` > 1).
- Échec partiel de l'annulation groupée (une des N requêtes `visit_cancel` échoue) : cas rare accepté tel quel — la bannière d'erreur existante s'affiche ; les visites déjà annulées avec succès le restent (pas de tentative de « rollback », cohérent avec le fait que l'app ne fait déjà aucune synchronisation temps réel ailleurs pour ce genre de cas).

## Tests

- Backend (`checkin/tests/test_views_visit_api.py`) : `count=5` crée 5 `Visit`, réponse contient 5 `ids` ; `count` absent se comporte exactement comme aujourd'hui (tests existants inchangés, `data["id"]` toujours valide) ; `count=0`, `count=11`, `count="abc"` → 400, aucune création.
- Frontend : pas de suite de tests JS dans ce projet (comme pour le reste de `register.js`) — vérification manuelle via Playwright dans le plan d'implémentation : enregistrement d'un groupe de plusieurs tailles, annulation groupée, écran « Autre pays » inchangé, rendu correct dans les deux thèmes (clair/sombre) puisque les nouvelles couleurs utilisent les tokens existants.
