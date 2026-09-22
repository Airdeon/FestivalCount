# Navigation de retour entre les pages

## Contexte et objectif

L'application n'a aucune navigation entre les pages une fois qu'on quitte l'écran d'accueil (`Mes festivals`) : les pages Statistiques, Éditions, Bénévoles, Enregistrement, etc. ne contiennent aucun lien vers une autre page. La seule façon de circuler est de taper une URL à la main ou d'utiliser le bouton retour du navigateur — peu pratique sur PC, et absent en mode kiosque/plein écran sur tablette.

Ce travail ajoute un lien de retour fixe sur chaque page vers sa page parente logique, basé sur la hiérarchie réelle de l'application plutôt que sur l'historique du navigateur (`history.back()`), pour un comportement prévisible même après une redirection de connexion ou un accès direct par URL.

## Architecture

- Nouveau bloc Django `{% block back_link %}{% endblock %}` dans `checkin/templates/checkin/base.html`, placé juste avant `<main>` (en dehors du `{% if user.is_authenticated %}` qui protège déjà le bouton de thème et le formulaire de déconnexion — le lien de retour doit s'afficher aussi sur les pages non authentifiées comme `Créer un compte`).
- Chaque template qui a besoin d'un retour surcharge ce bloc avec un lien `<a class="nav-back" href="...">← Libellé</a>` vers son parent.
- Les pages sans parent logique (point d'entrée ou page d'accueil) ne surchargent pas le bloc — rien ne s'affiche.
- Aucun JavaScript, aucune dépendance à l'historique du navigateur.

## Hiérarchie des pages

| Page (template) | URL name | Lien de retour | Cible |
|---|---|---|---|
| `registration/login.html` | `checkin:login` | *(aucun)* | — |
| `checkin/signup.html` | `checkin:signup` | ← Connexion | `checkin:login` |
| `checkin/select_festival.html` | `checkin:select_festival` | *(aucun — page d'accueil)* | — |
| `checkin/festival_create.html` | `checkin:festival_create` | ← Mes festivals | `checkin:select_festival` |
| `checkin/festival_search.html` | `checkin:festival_search` | ← Mes festivals | `checkin:select_festival` |
| `checkin/register.html` | `checkin:register` | ← Mes festivals | `checkin:select_festival` |
| `checkin/stats.html` | `checkin:stats` | ← Mes festivals | `checkin:select_festival` |
| `checkin/edition_list.html` | `checkin:edition_list` | ← Statistiques | `checkin:stats` (avec `festival_slug`) |
| `checkin/volunteer_list.html` | `checkin:volunteer_list` | ← Statistiques | `checkin:stats` (avec `festival_slug`) |

Éditions et Bénévoles remontent vers Statistiques (tableau de bord de l'organisateur pour ce festival) plutôt que directement vers Mes festivals : un seul saut logique à la fois. `request.festival.slug` est déjà disponible dans ces templates (posé par `checkin/permissions.py`).

## Style

Nouvelle classe CSS `.nav-back` dans `checkin/static/checkin/css/base.css`, consommant les tokens existants du système de thème (pas de nouvelle couleur codée en dur) :

```css
.nav-back {
    position: fixed;
    top: 0.75rem;
    left: 0.75rem;
    z-index: 10;
    display: inline-block;
    padding: 0.6rem 1rem;
    border-radius: var(--radius-sm);
    background: var(--color-surface);
    color: var(--color-text);
    text-decoration: none;
    font-weight: 700;
    box-shadow: var(--shadow-card);
    transition: var(--transition-theme);
}
```

Positionné en haut à gauche, symétrique au bouton de thème / formulaire de déconnexion (haut à droite, `.theme-toggle` / `.logout-form`).

## Gestion des erreurs

Aucune : ce sont des liens statiques rendus côté serveur avec `{% url %}`, rien ne peut échouer au runtime au-delà d'une erreur de routage déjà couverte par les tests Django existants.

## Tests

Pour chacune des 7 pages qui reçoivent un lien de retour, un test `pytest` vérifie que le HTML rendu contient bien le `href` attendu vers la page parente (même approche que les tests existants qui vérifient des attributs `data-*`/URLs dans le HTML rendu). Pas de test pour `login.html`/`select_festival.html` puisqu'elles n'ont pas de lien à vérifier.
