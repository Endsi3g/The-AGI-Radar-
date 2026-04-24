# CLAUDE.md — Guide pour Claude Code

Ce fichier guide les sessions Claude Code sur ce projet. Lis-le en entier avant de toucher au code.

---

## Contexte du projet

**HGI Radar** est un système de prospection B2B complet pour une agence numérique québécoise (2–5 utilisateurs). Il automatise : scraping de leads → enrichissement IA → messages personnalisés → approbation humaine → envoi → suivi CRM → Google Calendar/Gmail.

- **Langue de l'interface** : Français (FR) par défaut, bilingue FR/EN
- **Marché cible** : Canada (Québec) — restaurants et services locaux
- **IA** : Ollama + Mistral 7B local (pas d'API payante pour l'IA)
- **Branche de développement active** : `claude/hgi-prospecting-system-NaGOH`

---

## Stack & Structure

```
backend/          → Python 3.12 + FastAPI (async SQLAlchemy, Alembic, Celery)
frontend/         → Next.js 14 App Router + Tailwind + shadcn/ui
workers/          → Image Docker pour Celery (même code que backend/)
nginx/            → Reverse proxy production
scripts/          → seed_db.py, backup_db.sh
docker-compose.yml
```

### Backend (`backend/app/`)

| Dossier | Contenu |
|---|---|
| `models/` | SQLAlchemy ORM — 8 tables (users, leads, lead_sources, scrape_jobs, campaigns, messages, interactions, calendar_events) |
| `schemas/` | Pydantic v2 — validation request/response |
| `api/v1/` | Routers FastAPI — auth, leads, messages, scrape, users, (+ stubs: ai, campaigns, google, comms, map) |
| `services/` | Logique métier — à créer au fil des phases |
| `scrapers/` | Scrapers par source + utils (browser, anti_bot, normalizer) |
| `tasks/` | Tâches Celery — scrape_tasks, ai_tasks, email_tasks, sms_tasks, reminder_tasks |
| `core/` | security.py (JWT/bcrypt), exceptions.py, logging.py |

### Frontend (`frontend/src/`)

| Dossier | Contenu |
|---|---|
| `app/(auth)/` | Page login |
| `app/(dashboard)/` | Toutes les pages avec sidebar (dashboard, leads, scrape, map, campaigns, messages, voip, settings) |
| `components/layout/` | Sidebar.tsx, TopBar.tsx |
| `components/providers/` | QueryProvider.tsx (@tanstack/react-query) |
| `lib/api.ts` | Client axios avec auto-refresh JWT |
| `lib/auth.ts` | Zustand store (persist localStorage) |
| `i18n/request.ts` | Configuration next-intl |
| `public/locales/fr/` | Traductions françaises |
| `public/locales/en/` | Traductions anglaises |

---

## Commandes essentielles

```bash
# Démarrer tous les services
docker compose up -d

# Appliquer les migrations
docker compose exec backend alembic upgrade head

# Seed (admin + leads d'exemple)
docker compose exec backend python /scripts/seed_db.py

# Logs backend
docker compose logs -f backend

# Logs worker Celery
docker compose logs -f worker

# Accéder au shell backend
docker compose exec backend bash

# Générer une nouvelle migration Alembic
docker compose exec backend alembic revision --autogenerate -m "description"
```

---

## Conventions de code

### Backend (Python)

- **Style** : pas de commentaires inutiles, nommage explicite
- **Async partout** : toutes les routes FastAPI et les accès DB sont `async`
- **SQLAlchemy** : utiliser `mapped_column` + `Mapped[...]` (style moderne SQLAlchemy 2.0)
- **Pydantic** : toujours `model_config = {"from_attributes": True}` sur les schémas de réponse
- **Dépendances** : utiliser `Depends()` de FastAPI — `get_db`, `get_current_user`, `require_role`
- **Erreurs** : utiliser les classes de `app/core/exceptions.py` (NotFoundError, ForbiddenError, etc.)
- **Logging** : utiliser `from app.core.logging import logger` (structlog)
- **UUID** : tous les IDs sont des UUID v4 (`uuid.UUID`, `UUID(as_uuid=True)` en PostgreSQL)

### Frontend (TypeScript / Next.js)

- **App Router** : toutes les pages dans `src/app/`
- **"use client"** : seulement sur les composants avec état, hooks, événements
- **Auth** : utiliser `useAuthStore` de `lib/auth.ts` — jamais de localStorage direct
- **API calls** : toujours via `apiClient` de `lib/api.ts` — jamais via `fetch` directement
- **Styling** : Tailwind CSS + `cn()` de `lib/utils.ts` pour les classes conditionnelles
- **i18n** : utiliser `useTranslations` de `next-intl` pour tous les textes visibles

### Git

- **Branche active** : `claude/hgi-prospecting-system-NaGOH`
- **Messages de commit** : en français, préfixés par la phase (`Phase 1: ...`, `Phase 2: ...`)
- **Jamais** de push sur `main` directement

---

## Schéma de base de données

### Tables principales

**`users`** — `id`, `email`, `full_name`, `hashed_pw`, `role` (admin|sales|viewer), `google_access_token`, `google_refresh_token`, `google_token_expiry`

**`leads`** — `id`, `business_name`, `industry`, `phone`, `email`, `website`, `city`, `latitude`, `longitude`, `google_place_id`, `google_rating`, `google_reviews`, `owner_name`, `detected_language`, `status`, `ai_score`, `source_flags` (JSONB), `assigned_to`

**`messages`** — `id`, `lead_id`, `channel` (email|sms|voip_script), `direction` (outbound|inbound), `status` (draft→pending_approval→approved→sent), `body`, `gmail_thread_id`, `twilio_sid`, `ai_reply_suggestion`

**`interactions`** — log immuable de tout : email_sent, sms_sent, call_made, status_changed, note_added, score_updated

**`scrape_jobs`** — `id`, `sources[]`, `query_term`, `status` (pending|running|done|failed), `celery_task_id`, `leads_found`, `leads_new`, `leads_merged`

### Statuts du pipeline leads
`nouveau` → `contacté` → `réponse` → `rdv` → `fermé` | `perdu`

---

## Flux d'approbation des messages

```
POST /ai/generate-email  →  message créé (status: pending_approval)
                         →  visible dans l'inbox d'approbation
POST /messages/{id}/approve  →  status: approved
                             →  Celery task: send_email_message
                             →  Gmail API envoie l'email
                             →  status: sent, gmail_message_id renseigné
                             →  Interaction "email_sent" loggée
```

---

## Intégrations à configurer

### Google OAuth 2.0
- Créer un projet sur [Google Cloud Console](https://console.cloud.google.com)
- Activer les APIs : Gmail API, Google Calendar API
- Créer des identifiants OAuth 2.0 (application web)
- URI de redirection autorisée : `http://localhost:8000/api/v1/google/callback`
- Scopes : `gmail.send`, `gmail.readonly`, `calendar`, `userinfo.email`
- Renseigner `GOOGLE_CLIENT_ID` et `GOOGLE_CLIENT_SECRET` dans `.env`

### Twilio
- Créer un compte sur [twilio.com](https://twilio.com)
- Obtenir un numéro canadien (+1 514 ou +1 438)
- Renseigner `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` dans `.env`
- Configurer les webhooks dans la console Twilio :
  - SMS entrant → `https://tondomaine.com/api/v1/comms/sms/webhook`
  - Statut appel → `https://tondomaine.com/api/v1/comms/voice/webhook`

### LinkedIn (scraping)
- Dans ton navigateur, se connecter à LinkedIn
- Ouvrir DevTools → Application → Cookies → `li_at`
- Copier la valeur dans `LINKEDIN_LI_AT_COOKIE` dans `.env`
- Le cookie expire environ tous les 6 mois → renouveler manuellement

---

## Phases d'implémentation

| Phase | Statut | Description |
|---|---|---|
| **0** | ✅ Complété | Infrastructure (FastAPI, Next.js, PostgreSQL, Docker, Auth JWT) |
| **1** | ✅ Complété | CRM & Leads (Kanban, fiche lead, déduplication, scoring affichage) |
| **2** | ✅ Complété | Scraping engine (6 sources, Playwright stealth, Celery, WebSocket) |
| **3** | ✅ Complété | IA Ollama/Mistral (génération email/SMS/script, scoring, détection langue) |
| **4** | 🔄 En cours | Outreach (Gmail API, Twilio SMS/VoIP, téléprompter, PDF scripts) |
| **5** | ⏳ | Google OAuth + Gmail inbox + Calendar auto |
| **6** | ⏳ | Carte Leaflet (heatmap, draw zone, itinéraire OSRM) |
| **7** | ⏳ | Équipe, notifications WS, KPI dashboard, prod Docker |

---

## Points d'attention critiques

### Scraping
- **Ne jamais** lancer le scraping sans playwright-stealth activé — risque de ban IP
- Google Maps est le plus protégé — utiliser la stratégie JSON-LD (parse HTML) en priorité
- Délais aléatoires obligatoires entre chaque action Playwright (1.5–4 secondes)
- Le cookie LinkedIn `li_at` doit être injecté dans chaque contexte browser

### Ollama / Mistral
- Le modèle tourne localement sur CPU/GPU — génération ~15 tokens/sec sur CPU
- Pour 50 leads, la génération d'emails prend ~10 min → toujours en tâche Celery background
- Utiliser les prompts structurés dans `services/ai_service.py` — ne pas improviser des prompts inline
- Les réponses JSON de Mistral doivent être parsées avec `json.loads()` + try/except

### Déduplication
- Ordre de priorité : `google_place_id` (définitif) → téléphone normalisé → domaine website → fuzzy name×city (rapidfuzz WRatio > 85)
- Normaliser le téléphone canadien : supprimer `+1`, espaces, tirets, parenthèses → 10 chiffres

### Google OAuth tokens
- Toujours vérifier `google_token_expiry < now() + 5min` avant chaque appel API Google
- Si expiré → appeler le refresh endpoint et mettre à jour la DB
- Les tokens sont stockés chiffrés dans `users` (colonne `google_access_token`)

### Frontend
- **Leaflet.js ne fonctionne pas en SSR** — toujours utiliser `dynamic(() => import(...), { ssr: false })`
- La sidebar est en `(dashboard)/layout.tsx` — ne pas dupliquer la logique de navigation
- Les pages dans `(dashboard)/` héritent automatiquement du layout avec sidebar

---

## Fichiers à ne jamais modifier sans raison

- `backend/alembic/versions/001_initial_schema.py` — migration initiale, ne pas modifier. Créer une nouvelle migration à la place
- `backend/app/database.py` — engine SQLAlchemy, pool configuré pour la production
- `backend/app/core/security.py` — fonctions JWT et bcrypt critiques
- `docker-compose.yml` — dépendances entre services bien configurées avec healthchecks

---

## Seed de développement

Après `python /scripts/seed_db.py` :

| Email | Mot de passe | Rôle |
|---|---|---|
| admin@hgiradar.com | hgi2026! | admin |

3 leads d'exemple dans Montréal/Laval (restaurant, plombier, café).
