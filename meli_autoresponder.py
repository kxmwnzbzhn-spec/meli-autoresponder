#!/usr/bin/env python3
"""
MELI Auto-Responder — preguntas y reclamos
Uso: python meli_autoresponder.py

Requisitos:
- Env vars: MELI_APP_ID, MELI_APP_SECRET, MELI_REFRESH_TOKEN
- Crontab sugerido: cada 5 minutos
  */5 * * * * cd /ruta/a/este/script && python meli_autoresponder.py >> autoresponder.log 2>&1
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

API = "https://api.mercadolibre.com"
APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
TOKEN_FILE = os.environ.get("MELI_TOKEN_FILE", ".meli_token.json")
ESCALATION_EMAIL = os.environ.get("ESCALATION_EMAIL", "tu-email@dominio.com")


def _log(msg):
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)


def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return json.load(f)
    return {"refresh_token": os.environ["MELI_REFRESH_TOKEN"]}


def save_token(t):
    with open(TOKEN_FILE, "w") as f:
        json.dump(t, f)


def refresh_access_token():
    t = load_token()
    data = (
        f"grant_type=refresh_token&client_id={APP_ID}&client_secret={APP_SECRET}"
        f"&refresh_token={t['refresh_token']}"
    ).encode()
    req = urllib.request.Request(
        f"{API}/oauth/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        new = json.load(r)
    new["obtained_at"] = int(time.time())
    save_token(new)
    return new["access_token"]


def api(method, path, token, body=None, query=""):
    req = urllib.request.Request(
        f"{API}{path}{query}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method=method,
        data=json.dumps(body).encode() if body else None,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body_bytes = r.read().decode() or "{}"
            return r.status, (json.loads(body_bytes) if body_bytes.strip() else {})
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


# ============================================================
# Reglas de auto-respuesta a preguntas
# ============================================================

RULES = [
    {
        "patterns": [r"es\s+original", r"100\s*%\s*original", r"aut[eé]ntic"],
        "reply": (
            "Hola, gracias por tu consulta. Si, es un producto original de marca, "
            "remanufacturado y revisado por nuestro equipo tecnico. Incluye factura "
            "electronica y 12 meses de garantia directa con el vendedor. Saludos."
        ),
    },
    {
        "patterns": [r"cu[aá]nto\s+tarda", r"cu[aá]ndo\s+llega", r"tiempo\s+de\s+env",
                     r"d[ií]as?\s+de\s+entrega"],
        "reply": (
            "Hola, gracias por tu consulta. Con Mercado Envios la entrega es al dia "
            "siguiente habil en zona metropolitana (CDMX, GDL, MTY) y de 1 a 3 dias "
            "al resto del pais. El empaque va protegido. Saludos."
        ),
    },
    {
        "patterns": [r"es\s+nueva?", r"esta\s+nueva?", r"producto\s+nuevo"],
        "reply": (
            "Hola, gracias por tu consulta. Para transparencia: es un producto "
            "remanufacturado original, revisado y probado, con 12 meses de garantia "
            "directa con nosotros. No es nuevo de fabrica pero funciona al 100%. Saludos."
        ),
    },
    {
        "patterns": [r"factura", r"cfdi"],
        "reply": (
            "Hola, gracias por tu consulta. Si, incluimos factura electronica CFDI a "
            "tu nombre. Al momento de la compra escribenos tus datos fiscales por "
            "mensaje interno y la emitimos en menos de 24 horas habiles. Saludos."
        ),
    },
    {
        "patterns": [r"garant[ií]a"],
        "reply": (
            "Hola, gracias por tu consulta. La garantia es de 12 meses directa con "
            "el vendedor. Cubre defectos de funcionamiento. Cambio fisico los primeros "
            "15 dias. Saludos."
        ),
    },
    {
        "patterns": [r"disponib", r"en\s+stock", r"tienen"],
        "reply": (
            "Hola, gracias por tu consulta. Si, hay stock disponible en este momento. "
            "Haz tu compra y procesamos el envio en menos de 24 horas habiles. Saludos."
        ),
    },
]


def match_rule(text):
    t = (text or "").lower()
    for rule in RULES:
        for pat in rule["patterns"]:
            if re.search(pat, t):
                return rule["reply"]
    return None


def handle_questions(token, seller_id):
    _log("Buscando preguntas sin responder...")
    code, data = api(
        "GET",
        f"/questions/search?seller_id={seller_id}&status=UNANSWERED&limit=50",
        token,
    )
    if code != 200:
        _log(f"  error HTTP {code}: {data}")
        return
    questions = data.get("questions") or []
    _log(f"  {len(questions)} preguntas pendientes")
    answered = 0
    escalated = []
    for q in questions:
        reply = match_rule(q.get("text"))
        if reply:
            c, r = api(
                "POST",
                "/answers",
                token,
                body={"question_id": q["id"], "text": reply},
            )
            if c in (200, 201):
                answered += 1
                _log(f"  ✓ respondida #{q['id']}: {q['text'][:60]}...")
            else:
                _log(f"  ✗ error al responder #{q['id']}: {c} {r}")
        else:
            escalated.append(q)
    _log(f"  total respondidas: {answered}, escalar a humano: {len(escalated)}")
    if escalated:
        _log("  === ESCALAR ===")
        for q in escalated[:10]:
            _log(f"    #{q['id']} item:{q.get('item_id')} :: {q['text'][:120]}")


# ============================================================
# Reclamos
# ============================================================

def handle_claims(token):
    _log("Revisando reclamos abiertos...")
    total = 0
    for stage in ("claim", "dispute", "return"):
        code, data = api(
            "GET",
            f"/post-purchase/v1/claims/search?stage={stage}&status=opened&limit=20",
            token,
        )
        claims = data.get("data") or []
        total += len(claims)
        for cl in claims:
            cid = cl.get("id")
            reason = cl.get("reason_id")
            _log(f"  {stage}#{cid} reason:{reason} buyer:{cl.get('players',[{}])[0].get('user_id')}")

            # Acknowledge inicial (una vez)
            if not cl.get("claimer_got_response"):
                ack = (
                    "Hola, recibimos tu reclamo y lo estamos revisando. En las proximas "
                    "24 horas habiles te contactamos con una solucion. Gracias por tu paciencia."
                )
                c, r = api(
                    "POST",
                    f"/post-purchase/v1/claims/{cid}/messages",
                    token,
                    body={"message": ack},
                )
                if c in (200, 201):
                    _log(f"    ✓ ack enviado al comprador")

            # Escalar siempre — reclamos requieren decision humana
            _log(f"    → ESCALAR: revisar en panel MELI y decidir accion")

    _log(f"  total reclamos abiertos: {total}")


# ============================================================
# Main
# ============================================================

def main():
    try:
        token = refresh_access_token()
    except Exception as e:
        _log(f"ERROR refrescando token: {e}")
        sys.exit(1)

    # Decodificar seller_id del token (sub en JWT no aplica aqui, usamos /users/me)
    code, me = api("GET", "/users/me", token)
    seller_id = me.get("id")
    _log(f"Autenticado como {me.get('nickname')} (id {seller_id})")

    handle_questions(token, seller_id)
    handle_claims(token)

    _log("done")


if __name__ == "__main__":
    main()
