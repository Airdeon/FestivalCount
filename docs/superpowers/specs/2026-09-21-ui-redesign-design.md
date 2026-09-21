# Refonte visuelle de l'interface (thèmes clair/sombre)

## Contexte et objectif

L'interface actuelle (CSS vanilla minimal, un seul thème bleu/blanc) est fonctionnelle mais volontairement brute. Cette refonte introduit un vrai système de design (tokens CSS, ombres, dégradés, transitions) et un thème sombre/clair basculable, sur l'ensemble de l'application. Les directions visuelles ont été validées avec l'utilisateur via le compagnon visuel de brainstorming (maquettes comparatives des pages Enregistrement et Statistiques, dans les deux thèmes).

## Système de design tokens

Variables CSS (custom properties) définies sur `:root`, redéfinies selon l'attribut `data-theme` porté par `<html>`. Un seul jeu de tokens nommés est utilisé partout dans le CSS applicatif — aucune couleur codée en dur en dehors de cette définition.

### Thème sombre (`data-theme="dark"`, valeur par défaut)

```css
:root, [data-theme="dark"] {
  --color-bg: radial-gradient(circle at 20% -10%, #1f2937 0%, #0b0d14 55%);
  --color-bg-solid: #0b0d14; /* fallback pour propriétés n'acceptant pas de gradient */
  --color-text: #e5e7eb;
  --color-text-muted: #9ca3af;

  --color-surface: rgba(255, 255, 255, 0.04);
  --color-surface-border: rgba(255, 255, 255, 0.08);

  --color-accent-start: #3b82f6;
  --color-accent-end: #1d4ed8;
  --color-accent-text: #ffffff;
  --color-accent-soft-start: rgba(59, 130, 246, 0.18);
  --color-accent-soft-end: rgba(29, 78, 216, 0.08);
  --color-accent-solid: #60a5fa; /* pour texte/valeurs KPI, grilles de graphiques */

  --color-success-bg-start: #0f5132;
  --color-success-bg-end: #0a3622;
  --color-success-text: #86efac;

  --color-error-bg: #611a15;
  --color-error-text: #ffffff;

  --shadow-container: 0 20px 50px -20px rgba(0, 0, 0, 0.5);
  --shadow-card: 0 8px 18px -12px rgba(0, 0, 0, 0.5);
  --shadow-button: 0 10px 20px -10px rgba(37, 99, 235, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.15);
}
```

### Thème clair (`data-theme="light"`)

```css
[data-theme="light"] {
  --color-bg: #eef1f6;
  --color-bg-solid: #eef1f6;
  --color-text: #0f172a;
  --color-text-muted: #64748b;

  --color-surface: #ffffff;
  --color-surface-border: rgba(15, 23, 42, 0.06);

  --color-accent-start: #3b82f6;
  --color-accent-end: #1d4ed8;
  --color-accent-text: #ffffff;
  --color-accent-soft-start: rgba(59, 130, 246, 0.10);
  --color-accent-soft-end: rgba(96, 165, 250, 0.04);
  --color-accent-solid: #1d4ed8;

  --color-success-bg-start: #dcfce7;
  --color-success-bg-end: #bbf7d0;
  --color-success-text: #14532d;

  --color-error-bg: #fdecea;
  --color-error-text: #611a15;

  --shadow-container: 0 16px 40px -20px rgba(15, 23, 42, 0.2);
  --shadow-card: 0 8px 18px -12px rgba(15, 23, 42, 0.18);
  --shadow-button: 0 10px 20px -10px rgba(37, 99, 235, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.25);
}
```

### Tokens indépendants du thème

```css
:root {
  --radius-lg: 20px;
  --radius-md: 14px;
  --radius-sm: 10px;
  --transition-theme: background-color 0.35s ease, color 0.35s ease, border-color 0.35s ease;
  --transition-interactive: transform 0.15s ease, box-shadow 0.25s ease;
}
```

Ces valeurs remplacent les couleurs actuellement codées en dur dans `checkin/static/checkin/css/base.css` (`#2563eb`, `#f5f5f5`, etc.). Tous les boutons, cartes, bannières de message existants sont réécrits pour consommer ces variables plutôt que des couleurs fixes.

## Mécanisme de bascule de thème

- Attribut `data-theme` sur `<html>`, valeur `dark` par défaut.
- Un script inline dans `<head>` (avant le CSS, avant tout rendu visible) lit `localStorage.getItem('theme')` et pose `data-theme` immédiatement s'il existe une préférence enregistrée — évite le flash (fond clair qui apparaît une fraction de seconde avant de passer en sombre, ou inversement).
- Bouton 🌙/☀️ ajouté dans `checkin/templates/checkin/base.html`, à côté du bouton « Se déconnecter » existant, visible uniquement pour un utilisateur connecté (comme le bouton de déconnexion). Un clic bascule `data-theme` entre `dark`/`light` et écrit le choix dans `localStorage`.
- Aucune dépendance serveur : le thème n'est pas stocké en base de données ni lié au compte utilisateur, c'est une préférence de navigateur (cohérent avec l'app utilisée sur des tablettes partagées où un compte peut être utilisé sur plusieurs appareils avec des préférences différentes).

## Page d'enregistrement

Reprend le mockup validé : bouton de thème + bannière de confirmation en haut, grille de groupes/départements en boutons avec dégradé `--color-accent-start` → `--color-accent-end`, ombre `--shadow-button`, légère réduction d'échelle (`transform: scale(0.96)`) au clic. Coins arrondis `--radius-md` (boutons), `--radius-lg` (conteneurs). Le message d'erreur réseau utilise `--color-error-bg`/`--color-error-text`.

## Page de statistiques

Reprend le mockup validé :
- **Chiffres clés** en cartes KPI (`--color-surface`, `--shadow-card`), valeur en grand avec `--color-accent-solid`, libellé en petit avec `--color-text-muted`.
- **Classement** en barres horizontales dégradées (`--color-accent-start` → un ton plus clair), sur fond `--color-surface`.
- **Carte de France** (`checkin/static/checkin/js/map.js`) : le fond neutre actuel (`#f3f4f6`) et le contour (`#9ca3af`) doivent utiliser `--color-surface`/`--color-surface-border` ; l'échelle de couleur des départements visités (`COLOR_SCALE`, actuellement 5 teintes violettes fixes) est remplacée par une échelle basée sur `--color-accent-start`/`--color-accent-end` pour rester cohérente avec le reste de l'interface dans les deux thèmes. Comme ces couleurs sont définies en CSS et que `map.js` colore les `<path>` en JavaScript, le script lit les valeurs calculées (`getComputedStyle`) des variables CSS plutôt que de dupliquer les couleurs en JS.
- **Graphiques Chart.js** (`checkin/static/checkin/js/stats.js`) : couleurs de grille, texte des axes et légende, et couleur des barres/lignes doivent aussi être lues depuis les variables CSS calculées, pour rester lisibles et cohérentes dans les deux thèmes (actuellement Chart.js utilise ses couleurs par défaut, non adaptées à un fond sombre).

## Pages secondaires

Connexion, inscription, sélection/recherche/création de festival, gestion des éditions, gestion des bénévoles : pas de traitement visuel spécifique au-delà de l'héritage des tokens (fond, texte, boutons, champs de formulaire, cartes pour les listes). Les formulaires (`<input>`, `<select>`) adoptent un style cohérent (fond `--color-surface`, bordure `--color-surface-border`, coins `--radius-sm`) mais restent simples — pas de disposition en carte KPI comme la page stats.

## Gestion des erreurs

- **FOUC (flash de contenu non stylé)** : géré par le script inline de lecture du thème avant rendu (voir plus haut).
- **JavaScript désactivé** : le thème reste sombre par défaut (valeur de `data-theme` sur `<html>` posée côté serveur/HTML statique), seul le bouton de bascule est inopérant — dégradation raisonnable, pas de fonctionnalité perdue.
- **`localStorage` indisponible** (navigation privée stricte) : le `try/catch` autour de la lecture/écriture évite une erreur JS bloquante ; le thème retombe simplement sur la valeur par défaut à chaque chargement.

## Tests

Ce travail est purement visuel (CSS + petites additions JS pour le thème et la lecture des couleurs par Chart.js/la carte) — pas de nouveaux tests `pytest` pertinents au-delà de la suite existante, qui ne doit pas régresser. Vérification par inspection manuelle dans un navigateur (Playwright), sur les deux thèmes, couvrant : bascule du bouton, persistance après rechargement de page, lisibilité de la page d'enregistrement et de la page de statistiques (y compris graphiques et carte), absence de flash au chargement, rendu correct des pages secondaires.
