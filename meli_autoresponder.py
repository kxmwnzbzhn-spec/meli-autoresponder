#!/usr/bin/env python3
"""
MELI Auto-Responder + Telegram Alerts
Corre cada 10 min en GitHub Actions.
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
SEEN_FILE = os.environ.get("SEEN_FILE", ".seen_claims.json")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def _log(msg):
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


def load_token():
    return load_json(TOKEN_FILE, {"refresh_token": os.environ.get("MELI_REFRESH_TOKEN")})


def save_token(t):
    save_json(TOKEN_FILE, t)


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


def api(method, path, token, body=None):
    req = urllib.request.Request(
        f"{API}{path}",
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


def telegram_send(text):
    """Envia mensaje al chat configurado. Si no hay token configurado, lo omite."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        _log("  (Telegram no configurado, skip)")
        return False
    try:
        data = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            headers={"Content-Type": "application/json"},
            data=data,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read()
        _log("  ✓ Telegram enviado")
        return True
    except Exception as e:
        _log(f"  ✗ Telegram error: {e}")
        return False


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
        "patterns": [r"cu[aá]nto\s+tarda", r"cu[aá]ndo\s+llega",
                     r"tiempo\s+de\s+env", r"d[ií]as?\s+de\s+entrega"],
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
    code, data = api("GET", f"/questions/search?seller_id={seller_id}&status=UNANSWERED&limit=50", token)
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
            c, r = api("POST", "/answers", token, body={"question_id": q["id"], "text": reply})
            if c in (200, 201):
                answered += 1
                _log(f"  ✓ respondida #{q['id']}: {q['text'][:60]}...")
            else:
                _log(f"  ✗ error #{q['id']}: {c} {r}")
        else:
            escalated.append(q)
    _log(f"  total respondidas: {answered}, escalar: {len(escalated)}")

    if escalated:
        seen = load_json(SEEN_FILE, {"questions": [], "claims": []})
        seen_q = set(seen.get("questions", []))
        new_esc = [q for q in escalated if q["id"] not in seen_q]
        if new_esc:
            lines = ["🔔 *Preguntas escaladas* (no matchearon reglas)\n"]
            for q in new_esc[:5]:
                lines.append(f"• item `{q.get('item_id','?')}`")
                lines.append(f"  _{q['text'][:180]}_")
                lines.append("")
            if len(new_esc) > 5:
                lines.append(f"_(+{len(new_esc)-5} mas)_")
            lines.append(f"👉 Responde en: https://www.mercadolibre.com.mx/myaccount/messages")
            telegram_send("\n".join(lines))
            seen["questions"] = list(seen_q | {q["id"] for q in new_esc})[-500:]
            save_json(SEEN_FILE, seen)


def handle_claims(token):
    _log("Revisando reclamos abiertos...")
    seen = load_json(SEEN_FILE, {"questions": [], "claims": []})
    seen_claims = set(seen.get("claims", []))
    total = 0
    new_alerts = []
    for stage in ("claim", "dispute", "return"):
        code, data = api("GET", f"/post-purchase/v1/claims/search?stage={stage}&status=opened&limit=20", token)
        claims = data.get("data") or []
        total += len(claims)
        for cl in claims:
            cid = str(cl.get("id"))
            reason = cl.get("reason_id")
            _log(f"  {stage}#{cid} reason:{reason}")

            # Enviar acknowledge al comprador (una vez)
            if not cl.get("claimer_got_response"):
                ack = (
                    "Hola, recibimos tu reclamo y lo estamos revisando. En las proximas "
                    "24 horas habiles te contactamos con una solucion. Gracias por tu paciencia."
                )
                c, r = api("POST", f"/post-purchase/v1/claims/{cid}/messages", token, body={"message": ack})
                if c in (200, 201):
                    _log(f"    ✓ ack enviado")

            # Si es reclamo nuevo que no habia visto, agrega a alerta
            if cid not in seen_claims:
                new_alerts.append({"cid": cid, "stage": stage, "reason": reason, "raw": cl})
                seen_claims.add(cid)

    _log(f"  total reclamos: {total}, nuevos: {len(new_alerts)}")

    if new_alerts:
        lines = [f"🚨 *{len(new_alerts)} reclamo(s) nuevo(s)*\n"]
        for a in new_alerts[:10]:
            lines.append(f"• *{a['stage'].upper()}* #{a['cid']}")
            lines.append(f"  motivo: `{a['reason']}`")
            players = a['raw'].get('players') or []
            if players:
                lines.append(f"  comprador: {players[0].get('user_id')}")
            lines.append("")
        lines.append("👉 Revisa en: https://www.mercadolibre.com.mx/myaccount/sales/claims")
        lines.append("_Acknowledgment automatico ya enviado al comprador. Decision humana requerida._")
        telegram_send("\n".join(lines))

    seen["claims"] = list(seen_claims)[-500:]
    save_json(SEEN_FILE, seen)


def main():
    try:
        token = refresh_access_token()
    except Exception as e:
        msg = f"❌ *Auto-Responder error*\n\nFallo refrescando token MELI:\n`{e}`"
        telegram_send(msg)
        _log(f"ERROR refresh: {e}")
        sys.exit(1)

    code, me = api("GET", "/users/me", token)
    seller_id = me.get("id")
    _log(f"Auth OK: {me.get('nickname')} ({seller_id})")

    try:
        handle_questions(token, seller_id)
        handle_claims(token)
    except Exception as e:
        telegram_send(f"❌ *Auto-Responder error*\n\n`{e}`")
        _log(f"ERROR main: {e}")
        sys.exit(1)

    _log("done")


if __name__ == "__main__":
    main()
