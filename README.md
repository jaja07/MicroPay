# MicroPay Backend - Guide de Configuration et Lancement

Guide complet pour configurer et lancer l'application MicroPay en local ou avec Docker.

## Table des matières

1. [Prérequis](#prérequis)
2. [Installation](#installation)
3. [Configuration de l'environnement](#configuration-de-lenvironnement)
4. [Lancement en développement local](#lancement-en-développement-local)
5. [Lancement avec Docker](#lancement-avec-docker)
6. [Migrations de base de données](#migrations-de-base-de-données)
7. [Structure du projet](#structure-du-projet)
8. [Commandes utiles](#commandes-utiles)

---

## Prérequis

### Pour le développement local
- **Python 3.11+** (testé avec 3.11)
- **Conda** ou **venv**
- **PostgreSQL 15+** (ou via Docker)
- **Git**

### Pour Docker
- **Docker Desktop** ou Docker
- **Docker Compose**

---

## Installation

### 1. Cloner le repository

```bash
git clone <repo-url>
cd MicroPay
```

### 2. Créer et activer l'environnement Python

#### Avec Conda
```bash
conda create -n micropay python=3.11
conda activate micropay
```

#### Avec venv (Windows)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### Avec venv (Linux/Mac)
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
cd backend
pip install -r requirements.txt
```

---

## Configuration de l'environnement

### 1. Créer le fichier `.env`

Depuis le dossier `backend`, crée ton `.env` à partir du modèle :

```powershell
Copy-Item .env.example .env
```

Puis renseigne les valeurs sensibles dans `.env` (Circle, JWT, SMTP). Variables requises :

```env
# Database
DB_HOST=localhost
DB_PORT=5434
DB_NAME=payment_db
DB_USER=admin
DB_PASSWORD=adminpassword

# Circle API
CIRCLE_API_KEY=your_circle_api_key
WALLET_SET_ID=your_wallet_set_id
HEX_ENCODED_ENTITY_SECRET=your_hex_encoded_entity_secret
CIRCLE_MASTER_WALLET_ID=your_master_wallet_id
CIRCLE_USDC_TOKEN_ID=your_usdc_token_id
CIRCLE_GAS_TOKEN_SYMBOL=USDC-TESTNET
CIRCLE_MIN_GAS_THRESHOLD=1.0

# JWT
SECRET_KEY=replace_with_a_long_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Email / SMTP
MAIL_HOST=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email_username
MAIL_PASSWORD=your_email_password_or_app_password
FROM_MAIL=no-reply@micropay.local
```

### 2. Lancer PostgreSQL (avec Docker)

Avant de lancer l'app en local, démarrez juste la base de données :

```bash
# Depuis la racine du projet
docker-compose up db -d
```

Attends quelques secondes que la BD soit prête (healthcheck).

---

## Lancement en développement local

### 1. Appliquer les migrations

```bash
cd backend
alembic upgrade head
```

### 2. Lancer le serveur FastAPI

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

L'application sera accessible à : **http://127.0.0.1:8000**

Documentation interactive (Swagger) : **http://127.0.0.1:8000/docs**

---

## Lancement avec Docker

### 1. Arrêter les services existants

```bash
docker-compose down
```

### 2. Démarrer tous les services

```bash
# Depuis la racine du projet
docker-compose up -d
```

Cela lancera :
- 🐘 PostgreSQL sur le port `5434`
- 🚀 FastAPI sur le port `8000`

### 3. Vérifier l'état des services

```bash
docker-compose ps
```

### 4. Voir les logs

```bash
# Tous les logs
docker-compose logs -f

# Logs du backend uniquement
docker-compose logs -f backend

# Logs de PostgreSQL uniquement
docker-compose logs -f db
```

### 5. Arrêter les services

```bash
docker-compose down
```

---

## Migrations de base de données

### Créer une nouvelle migration

```bash
alembic revision --autogenerate -m "Description de la migration"
```

### Appliquer les migrations

```bash
# Appliquer toutes les migrations
alembic upgrade head

# Appliquer jusqu'à une version spécifique
alembic upgrade <revision_id>
```

### Revenir à une version précédente

```bash
# Revenir d'une migration
alembic downgrade -1

# Revenir à une version spécifique
alembic downgrade <revision_id>
```

### Voir l'historique des migrations

```bash
alembic history
```

---

## Structure du projet

```
backend/
├── main.py                 # Point d'entrée FastAPI
├── requirements.txt        # Dépendances Python
├── .env                    # Variables d'environnement
├── alembic.ini            # Configuration Alembic
├── Dockerfile             # Configuration Docker
├── docker-compose.yml     # Orchestration des conteneurs (à la racine)
├── start.sh              # Script de démarrage pour Docker
│
├── models/               # Entités SQLModel
│   ├── user_entity.py
│   ├── wallet_entity.py
│   └── recharge_entity.py
│
├── schema/              # DTOs Pydantic
│   ├── user.py
│   └── recharges.py
│
├── db/                  # Configuration de base de données
│   ├── session.py       # SessionLocal et engine
│   └── init.sql        # Script d'initialisation SQL
│
├── repositories/       # Couche d'accès aux données
│   ├── user_repository.py
│   └── recharges_repository.py
│
├── services/           # Logique métier
│   └── user_service.py
│
├── routers/            # Routes API
│   └── user.py
│
└── migrations/         # Migrations Alembic
    ├── env.py
    ├── script.py.mako
    └── versions/       # Fichiers de migration générés
```

---

## Commandes utiles

### Base de données

```bash
# Afficher l'état de la BD via psql
docker exec -it micropay-postgres psql -U admin -d payment_db

# Exécuter une requête SQL
docker exec -it micropay-postgres psql -U admin -d payment_db -c "SELECT * FROM users;"
```

### Docker

```bash
# Reconstruire les images
docker-compose build

# Redémarrer les services
docker-compose restart

# Supprimer tout (images, conteneurs, volumes)
docker-compose down -v
```

### FastAPI

```bash
# Lancer avec auto-reload en dev
uvicorn main:app --reload

# Lancer en production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Python/Pip

```bash
# Installer une nouvelle dépendance
pip install <package-name>

# Mettre à jour requirements.txt
pip freeze > requirements.txt

# Vérifier les versions des packages
pip show <package-name>
```

---

## Troubleshooting

### Erreur : `could not translate host name "db" to address`

**Cause** : Tu lances Alembic en local mais `.env` utilise `db` (nom du service Docker).

**Solution** : Assure-toi que `.env` a `DB_HOST=localhost` pour le développement local.

### Erreur : `failed to create task for container`

**Cause** : Le `Dockerfile` ou `docker-compose.yml` est mal configuré.

**Solution** : Vérifiez que `context: .` pointe vers le bon répertoire.

### Erreur : `Connection refused on port 5434`

**Cause** : PostgreSQL n'est pas en cours d'exécution.

**Solution** : 
```bash
docker-compose up db -d
# Attendre 10-15 secondes que la BD soit prête
```

### Erreur : `InvalidRequestError` avec Alembic

**Cause** : Dépendances circulaires entre les modèles.

**Solution** : Assurez-vous que `from __future__ import annotations` est au début de chaque fichier de modèle.

---

## Documentation supplémentaire

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)

---

## Support

En cas de problème, vérifiez :
1. ✅ Les prérequis sont installés
2. ✅ Les variables d'environnement sont correctes
3. ✅ PostgreSQL est en cours d'exécution
4. ✅ Les migrations sont appliquées (`alembic upgrade head`)
5. ✅ Les logs (`docker-compose logs -f`)
