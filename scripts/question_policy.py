"""Politica pura y comprobable para autorizar respuestas pre-venta."""
import json
import re
import unicodedata

AUTH_QUESTION_TERMS = (
    "original", "autentic", "oficial", "clon", "replica", "imitacion",
    "pirata", "falso", "falsa", "copia", "de la marca",
)
APP_QUESTION_TERMS = (
    " app", "app ", "aplicacion", "se vincula", "se vincula", "se conecta",
    "conecta con", "jbl portable", "sony music center", "bose connect",
)
AUTH_EVIDENCE_TERMS = ("original", "autentic", "producto oficial")
APP_NAME_TERMS = (
    " app", "app ", "aplicacion", "jbl portable", "sony music center",
    "bose connect", "marshall bluetooth",
)
APP_SUPPORT_TERMS = ("compatible", "vincul", "conect", "control", "funciona con")
AUTH_NEGATIVE_TERMS = (
    "no es original", "no original", "no es autentico", "replica", "clon",
    "imitacion", "pirata", "falso", "falsa", "generico",
)
APP_NEGATIVE_TERMS = (
    "no es compatible", "no compatible", "no se conecta", "no conecta",
    "no se vincula", "sin compatibilidad",
)
USER_VERIFIED_ACCOUNTS = {"LUISED", "EDILBERTO"}


def normalize(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().lower()


def evidence_is_grounded(evidence, context):
    evidence_n = normalize(evidence)
    context_n = normalize(json.dumps(context, ensure_ascii=False))
    return len(evidence_n) >= 3 and evidence_n in context_n


def asks_authenticity(question):
    text = normalize(question)
    return any(term in text for term in AUTH_QUESTION_TERMS)


def asks_app_compatibility(question):
    padded = f" {normalize(question)} "
    return any(term in padded for term in APP_QUESTION_TERMS)


def validate_decision(decision, context, max_chars=500):
    """Devuelve (autorizada, motivo). Ante cualquier duda falla cerrado."""
    if not isinstance(decision, dict):
        return False, "decision_missing"
    if normalize(decision.get("risk")) != "low":
        return False, "risk_not_low"
    answer = (decision.get("answer") or "").strip()
    evidence = (decision.get("evidence") or "").strip()
    if not answer:
        return False, "answer_missing"
    if len(answer) > max_chars:
        return False, "answer_too_long"
    if not evidence:
        return False, "evidence_missing"
    if not evidence_is_grounded(evidence, context):
        return False, "evidence_not_grounded"

    question = context.get("question_text") or ""
    evidence_n = normalize(evidence)
    if asks_authenticity(question):
        if any(term in evidence_n for term in AUTH_NEGATIVE_TERMS):
            return False, "authenticity_negative_evidence"
        if not any(term in evidence_n for term in AUTH_EVIDENCE_TERMS):
            return False, "authenticity_not_proven"
    if asks_app_compatibility(question):
        if any(term in evidence_n for term in APP_NEGATIVE_TERMS):
            return False, "app_negative_evidence"
        has_app = any(term in f" {evidence_n} " for term in APP_NAME_TERMS)
        has_support = any(term in evidence_n for term in APP_SUPPORT_TERMS)
        if not (has_app and has_support):
            return False, "app_compatibility_not_proven"
    return True, "verified"


def canonical_answer(question):
    """Respuesta cerrada para los dos reclamos comerciales mas sensibles."""
    auth = asks_authenticity(question)
    app = asks_app_compatibility(question)
    if auth and app:
        return ("Buen dia, si, el producto es original y es compatible con la aplicacion "
                "oficial indicada en la publicacion. Saludos cordiales — Elite Market.")
    if auth:
        return ("Buen dia, si, el producto es original, tal como se indica en la publicacion. "
                "Saludos cordiales — Elite Market.")
    if app:
        return ("Buen dia, si, es compatible con la aplicacion indicada en la publicacion. "
                "Saludos cordiales — Elite Market.")
    return None


def user_verified_answer(account, question):
    """Directiva expresa del propietario para estas dos cuentas."""
    if normalize(account).upper() not in USER_VERIFIED_ACCOUNTS:
        return None
    auth = asks_authenticity(question)
    app = asks_app_compatibility(question)
    if auth and app:
        return ("Buen dia, si, el producto es original y es compatible con la aplicacion "
                "oficial de la marca. Saludos cordiales — Elite Market.")
    if auth:
        return ("Buen dia, si, el producto es original. Saludos cordiales — Elite Market.")
    if app:
        return ("Buen dia, si, el producto es compatible con la aplicacion oficial de la marca. "
                "Saludos cordiales — Elite Market.")
    return None
