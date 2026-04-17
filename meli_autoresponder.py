#!/usr/bin/env python3
"""
MELI Auto-Responder + Telegram Interactivo + Playbooks de Reclamos
Corre cada 10 min en GitHub Actions.

Flujo:
 1. Refresca access_token
 2. Responde preguntas pendientes con reglas
 3. Detecta reclamos nuevos, los clasifica (defecto / no_original / arrepentimiento)
 4. Envia alert a Telegram con botones interactivos
 5. Procesa callbacks de Telegram (botones tocados) y ejecuta acciones
 6. Avanza playbooks pendientes (ej: esperar confirmacion de MELI bot)
 7. Envia recordatorios a las 72hrs para pedir exclusion en chat de ayuda
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
TOKEN_FILE = ".meli_token.json"
STATE_FILE = ".seen_claims.json"

TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID")


def _log(msg):
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)


# ============================================================
# Storage helpers
# ============================================================

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
        json.dump(data, f, indent=2)


def load_state():
    return load_json(STATE_FILE, {
        "questions_seen": [],
        "claims_seen": [],
        "claim_states": {},  # {claim_id: {type, step, data, next_check}}
        "last_telegram_update_id": 0,
    })


# ============================================================
# MELI API
# ============================================================

def refresh_access_token():
    t = load_json(TOKEN_FILE, {"refresh_token": os.environ.get("MELI_REFRESH_TOKEN")})
    data = (
        f"grant_type=refresh_token&client_id={APP_ID}&client_secret={APP_SECRET}"
        f"&refresh_token={t['refresh_token']}"
    ).encode()
    req = urllib.request.Request(
        f"{API}/oauth/token", data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        new = json.load(r)
    new["obtained_at"] = int(time.time())
    save_json(TOKEN_FILE, new)
    return new["access_token"]


def meli(method, path, token, body=None):
    req = urllib.request.Request(
        f"{API}{path}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method=method,
        data=json.dumps(body).encode() if body else None,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            txt = r.read().decode() or "{}"
            return r.status, (json.loads(txt) if txt.strip() else {})
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read().decode())
        except Exception: return e.code, {}


# ============================================================
# Telegram
# ============================================================

def tg(method, body):
    if not TG_TOKEN or not TG_CHAT:
        return None
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TG_TOKEN}/{method}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(body).encode(), method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        _log(f"  telegram err: {e}")
        return None


def tg_send(text, buttons=None):
    body = {"chat_id": TG_CHAT, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    if buttons: body["reply_markup"] = {"inline_keyboard": buttons}
    return tg("sendMessage", body)


def tg_edit(chat_id, msg_id, text, buttons=None):
    body = {"chat_id": chat_id, "message_id": msg_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    if buttons: body["reply_markup"] = {"inline_keyboard": buttons}
    return tg("editMessageText", body)


def tg_answer_cb(cb_id, text):
    return tg("answerCallbackQuery", {"callback_query_id": cb_id, "text": text[:200]})


# ============================================================
# Clasificacion de reclamos
# ============================================================

REASON_MAP = {
    # defectos
    "product_is_defective": "defecto",
    "defective_product": "defecto",
    "damaged_product": "defecto",
    "missing_parts": "defecto",
    "not_as_described": "defecto",
    "product_not_as_described": "defecto",
    "pdd_not_as_described": "defecto",
    # no original
    "product_is_not_original": "no_original",
    "not_original": "no_original",
    "replica": "no_original",
    "fake_product": "no_original",
    # arrepentimiento
    "buyer_regret": "arrepentimiento",
    "change_of_mind": "arrepentimiento",
    "buyer_change_mind": "arrepentimiento",
}


def classify_claim(reason_id):
    rid = (reason_id or "").lower()
    if rid in REASON_MAP: return REASON_MAP[rid]
    for key, val in REASON_MAP.items():
        if key in rid or rid in key: return val
    return "otro"


TYPE_EMOJI = {"defecto": "🔧", "no_original": "🛡️", "arrepentimiento": "↩️", "otro": "❓"}


MELI_CONFIRM_MSG = (
    "En el caso de aceptar la opcion sugerida por el sistema mi reputacion ya no se veria "
    "afectada por dar solucion dentro de las 24 horas despues de iniciado el reclamo esto "
    "es correcto, esto me indico el asistente"
)
ACCEPT_SOLUTION_MSG = "Acepto la solucion sugerida"


# ============================================================
# Preguntas: DESHABILITADO — las responde Mercabot aparte
# ============================================================


# ============================================================
# Reclamos - accion handlers
# ============================================================

def claim_action(token, cid, action, body=None):
    return meli("POST", f"/post-purchase/v1/claims/{cid}/actions/{action}", token, body or {})


def claim_send_msg(token, cid, text):
    return meli("POST", f"/post-purchase/v1/claims/{cid}/messages", token, {"message": text})


def claim_get_messages(token, cid):
    c, d = meli("GET", f"/post-purchase/v1/claims/{cid}/messages", token)
    return d.get("data") or d.get("messages") or []


def claim_get_details(token, cid):
    c, d = meli("GET", f"/post-purchase/v1/claims/{cid}", token)
    return d


# ============================================================
# Playbooks
# ============================================================

def start_playbook(token, cid, claim_type, state):
    """Inicia playbook para un reclamo. Devuelve mensaje de resultado."""
    if claim_type == "arrepentimiento":
        # Bajo impacto reputacional: solo aceptar devolucion
        c, r = claim_action(token, cid, "allow_return")
        state["claim_states"][str(cid)] = {
            "type": claim_type, "step": "completed",
            "accepted_at": int(time.time())
        }
        return f"✓ Devolución aceptada (HTTP {c}). Arrepentimiento no impacta reputación."

    # defecto / no_original: mismo flujo — enviar mensaje de confirmación al sistema
    c, r = claim_send_msg(token, cid, MELI_CONFIRM_MSG)
    state["claim_states"][str(cid)] = {
        "type": claim_type,
        "step": "waiting_bot_reply",
        "msg_sent_at": int(time.time()),
        "next_check": int(time.time()) + 600,  # chequear en 10 min
    }
    return f"✓ Mensaje enviado al sistema MELI (HTTP {c}). Esperando confirmación del asistente."


def advance_playbook(token, cid, cstate, state):
    """Avanza un playbook en progreso. cstate es el dict de ese claim."""
    step = cstate.get("step")
    now = int(time.time())

    if step == "waiting_bot_reply":
        # Leer mensajes del claim, buscar respuesta del asistente
        msgs = claim_get_messages(token, cid)
        sender_types_seen = set()
        confirmed = False
        for m in msgs:
            # MELI msg structure varies; buscar mensajes del "system" o "mediator"
            sender = (m.get("sender_role") or m.get("from") or "").lower()
            txt = (m.get("message") or m.get("text") or "").lower()
            sender_types_seen.add(sender)
            if sender in ("system", "mediator", "meli", "platform") or "asistente" in txt:
                # heuristic: cualquier respuesta del sistema despues de nuestro mensaje cuenta
                if "correct" in txt or "afect" in txt or "solucion" in txt or "sugerida" in txt:
                    confirmed = True
                    break

        if confirmed:
            # Aceptar solucion
            claim_send_msg(token, cid, ACCEPT_SOLUTION_MSG)
            c, r = claim_action(token, cid, "allow_return")
            cstate["step"] = "solution_accepted"
            cstate["accepted_at"] = now
            cstate["next_check"] = now + 72 * 3600  # 72h
            tg_send(
                f"✅ *Reclamo #{cid}* — solución aceptada automáticamente\n\n"
                f"Tipo: {cstate.get('type')}\n"
                f"El sistema MELI confirmó. Devolución aceptada y el playbook "
                f"te recordará en 72hrs para pedir exclusión en el chat de ayuda."
            )
            return True
        # Si aún no confirma, reagenda
        if now - cstate.get("msg_sent_at", now) > 6 * 3600:
            # Más de 6hrs sin respuesta — escala
            tg_send(
                f"⚠️ *Reclamo #{cid}* — playbook estancado\n\n"
                f"Envié el mensaje de confirmación hace 6hrs pero el sistema MELI no responde. "
                f"Revisa manualmente: https://www.mercadolibre.com.mx/myaccount/sales/claims\n\n"
                f"Mensajes vistos de: {sender_types_seen}"
            )
            cstate["step"] = "stuck"
        else:
            cstate["next_check"] = now + 600  # recheck en 10 min
        return True

    if step == "solution_accepted":
        # Esperar 72hrs post-aceptación para recordar exclusión
        if now >= cstate.get("next_check", 0):
            # Ver status actual del reclamo
            details = claim_get_details(token, cid)
            status = details.get("status") or details.get("stage")
            tg_send(
                f"⏰ *Recordatorio: exclusión de reclamo #{cid}*\n\n"
                f"Tipo: `{cstate.get('type')}`\n"
                f"Status actual: `{status}`\n\n"
                f"Ve al **chat de ayuda de MELI** (no al chat del reclamo) y pega este mensaje:\n\n"
                f"```\nHola, solicito la exclusión del reclamo #{cid} ya que la solución "
                f"fue brindada dentro de las 24 horas de iniciado el reclamo, conforme a "
                f"la sugerencia del sistema. Gracias.\n```\n\n"
                f"Link: https://www.mercadolibre.com.mx/ayuda\n\n"
                f"Cuando lo hayas enviado, mándame `/listo {cid}` al bot y marco el reclamo como resuelto. "
                f"Si MELI dice que aún no se puede, mándame `/posponer {cid}` y te recuerdo en 72hrs más."
            )
            cstate["step"] = "exclusion_reminded"
            cstate["reminded_at"] = now
        return True

    if step == "exclusion_reminded":
        # esperar confirmación por comando de usuario, no hacer nada más
        return True

    return False


# ============================================================
# Detección de reclamos nuevos
# ============================================================

def handle_claims(token, state):
    _log("Reclamos...")
    seen = set(state.get("claims_seen", []))
    total = 0
    new_alerts = []
    for stage in ("claim", "dispute", "return"):
        c, d = meli("GET", f"/post-purchase/v1/claims/search?stage={stage}&status=opened&limit=20", token)
        for cl in (d.get("data") or []):
            cid = str(cl.get("id"))
            total += 1
            if cid in seen: continue
            seen.add(cid)
            new_alerts.append((cid, stage, cl))

    _log(f"  total:{total}  nuevos:{len(new_alerts)}")

    for cid, stage, cl in new_alerts:
        reason = cl.get("reason_id") or ""
        tipo = classify_claim(reason)
        emoji = TYPE_EMOJI.get(tipo, "❓")
        order_id = (cl.get("resource_sub_type") or cl.get("resource_id") or "")

        # Extraer monto de la orden (para auto-decisión arrepentimiento)
        amount = 0
        try:
            if order_id and str(order_id).isdigit():
                c_ord, ord_data = meli("GET", f"/orders/{order_id}", token)
                amount = float(ord_data.get("total_amount") or 0)
        except Exception:
            amount = 0

        # Guardar estado inicial + timestamp creación
        state["claim_states"][cid] = {
            "type": tipo,
            "stage": stage,
            "reason": reason,
            "amount": amount,
            "created_at": int(time.time()),
            "last_status": stage,
            "step": "pending_user_action",
        }

        # (b) Auto-aceptar arrepentimiento con monto < $500
        if tipo == "arrepentimiento" and 0 < amount < 500:
            _log(f"  auto-arrepentimiento #{cid} (${amount})")
            result = start_playbook(token, cid, tipo, state)
            tg_send(
                f"↩️ *Arrepentimiento auto-aceptado* — #{cid}\n\n"
                f"Monto ${amount:.0f} (< $500 umbral) → devolución aceptada automáticamente.\n"
                f"_{result}_"
            )
            continue

        # Mensaje Telegram con botones
        amount_line = f"\nMonto: ${amount:.0f} MXN" if amount else ""
        txt = (
            f"🚨 *Reclamo nuevo #{cid}*\n\n"
            f"{emoji} Tipo: *{tipo.upper()}*\n"
            f"Motivo MELI: `{reason}`\n"
            f"Stage: `{stage}`"
            f"{amount_line}\n"
            f"Orden: `{order_id}`\n\n"
            f"Elige acción:"
        )
        if tipo == "arrepentimiento":
            buttons = [
                [{"text": "↩️ Aceptar devolución (auto)", "callback_data": f"pb:{cid}"}],
                [{"text": "👁️ Ver detalles", "callback_data": f"dt:{cid}"}],
            ]
        else:
            buttons = [
                [{"text": f"{emoji} Ejecutar playbook", "callback_data": f"pb:{cid}"}],
                [{"text": "✅ Solo aceptar devolución", "callback_data": f"ar:{cid}"},
                 {"text": "💰 Reembolso 100%", "callback_data": f"rf:{cid}"}],
                [{"text": "👁️ Ver detalles", "callback_data": f"dt:{cid}"}],
            ]
        tg_send(txt, buttons)

    state["claims_seen"] = list(seen)[-500:]


# ============================================================
# (a) Tracking de status — detectar cambios de fase
# ============================================================

STATUS_LABELS = {
    "opened": "abierto",
    "closed": "cerrado",
    "in_process": "en proceso",
    "claim": "reclamo",
    "dispute": "mediación MELI",
    "return": "devolución en camino",
}

def track_status_changes(token, state):
    """Revisa cada claim_state activo y avisa si cambió de status."""
    for cid, cst in list(state.get("claim_states", {}).items()):
        if cst.get("step") in ("completed", "stuck"):
            continue
        c, d = meli("GET", f"/post-purchase/v1/claims/{cid}", token)
        if c != 200: continue
        curr = d.get("stage") or d.get("status") or ""
        prev = cst.get("last_status")
        if curr and curr != prev:
            prev_lbl = STATUS_LABELS.get(prev, prev or "?")
            curr_lbl = STATUS_LABELS.get(curr, curr)
            tg_send(
                f"🔄 *Status de reclamo #{cid} cambió*\n\n"
                f"`{prev_lbl}` → *{curr_lbl}*\n"
                f"Tipo: {cst.get('type')}\n"
                f"Edad: {int((time.time() - cst.get('created_at',time.time()))/3600)}hrs"
            )
            cst["last_status"] = curr


# ============================================================
# (c) Alerta de reclamos por vencerse (>20hrs sin resolver)
# ============================================================

def check_overdue_claims(state):
    now = int(time.time())
    for cid, cst in (state.get("claim_states") or {}).items():
        if cst.get("step") in ("completed", "stuck"):
            continue
        age_hrs = (now - cst.get("created_at", now)) / 3600
        if age_hrs < 20: continue
        if cst.get("urgent_alerted_at"): continue  # ya alertado
        tg_send(
            f"🔥 *URGENTE — Reclamo #{cid}*\n\n"
            f"Lleva {age_hrs:.1f}hrs abierto sin resolverse.\n"
            f"A las 24hrs pierdes la protección reputacional.\n\n"
            f"Tipo: {cst.get('type')} | Monto: ${cst.get('amount',0):.0f}\n"
            f"Step actual: `{cst.get('step')}`\n\n"
            f"👉 https://www.mercadolibre.com.mx/myaccount/sales/claims/{cid}"
        )
        cst["urgent_alerted_at"] = now


# ============================================================
# (d) Estadísticas semanales — resumen los lunes
# ============================================================

def send_weekly_stats_if_monday(state):
    now = int(time.time())
    last = state.get("last_weekly_sent", 0)
    if now - last < 6 * 24 * 3600:  # menos de 6 días, no enviar
        return
    # Lunes en UTC; GitHub Actions corre en UTC
    weekday = datetime.utcfromtimestamp(now).weekday()  # 0=lunes
    if weekday != 0:
        return

    week_ago = now - 7 * 24 * 3600
    claims = state.get("claim_states", {})
    recent = [c for c in claims.values() if c.get("created_at", 0) >= week_ago]
    completed = [c for c in recent if c.get("step") == "completed"]
    stuck = [c for c in recent if c.get("step") == "stuck"]

    # Tiempo promedio de resolución (completed con timestamp)
    times = []
    for c in completed:
        if c.get("accepted_at") and c.get("created_at"):
            times.append(c["accepted_at"] - c["created_at"])
    avg_hrs = (sum(times) / len(times) / 3600) if times else 0

    # Por tipo
    by_type = {}
    for c in recent:
        t = c.get("type", "otro")
        by_type[t] = by_type.get(t, 0) + 1

    breakdown = "\n".join(f"  • {k}: {v}" for k, v in sorted(by_type.items(), key=lambda x: -x[1])) or "  (sin reclamos)"

    tg_send(
        f"📊 *Resumen semanal de reclamos*\n"
        f"_Semana terminando {datetime.utcnow().strftime('%d %b %Y')}_\n\n"
        f"Total reclamos: *{len(recent)}*\n"
        f"Resueltos (completed): *{len(completed)}*\n"
        f"Estancados (stuck): *{len(stuck)}*\n"
        f"Tiempo promedio resolución: *{avg_hrs:.1f}hrs*\n\n"
        f"*Desglose por tipo:*\n{breakdown}\n\n"
        f"✅ Protección reputacional efectiva: "
        f"{sum(1 for c in completed if c.get('type') in ('defecto','no_original'))}/"
        f"{sum(1 for c in recent if c.get('type') in ('defecto','no_original'))}"
    )
    state["last_weekly_sent"] = now


# ============================================================
# Procesar callbacks de Telegram (botones tocados)
# ============================================================

def process_telegram_callbacks(token, state):
    """Polling de /getUpdates para procesar botones tocados."""
    if not TG_TOKEN: return
    last_id = state.get("last_telegram_update_id", 0)
    resp = tg("getUpdates", {"offset": last_id + 1, "timeout": 0, "allowed_updates": ["callback_query", "message"]})
    if not resp or not resp.get("ok"): return
    updates = resp.get("result", [])
    _log(f"Telegram callbacks: {len(updates)}")

    for u in updates:
        state["last_telegram_update_id"] = max(state.get("last_telegram_update_id", 0), u["update_id"])

        # Procesar comandos de texto tipo /listo 12345 y /posponer 12345
        msg = u.get("message")
        if msg and msg.get("text","").startswith("/"):
            text = msg["text"].strip()
            chat_id = msg["chat"]["id"]
            parts = text.split()
            if len(parts) >= 2 and parts[0] in ("/listo","/posponer"):
                cmd, cid = parts[0], parts[1].lstrip("#")
                cst = state.get("claim_states", {}).get(cid)
                if not cst:
                    tg("sendMessage", {"chat_id": chat_id, "text": f"No tengo estado para #{cid}"})
                    continue
                if cmd == "/listo":
                    cst["step"] = "completed"
                    cst["completed_at"] = int(time.time())
                    tg("sendMessage", {"chat_id": chat_id, "text": f"✓ Reclamo #{cid} marcado como resuelto."})
                elif cmd == "/posponer":
                    cst["step"] = "solution_accepted"
                    cst["next_check"] = int(time.time()) + 72*3600
                    tg("sendMessage", {"chat_id": chat_id, "text": f"✓ Recordatorio reagendado +72hrs para #{cid}."})
            continue

        cb = u.get("callback_query")
        if not cb: continue
        data = cb.get("data", "")
        if ":" not in data:
            tg_answer_cb(cb["id"], "acción inválida"); continue
        action, cid = data.split(":", 1)
        orig_text = cb.get("message", {}).get("text", "")

        result = ""
        try:
            # Test mode: si el cid empieza con "DEMO" no llama API real
            if str(cid).startswith("DEMO"):
                result = f"🧪 Demo: acción `{action}` registrada (no se llamó MELI). Funcional ✓"
                tg_edit(cb["message"]["chat"]["id"], cb["message"]["message_id"],
                        orig_text + f"\n\n*Demo OK:* `{action}`\n_{result}_")
                tg_answer_cb(cb["id"], result[:200])
                continue

            if action == "ar":  # allow return
                c, r = claim_action(token, cid, "allow_return")
                result = "✅ Devolución aceptada" if c in (200,201) else f"✗ err {c}"
                state["claim_states"].setdefault(str(cid), {})["step"] = "completed"

            elif action == "rf":  # refund
                c, r = claim_action(token, cid, "refund")
                result = "💰 Reembolso emitido" if c in (200,201) else f"✗ err {c}"
                state["claim_states"].setdefault(str(cid), {})["step"] = "completed"

            elif action == "pb":  # playbook
                # Descubrir tipo si aún no lo tenemos
                cst = state.get("claim_states", {}).get(cid, {})
                tipo = cst.get("type")
                if not tipo:
                    details = claim_get_details(token, cid)
                    tipo = classify_claim(details.get("reason_id") or "")
                result = start_playbook(token, cid, tipo, state)

            elif action == "dt":  # details
                details = claim_get_details(token, cid)
                result = f"Status: {details.get('status')} / Stage: {details.get('stage')} / Reason: {details.get('reason_id')}"

            else:
                result = f"acción desconocida: {action}"
        except Exception as e:
            result = f"✗ error: {e}"

        # Actualizar mensaje y confirmar callback
        tg_edit(cb["message"]["chat"]["id"], cb["message"]["message_id"],
                orig_text + f"\n\n*Acción ejecutada:* `{action}`\n_{result}_")
        tg_answer_cb(cb["id"], result[:200])


# ============================================================
# Avanzar playbooks pendientes (state machine)
# ============================================================

def advance_pending_playbooks(token, state):
    now = int(time.time())
    to_advance = []
    for cid, cst in (state.get("claim_states") or {}).items():
        if cst.get("step") in ("completed", "stuck"): continue
        if cst.get("next_check", 0) <= now:
            to_advance.append((cid, cst))
    _log(f"Playbooks por avanzar: {len(to_advance)}")
    for cid, cst in to_advance:
        try:
            advance_playbook(token, cid, cst, state)
        except Exception as e:
            _log(f"  playbook #{cid} err: {e}")


# ============================================================
# Main
# ============================================================

def main():
    state = load_state()
    state.setdefault("claim_states", {})

    try:
        token = refresh_access_token()
    except Exception as e:
        tg_send(f"❌ *MELI token error*\n\n`{e}`")
        _log(f"token err: {e}"); sys.exit(1)

    code, me = meli("GET", "/users/me", token)
    seller_id = me.get("id")
    _log(f"Auth: {me.get('nickname')} ({seller_id})")

    try:
        handle_claims(token, state)
        process_telegram_callbacks(token, state)
        advance_pending_playbooks(token, state)
        track_status_changes(token, state)
        check_overdue_claims(state)
        send_weekly_stats_if_monday(state)
    except Exception as e:
        tg_send(f"❌ *Auto-Responder error*\n\n`{e}`")
        _log(f"main err: {e}"); save_json(STATE_FILE, state); sys.exit(1)

    save_json(STATE_FILE, state)
    _log("done")


if __name__ == "__main__":
    main()
