"""Regras puras e testáveis para cenários sintéticos de CRM e suporte."""
from __future__ import annotations

import re

def phone_e164(raw: str) -> str | None:
    digits = re.sub(r"\D", "", str(raw))
    if digits.startswith("55") and len(digits) in (12, 13):
        digits = digits[2:]
    if len(digits) not in (10, 11):
        return None
    ddd = int(digits[:2])
    if not (11 <= ddd <= 99):
        return None
    if len(digits) == 11 and digits[2] != "9":
        return None
    if len(digits) == 10 and digits[2] not in "2345":
        return None
    return "55" + digits

def retry_delay(attempt: int, base_seconds: int = 5, cap_seconds: int = 1800) -> int:
    if attempt < 1 or base_seconds < 1 or cap_seconds < 1:
        raise ValueError("Parâmetros positivos obrigatórios")
    return min(base_seconds * 2 ** (attempt - 1), cap_seconds)

def sla_status(elapsed_minutes: int, limit_minutes: int, warning_minutes: int = 30) -> str:
    if elapsed_minutes < 0 or limit_minutes <= 0 or warning_minutes < 0:
        raise ValueError("SLA inválido")
    remaining = limit_minutes - elapsed_minutes
    if remaining <= 0:
        return "overdue"
    if remaining <= warning_minutes:
        return "warning"
    return "healthy"

def message_mode(minutes_since_contact: int, window_minutes: int = 1440) -> str:
    if minutes_since_contact < 0 or window_minutes < 1:
        raise ValueError("Janela inválida")
    return "session" if minutes_since_contact <= window_minutes else "template"

def lead_completeness_score(name: bool, phone: bool, email: bool, source: bool, engagement_points: int = 0) -> int:
    if engagement_points < 0:
        raise ValueError("Pontuação de engajamento inválida")
    return 20 * bool(name) + 40 * bool(phone) + 30 * bool(email) + 10 * bool(source) + engagement_points

def evaluate(category: str, payload: dict):
    if category == "phone":
        return phone_e164(payload["raw"])
    if category == "retry":
        return retry_delay(payload["attempt"], payload["base_seconds"], payload["cap_seconds"])
    if category == "sla":
        return sla_status(payload["elapsed_minutes"], payload["limit_minutes"], payload["warning_minutes"])
    if category == "message":
        return message_mode(payload["minutes_since_contact"], payload["window_minutes"])
    if category == "lead_score":
        return lead_completeness_score(**payload)
    raise ValueError(f"Categoria desconhecida: {category}")
