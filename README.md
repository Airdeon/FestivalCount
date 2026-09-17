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

## Créer un compte et un festival

1. Lancer `python manage.py runserver`, ouvrir `/inscription/` et créer un compte.
2. Depuis le tableau de bord, cliquer sur « Créer un festival » (le slug est généré automatiquement à partir du nom) : vous devenez Organisateur de ce festival.
3. Depuis la page « Éditions » du festival, créer une édition (nom + dates du week-end du festival).
4. Les bénévoles créent eux-mêmes un compte via `/inscription/`, puis « Rejoindre un festival » pour envoyer une demande — à valider depuis la page « Bénévoles » du festival. Un organisateur peut aussi créer directement un compte bénévole depuis cette même page.

Le compte superuser Django (`createsuperuser` + `/admin/`) reste utile pour l'administration technique (suppression de données, etc.) mais n'est plus nécessaire pour créer le premier festival.

## Lancer l'application

```bash
python manage.py runserver
```

## Lancer les tests

```bash
pytest -v
```
