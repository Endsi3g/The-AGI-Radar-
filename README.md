# AGI Radar — Système de Prospection Intelligent

Plateforme de prospection B2B complète pour agences numériques québécoises. Le système automatise l'intégralité du cycle de prospection : scraping gratuit de leads → enrichissement IA → messages ultra-personnalisés → envoi avec approbation humaine → suivi CRM → intégrations Google.

---

## Fonctionnalités

### Génération de leads (scraping 100% gratuit)
- **Google Maps / Places** — entreprises locales avec adresse, téléphone, site, avis Google
- **Pages Jaunes Canada** — annuaire avec coordonnées complètes
- **Yelp** — restaurants, services locaux, avis
- **LinkedIn** — profils d'entreprises et décideurs
- **Instagram / Facebook** — pages business publiques

### CRM & Pipeline
- Pipeline Kanban drag-and-drop : Nouveau → Contacté → Réponse → RDV → Fermé | Perdu
- Fiche lead complète avec timeline d'interactions
- Score IA automatique 0–100 avec justification (Ollama/Mistral)
- Déduplication intelligente multi-sources (rapidfuzz)
- Relances automatiques et rappels (Celery Beat)

### Outreach ultra-personnalisé (IA locale — 0 $ d'API)
- **Emails** : < 150 mots, observe le business spécifiquement, CTA simple
- **SMS** : < 160 caractères, percutant, prénom du propriétaire si disponible
- **Scripts d'appel** : intro + proposition de valeur + 3 objections + close
- Détection automatique de la langue (FR/EN) du prospect
- Suggestion de réponse aux emails reçus par l'IA

### Flux d'approbation (semi-automatique)
- L'IA génère tout → dashboard d'approbation côte-à-côte (draft / éditeur)
- Approuver → envoi via Gmail API ou Twilio
- Aucun envoi automatique sans validation humaine

### Intégrations Google
- **Gmail** : envoi depuis ton compte, lecture des réponses, suggestions IA de réponse
- **Google Calendar** : création automatique de RDV, rappels de suivi

### VoIP & Scripts d'appel
- Téléprompter en direct (mode plein écran, avancement au clavier)
- Appels VoIP depuis l'app (Twilio Voice)
- Transcript automatique des appels (Whisper local)
- Export PDF du script

### Carte interactive
- Marqueurs colorés par statut sur OpenStreetMap (gratuit)
- Heatmap de densité de prospects
- Dessiner une zone → scraper uniquement cette région
- Planification d'itinéraire de visite (OSRM)

---

## Stack technique

| Composant | Technologie |
|---|---|
| Backend | Python 3.12 + FastAPI (async) |
| Frontend | Next.js 14 (App Router) + Tailwind CSS + shadcn/ui |
| Base de données | PostgreSQL 16 |
| Intelligence artificielle | Ollama + Mistral 7B (100% local, gratuit) |
| Tâches background | Celery + Redis |
| SMS / VoIP | Twilio |
| Carte | Leaflet.js + OpenStreetMap |
| Auth | JWT (access + refresh tokens) |
| Scraping | Playwright + playwright-stealth |
| Déploiement | Docker Compose |

---

## Démarrage rapide

### Prérequis
- Docker + Docker Compose
- 8 GB RAM minimum (16 GB recommandé pour Ollama/Mistral)
- Git

### Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/Endsi3g/The-AGI-Radar-.git
cd The-AGI-Radar-

# 2. Configurer l'environnement
cp .env.example .env
```

Remplir dans `.env` :

```bash
JWT_SECRET=une-clé-secrète-minimum-32-caractères
GOOGLE_CLIENT_ID=...       # Google Cloud Console
GOOGLE_CLIENT_SECRET=...
TWILIO_ACCOUNT_SID=...     # twilio.com
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+15145550000
```

```bash
# 3. Démarrer tous les services (postgres, redis, ollama, backend, worker, beat, flower, frontend)
docker compose up -d

# 4. Créer les tables (migration Alembic)
docker compose exec backend alembic upgrade head

# 5. Créer l'admin et 3 leads d'exemple
docker compose exec backend python /scripts/seed_db.py
```

### Accès

| Service | URL | Credentials |
|---|---|---|
| Application | http://localhost:3000 | admin@hgiradar.com / hgi2026! |
| API (docs) | http://localhost:8000/docs | — |
| Health check | http://localhost:8000/api/v1/health | — |
| Flower (workers) | http://localhost:5555 | — |

> **Note** : Ollama télécharge Mistral 7B (~4 GB) au premier démarrage. Le service sera prêt après environ 5 minutes.

---

## Architecture

```
The-AGI-Radar-/
├── backend/                    # FastAPI (Python 3.12)
│   ├── app/
│   │   ├── main.py             # Factory FastAPI, CORS, lifespan
│   │   ├── config.py           # pydantic-settings (.env)
│   │   ├── database.py         # SQLAlchemy async engine
│   │   ├── dependencies.py     # get_current_user, require_role
│   │   ├── models/             # 8 modèles SQLAlchemy ORM
│   │   ├── schemas/            # Pydantic v2 (request/response)
│   │   ├── api/v1/             # Routers REST + WebSocket
│   │   ├── services/           # Logique métier (AI, Gmail, Twilio…)
│   │   ├── scrapers/           # Scrapers par source + utils anti-bot
│   │   ├── tasks/              # Tâches Celery (scrape, ai, email, sms)
│   │   └── core/               # Sécurité, exceptions, logging
│   └── alembic/                # Migrations de base de données
│
├── frontend/                   # Next.js 14 (App Router)
│   └── src/
│       ├── app/                # Pages (dashboard, leads, kanban, map…)
│       ├── components/         # Composants React réutilisables
│       ├── lib/                # API client, auth store, utils
│       └── i18n/               # Traductions FR/EN
│
├── workers/                    # Image Docker Celery (même code que backend)
├── nginx/                      # Config reverse proxy (production)
├── scripts/                    # seed_db.py, backup_db.sh
├── docker-compose.yml          # Dev local (8 services)
└── docker-compose.prod.yml     # Overrides production
```

### Schéma de base de données

```
users ──< leads ──< messages ──< interactions
              ├──< lead_sources
              ├──< calendar_events
              └──< (via campaign) campaigns ──< messages

scrape_jobs ──< lead_sources
```

---

## API

Documentation interactive disponible sur http://localhost:8000/docs

### Endpoints principaux

```
POST   /api/v1/auth/login              # Connexion JWT
GET    /api/v1/leads                   # Liste des leads (filtres: status, city, industry, score)
POST   /api/v1/leads                   # Créer un lead manuellement
PATCH  /api/v1/leads/{id}              # Modifier statut, assignation, relance
POST   /api/v1/scrape/jobs             # Lancer un scraping
WS     /api/v1/scrape/jobs/{id}/stream # Progression temps réel
POST   /api/v1/ai/generate-email       # Générer un email personnalisé
POST   /api/v1/ai/generate-sms         # Générer un SMS
POST   /api/v1/ai/generate-call-script # Générer un script d'appel
POST   /api/v1/messages/{id}/approve   # Approuver et envoyer
GET    /api/v1/map/leads               # GeoJSON pour la carte
GET    /api/v1/health                  # Statut de tous les services
```

---

## Rôles utilisateurs

| Rôle | Accès |
|---|---|
| `admin` | Tout (création d'utilisateurs, suppression, configuration) |
| `sales` | Leads assignés, génération et approbation de messages |
| `viewer` | Lecture seule (pas de suppression, pas d'envoi) |

---

## Déploiement en production

```bash
# Variables d'environnement
APP_ENV=production

# Démarrer avec les overrides prod (Nginx + SSL + 4 workers uvicorn)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# SSL — Certbot (Let's Encrypt)
docker compose exec nginx certbot --nginx -d tondomaine.com
```

Modifier `nginx/nginx.conf` avec ton domaine avant de démarrer.

---

## Phases d'implémentation

| Phase | Contenu | Statut |
|---|---|---|
| **0** | Infrastructure (FastAPI, Next.js, PostgreSQL, Docker) | ✅ Complété |
| **1** | CRM & Leads (Kanban, fiche complète, déduplication) | ✅ Complété |
| **2** | Moteur de scraping (6 sources, anti-bot, Celery) | ✅ Complété |
| **3** | IA Ollama/Mistral (emails, SMS, scripts, scoring) | ✅ Complété |
| **4** | Outreach (Gmail API, Twilio SMS/VoIP, téléprompter) | ✅ Complété |
| **5** | Google OAuth + Gmail inbox + Calendar | ✅ Complété |
| **6** | Carte Leaflet (heatmap, draw zone, itinéraire) | 🔄 En cours |
| **7** | Équipe, notifications, KPI dashboard, prod | ⏳ Planifié |

---

## Changelog

### v0.5.0 — Phase 5 : Google OAuth + Gmail Inbox + Calendar Auto
- `api/v1/google.py` : flux OAuth 2.0 complet — `GET /google/auth-url` (state signé JWT), `GET /google/callback` (échange code → tokens + google_email), `DELETE /google/disconnect`, `GET /google/status`
- `api/v1/google.py` : `GET /google/calendar/events` (liste), `POST /google/calendar/events` (création manuelle), `DELETE /google/calendar/events/{id}`
- `services/calendar_service.py` : `create_rdv_event` avec Google Meet + rappels email/popup, `create_followup_event`, `delete_event`, `list_upcoming_events`
- `api/v1/leads.py` : hook automatique — statut lead → `rdv` crée un événement Google Calendar si compte connecté
- `app/(dashboard)/settings/integrations/page.tsx` : UI connect/disconnect Google, statut, liste des 5 prochains événements Calendar avec lien Meet
- `app/(dashboard)/settings/page.tsx` : hub de navigation vers les sous-pages paramètres
- `app/(dashboard)/messages/inbox/page.tsx` : boîte de réception emails entrants, expansion corps complet, suggestion IA de réponse avec bouton "Utiliser cette réponse"
- `components/layout/Sidebar.tsx` : ajout lien "Boîte de réception" sous Messages

### v0.4.0 — Phase 4 : Outreach (Gmail API + Twilio SMS/VoIP)
- `services/gmail_service.py` : envoi MIME multipart (text+HTML), polling inbox, refresh token auto (< 5 min avant expiry)
- `services/twilio_service.py` : send_sms, initiate_call (enregistrement auto), parse webhooks entrants
- `tasks/email_tasks.py` : `send_email_message` (retry x3) + `poll_gmail_inbox` (Celery Beat 15 min) — détecte réponses, génère suggestion IA, stocke inbound, mark as read
- `tasks/sms_tasks.py` : `send_sms_message` (retry x3), normalisation E.164 automatique
- `tasks/reminder_tasks.py` : `check_followup_reminders` (Beat toutes les heures), crée interaction et remet `next_followup_at` à None
- `api/v1/comms.py` : webhooks SMS/Voice entrants Twilio, initiation appel, TwiML, recording callback
- `Teleprompter.tsx` : mode plein écran, navigation clavier (→ / Espace / ←), dots de progression, parseur `=== sections ===`
- `Dialer.tsx` : bouton Twilio, timer live, mute, états idle/calling/connected/ended
- `voip/page.tsx` : liste leads searchable, composeur + script côte à côte, bascule téléprompter

### v0.3.0 — Phase 3 : IA Ollama/Mistral
- `services/ai_service.py` : génération email (<150 mots), SMS (<160 chars), script d'appel (intro+valeur+3 objections+close), score 0-100, suggestion réponse inbound
- `services/language_service.py` : détection automatique FR/EN (langdetect + heuristique)
- `services/scoring_service.py` : scoring heuristique rapide + chemin IA async, persisté en DB
- `api/v1/ai.py` : `/ai/generate-email|sms|script`, `/ai/leads/{id}/score`, `/ai/batch-score`, `/ai/batch-generate`
- Inbox d'approbation complète : édition inline, approbation 1-clic, rejet avec raison
- Panneau IA sur chaque fiche lead (3 canaux + bouton scorer)
- Génération et scoring en masse via Celery (50 leads ≈ 10 min)

### v0.2.0 — Phase 2 : Moteur de scraping
- 6 scrapers : Google Maps (JSON-LD), Pages Jaunes CA, Yelp, LinkedIn, Instagram (instagrapi), Facebook
- Anti-bot 3 couches : playwright-stealth, délais aléatoires 1.5–4s, scroll/mouse humain
- Déduplication : google_place_id → téléphone normalisé → domaine → fuzzy name×city (rapidfuzz WRatio > 85)
- Progression en temps réel par lead via Redis pub/sub + WebSocket
- Frontend : formulaire de lancement, journal terminal live, historique des jobs

### v0.1.0 — Phase 1 : CRM & Leads
- Liste leads avec filtres (statut, secteur, recherche texte)
- Vue Kanban drag-and-drop avec changement de statut
- Fiche lead complète (contact, décideur, timeline d'interactions, relances)
- Dashboard avec KPIs, mini pipeline, leads récents

### v0.0.1 — Phase 0 : Infrastructure
- Backend FastAPI async + 8 modèles SQLAlchemy + migration Alembic
- Auth JWT (access + refresh), rôles admin/sales/viewer
- Docker Compose 8 services (postgres, redis, ollama, backend, worker, beat, flower, frontend)

---

## Variables d'environnement

| Variable | Description | Requis |
|---|---|---|
| `JWT_SECRET` | Clé secrète JWT (min 32 caractères) | ✅ |
| `GOOGLE_CLIENT_ID` | ID client Google Cloud | Pour Gmail/Calendar |
| `GOOGLE_CLIENT_SECRET` | Secret Google Cloud | Pour Gmail/Calendar |
| `TWILIO_ACCOUNT_SID` | SID Twilio | Pour SMS/VoIP |
| `TWILIO_AUTH_TOKEN` | Token Twilio | Pour SMS/VoIP |
| `TWILIO_FROM_NUMBER` | Numéro Twilio (format E.164) | Pour SMS/VoIP |
| `LINKEDIN_LI_AT_COOKIE` | Cookie `li_at` LinkedIn | Pour scraping LinkedIn |
| `INSTAGRAM_USERNAME` | Compte Instagram (business) | Pour scraping Instagram |
| `INSTAGRAM_PASSWORD` | Mot de passe Instagram | Pour scraping Instagram |
| `OLLAMA_MODEL` | Modèle Ollama (défaut: `mistral`) | Optionnel |
| `SCRAPER_PROXY_URL` | URL proxy SOCKS5 pour le scraping | Optionnel |

---

## Contribution

Ce projet est développé pour usage interne d'agence. Pour signaler un problème ou suggérer une amélioration, ouvre une issue sur GitHub.

---

*Développé avec Claude Code — Anthropic*
