# Festival Count

Application Django d'enregistrement du département/pays d'origine des visiteurs d'un festival photo, avec statistiques et graphiques. Supporte plusieurs festivals indépendants (multi-tenant).

## Prérequis

- Python 3.14
- pip

## Installation

```bash
python -m venv .venv
.venv/Scripts/activate  # ou source .venv/bin/activate sous Linux/macOS
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

## Création d'un festival (première fois)

1. Lancer `python manage.py runserver` et se connecter sur `/admin/` avec le compte superuser.
2. Créer un `Festival` (nom + slug).
3. Créer une `Edition` pour ce festival (nom + dates du week-end du festival).
4. Créer un compte `User` pour le premier organisateur (ou utiliser le compte superuser).
5. Créer un `Membership` liant ce compte au festival avec le rôle « Organisateur ».
6. Se déconnecter de `/admin/`, se connecter sur `/login/` avec ce compte : vous êtes redirigé vers les statistiques du festival. Depuis là, la page « Bénévoles » (accessible depuis `/f/<slug>/benevoles/`) permet de créer les comptes bénévoles sans repasser par l'admin.

## Lancer l'application

```bash
python manage.py runserver
```

## Lancer les tests

```bash
pytest -v
```
