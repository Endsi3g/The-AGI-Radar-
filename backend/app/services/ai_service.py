"""AI generation service — Ollama/Mistral for emails, SMS, call scripts, scoring, reply suggestions."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Literal

import ollama

from app.config import settings
from app.core.logging import logger


@dataclass
class EmailResult:
    subject: str
    body: str
    language: str


@dataclass
class SMSResult:
    body: str
    language: str


@dataclass
class CallScriptResult:
    intro: str
    value_prop: str
    objection_handlers: list[str]
    close: str
    language: str


@dataclass
class ScoreResult:
    score: int
    rationale: str


@dataclass
class ReplyResult:
    body: str
    subject: str
    language: str


_AGENCY_NAME = "HGI Digital"
_AGENCY_TAGLINE_FR = "agence numérique spécialisée en marketing local"
_AGENCY_TAGLINE_EN = "digital agency specialized in local marketing"


def _client() -> ollama.AsyncClient:
    return ollama.AsyncClient(host=settings.ollama_base_url)


def _model() -> str:
    return settings.ollama_model


def _extract_json(text: str) -> dict:
    """Extract the first JSON object from a model response."""
    # Strip markdown code fences
    text = re.sub(r"```(?:json)?", "", text).strip()
    # Find first {...}
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError(f"No JSON found in response: {text[:300]}")
    return json.loads(m.group(0))


def _business_context(lead: dict) -> str:
    """Build a compact business description from lead fields."""
    parts = []
    if lead.get("business_name"):
        parts.append(f"Entreprise: {lead['business_name']}")
    if lead.get("industry"):
        parts.append(f"Secteur: {lead['industry']}")
    if lead.get("city"):
        parts.append(f"Ville: {lead['city']}")
    if lead.get("google_rating"):
        parts.append(f"Note Google: {lead['google_rating']}/5 ({lead.get('google_reviews', '?')} avis)")
    if lead.get("website"):
        parts.append(f"Site web: {lead['website']}")
    else:
        parts.append("Site web: absent")
    if lead.get("owner_name"):
        parts.append(f"Propriétaire: {lead['owner_name']}")
    if lead.get("description"):
        parts.append(f"Description: {lead['description'][:200]}")
    return "\n".join(parts)


async def generate_email(lead: dict) -> EmailResult:
    """Generate a personalised cold email < 150 words."""
    lang = lead.get("detected_language", "fr")
    ctx = _business_context(lead)
    owner = lead.get("owner_name", "")
    first_name = owner.split()[0] if owner else ""

    if lang == "fr":
        greeting = f"Bonjour {first_name}," if first_name else "Bonjour,"
        prompt = f"""Tu es un conseiller commercial de {_AGENCY_NAME}, {_AGENCY_TAGLINE_FR}.
Génère un email de prospection froid en français pour cette entreprise:

{ctx}

Consignes:
- Commence par: {greeting}
- Moins de 150 mots
- Fais UNE observation spécifique et pertinente sur l'entreprise (note Google, absence de site, etc.)
- Propose notre service de façon naturelle
- CTA simple et unique à la fin (ex: "Disponible pour un appel de 15 min ?")
- Ton professionnel mais chaleureux, pas vendeur agressif
- Signature: [Prénom] | {_AGENCY_NAME}

Réponds UNIQUEMENT en JSON: {{"subject": "...", "body": "..."}}"""
    else:
        greeting = f"Hi {first_name}," if first_name else "Hi,"
        prompt = f"""You are a sales representative at {_AGENCY_NAME}, {_AGENCY_TAGLINE_EN}.
Write a cold outreach email in English for this business:

{ctx}

Guidelines:
- Start with: {greeting}
- Under 150 words
- Make ONE specific observation about this business (Google rating, missing website, etc.)
- Propose our service naturally
- Single simple CTA at the end (e.g., "Would you be open to a quick 15-min call?")
- Professional but warm tone, not pushy
- Sign off: [Name] | {_AGENCY_NAME}

Reply ONLY in JSON: {{"subject": "...", "body": "..."}}"""

    try:
        client = _client()
        response = await client.generate(
            model=_model(),
            prompt=prompt,
            options={"temperature": 0.7, "num_predict": 400},
        )
        data = _extract_json(response["response"])
        return EmailResult(
            subject=data.get("subject", f"Proposition pour {lead.get('business_name', '')}"),
            body=data.get("body", ""),
            language=lang,
        )
    except Exception as exc:
        logger.error("ai_email_generation_failed", error=str(exc), lead=lead.get("business_name"))
        raise


async def generate_sms(lead: dict) -> SMSResult:
    """Generate a punchy SMS < 160 characters."""
    lang = lead.get("detected_language", "fr")
    ctx = _business_context(lead)
    owner = lead.get("owner_name", "")
    first_name = owner.split()[0] if owner else ""

    if lang == "fr":
        prompt = f"""Tu es un conseiller de {_AGENCY_NAME}.
Génère un SMS de prospection en français pour:
{ctx}

Consignes:
- MAXIMUM 160 caractères
- {'Commence par le prénom: ' + first_name if first_name else 'Commence direct'}
- Observation spécifique + offre + CTA
- Inclus un numéro de rappel fictif: 514-555-0100

Réponds UNIQUEMENT en JSON: {{"body": "..."}}"""
    else:
        prompt = f"""You are a rep at {_AGENCY_NAME}.
Write a cold SMS in English for:
{ctx}

Guidelines:
- MAX 160 characters
- {'Start with first name: ' + first_name if first_name else 'Go straight to the point'}
- Specific observation + offer + CTA
- Include callback number: 514-555-0100

Reply ONLY in JSON: {{"body": "..."}}"""

    try:
        client = _client()
        response = await client.generate(
            model=_model(),
            prompt=prompt,
            options={"temperature": 0.7, "num_predict": 100},
        )
        data = _extract_json(response["response"])
        body = data.get("body", "")[:160]
        return SMSResult(body=body, language=lang)
    except Exception as exc:
        logger.error("ai_sms_generation_failed", error=str(exc))
        raise


async def generate_call_script(lead: dict) -> CallScriptResult:
    """Generate a structured call script with objection handlers."""
    lang = lead.get("detected_language", "fr")
    ctx = _business_context(lead)

    if lang == "fr":
        prompt = f"""Tu es un conseiller commercial expert de {_AGENCY_NAME}.
Génère un script d'appel téléphonique de prospection pour:
{ctx}

Structure requise:
1. intro: accroche courte de 2-3 phrases (qui tu es + raison d'appel)
2. value_prop: proposition de valeur en 2-3 phrases adaptée à cette entreprise
3. objection_handlers: EXACTEMENT 3 gestionnaires d'objections courantes (format: "Objection — Réponse")
4. close: demande de rendez-vous naturelle

Réponds UNIQUEMENT en JSON:
{{"intro": "...", "value_prop": "...", "objection_handlers": ["...", "...", "..."], "close": "..."}}"""
    else:
        prompt = f"""You are an expert sales rep at {_AGENCY_NAME}.
Generate a cold call script for:
{ctx}

Required structure:
1. intro: 2-3 sentence opener (who you are + reason for calling)
2. value_prop: 2-3 sentence value proposition tailored to this business
3. objection_handlers: EXACTLY 3 common objection handlers (format: "Objection — Response")
4. close: natural appointment ask

Reply ONLY in JSON:
{{"intro": "...", "value_prop": "...", "objection_handlers": ["...", "...", "..."], "close": "..."}}"""

    try:
        client = _client()
        response = await client.generate(
            model=_model(),
            prompt=prompt,
            options={"temperature": 0.65, "num_predict": 600},
        )
        data = _extract_json(response["response"])
        return CallScriptResult(
            intro=data.get("intro", ""),
            value_prop=data.get("value_prop", ""),
            objection_handlers=data.get("objection_handlers", [])[:3],
            close=data.get("close", ""),
            language=lang,
        )
    except Exception as exc:
        logger.error("ai_call_script_generation_failed", error=str(exc))
        raise


async def score_lead(lead: dict) -> ScoreResult:
    """Score a lead 0-100 with rationale."""
    ctx = _business_context(lead)

    prompt = f"""Tu es un analyste commercial pour une agence numérique.
Évalue ce lead sur une échelle de 0 à 100.

{ctx}

Critères de scoring (cumul):
+25 si site web absent ou très basique
+20 si bonne note Google (≥ 4.0) → audience fidèle mais besoin de visibilité
+15 si beaucoup d'avis Google (≥ 50) → business actif
+15 si secteur prioritaire (restaurant, café, hôtel, coiffeur, spa, gym)
+10 si propriétaire identifié (décideur direct)
+5 si présence Instagram/Facebook mais sans site
-15 si email absent (moins joignable)
-10 si note Google < 3.0 (problèmes de fond)
-5 si hors Québec

Score final = somme plafonnée entre 0 et 100.
Rédige une justification courte (2 phrases max).

Réponds UNIQUEMENT en JSON: {{"score": <entier 0-100>, "rationale": "..."}}"""

    try:
        client = _client()
        response = await client.generate(
            model=_model(),
            prompt=prompt,
            options={"temperature": 0.3, "num_predict": 150},
        )
        data = _extract_json(response["response"])
        score = max(0, min(100, int(data.get("score", 50))))
        return ScoreResult(score=score, rationale=data.get("rationale", ""))
    except Exception as exc:
        logger.error("ai_score_failed", error=str(exc))
        # Fallback heuristic score
        score = _heuristic_score(lead)
        return ScoreResult(score=score, rationale="Score calculé par heuristique (IA indisponible).")


def _heuristic_score(lead: dict) -> int:
    """Fast heuristic scoring without AI."""
    score = 40  # base
    if not lead.get("website"):
        score += 25
    rating = lead.get("google_rating") or 0
    if rating >= 4.0:
        score += 20
    elif rating < 3.0 and rating > 0:
        score -= 10
    reviews = lead.get("google_reviews") or 0
    if reviews >= 50:
        score += 15
    elif reviews >= 20:
        score += 8
    if lead.get("owner_name"):
        score += 10
    if not lead.get("email"):
        score -= 15
    if lead.get("instagram_handle") and not lead.get("website"):
        score += 5
    priority = {"restaurant", "café", "cafe", "hôtel", "hotel", "coiffeur", "spa", "gym"}
    if (lead.get("industry") or "").lower() in priority:
        score += 15
    return max(0, min(100, score))


async def suggest_reply(incoming_email: str, lead: dict) -> ReplyResult:
    """Suggest a reply to an inbound email."""
    lang = lead.get("detected_language", "fr")
    biz = lead.get("business_name", "le prospect")

    if lang == "fr":
        prompt = f"""Tu es un conseiller commercial de {_AGENCY_NAME}.
Un prospect ({biz}) a répondu à notre email de prospection.

Message reçu:
---
{incoming_email[:1000]}
---

Rédige une réponse courte (< 120 mots), professionnelle et chaleureuse qui:
- Confirme la réception et remercie
- Répond directement à ce qui a été dit/demandé
- Propose un créneau de RDV (lundi ou mardi prochain, 10h ou 14h)
- Signature: [Prénom] | {_AGENCY_NAME}

Réponds UNIQUEMENT en JSON: {{"subject": "Re: ...", "body": "..."}}"""
    else:
        prompt = f"""You are a sales rep at {_AGENCY_NAME}.
A prospect ({biz}) replied to our outreach email.

Received message:
---
{incoming_email[:1000]}
---

Write a short reply (< 120 words), professional and warm that:
- Acknowledges receipt and thanks them
- Directly addresses what was said/asked
- Proposes a meeting slot (next Monday or Tuesday, 10am or 2pm)
- Sign off: [Name] | {_AGENCY_NAME}

Reply ONLY in JSON: {{"subject": "Re: ...", "body": "..."}}"""

    try:
        client = _client()
        response = await client.generate(
            model=_model(),
            prompt=prompt,
            options={"temperature": 0.65, "num_predict": 300},
        )
        data = _extract_json(response["response"])
        return ReplyResult(
            subject=data.get("subject", "Re: Votre message"),
            body=data.get("body", ""),
            language=lang,
        )
    except Exception as exc:
        logger.error("ai_reply_suggestion_failed", error=str(exc))
        raise
