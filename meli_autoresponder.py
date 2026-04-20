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
TG_RET_TOKEN = os.environ.get("TELEGRAM_RETURNS_BOT_TOKEN", "")
RETURNS_BOT_USERNAME = "Sonixmx_devoluciones_bot"
SHEETS_WEBHOOK_URL = os.environ.get("SHEETS_WEBHOOK_URL")  # Apps Script Web App URL


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
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode())
            return {"ok": False, "error_code": e.code, "description": err_body.get("description","")}
        except Exception:
            return {"ok": False, "error_code": e.code}
    except Exception as e:
        _log(f"  telegram err: {e}")
        return None


def tg_send(text, buttons=None):
    body = {"chat_id": TG_CHAT, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    if buttons: body["reply_markup"] = {"inline_keyboard": buttons}
    return tg("sendMessage", body)


def tg_edit(chat_id, msg_id, text, buttons=None):
    # Intentar editar con Markdown, si falla reintenta sin parse_mode, y si falla manda mensaje nuevo
    body = {"chat_id": chat_id, "message_id": msg_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    if buttons: body["reply_markup"] = {"inline_keyboard": buttons}
    r = tg("editMessageText", body)
    if r and r.get("ok"): return r
    body.pop("parse_mode", None)
    r = tg("editMessageText", body)
    if r and r.get("ok"): return r
    # Fallback: mensaje nuevo
    return tg_send(text)


def tg_answer_cb(cb_id, text):
    return tg("answerCallbackQuery", {"callback_query_id": cb_id, "text": text[:200]})


# ============================================================
# Google Sheets (vía Apps Script webhook)
# ============================================================

def push_to_sheets(payload):
    """POST a la URL del Web App de Apps Script para agregar fila."""
    if not SHEETS_WEBHOOK_URL:
        _log("  sheets: no webhook configurado")
        return False
    try:
        req = urllib.request.Request(
            SHEETS_WEBHOOK_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload).encode(),
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = r.read().decode()
        _log(f"  ✓ sheets push: {resp[:100]}")
        return True
    except Exception as e:
        _log(f"  ✗ sheets err: {e}")
        return False


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
# RETURNS PROTECTION — bot dedicado de devoluciones
# ============================================================

RETURN_REASONS = {
    # Reasons que indican devolución entrante sospechosa
    "product_not_as_described",
    "return_by_product_not_as_described",
    "product_defective",
    "return_product_defective",
    "return_change_of_mind",
    "product_is_not_original",
    "product_is_defective",
    "return_by_change_of_mind",
    "item_arrived_broken",
    "not_delivered",
    "wrong_product_received",
}


def tg_ret(method, body, files=None):
    """Telegram Bot API al bot de DEVOLUCIONES."""
    if not TG_RET_TOKEN:
        return None
    try:
        if files:
            # multipart
            boundary = "----sonixmxretunbnd" + str(int(time.time()))
            data = b""
            for k, v in body.items():
                data += f"--{boundary}\r\n".encode()
                data += f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
                data += str(v).encode() + b"\r\n"
            for fname, (content, mime) in files.items():
                data += f"--{boundary}\r\n".encode()
                data += f'Content-Disposition: form-data; name="{fname}"; filename="{fname}"\r\n'.encode()
                data += f'Content-Type: {mime}\r\n\r\n'.encode()
                data += content + b"\r\n"
            data += f"--{boundary}--\r\n".encode()
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{TG_RET_TOKEN}/{method}",
                data=data,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                method="POST",
            )
        else:
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{TG_RET_TOKEN}/{method}",
                headers={"Content-Type": "application/json"},
                data=json.dumps(body).encode(), method="POST",
            )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return {"ok": False, "error_code": e.code, "description": json.loads(e.read().decode()).get("description","")}
        except Exception:
            return {"ok": False, "error_code": e.code}
    except Exception as e:
        _log(f"  tg_ret err: {e}")
        return None


def tg_ret_send(chat_id, text, buttons=None, reply_to=None):
    body = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    if buttons: body["reply_markup"] = {"inline_keyboard": buttons}
    if reply_to: body["reply_to_message_id"] = reply_to
    return tg_ret("sendMessage", body)


def tg_ret_answer_cb(cb_id, text):
    return tg_ret("answerCallbackQuery", {"callback_query_id": cb_id, "text": text[:200]})


def tg_ret_get_file_url(file_id):
    """Obtener la URL temporal para descargar un archivo de Telegram."""
    r = tg_ret("getFile", {"file_id": file_id})
    if not r or not r.get("ok"):
        return None
    path = r.get("result", {}).get("file_path")
    if not path:
        return None
    return f"https://api.telegram.org/file/bot{TG_RET_TOKEN}/{path}"


def tg_ret_download_file(file_id):
    """Descarga bytes de un archivo de Telegram via file_id."""
    url = tg_ret_get_file_url(file_id)
    if not url: return None, None
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read(), url.split("/")[-1]
    except Exception as e:
        _log(f"  tg_ret_download err: {e}")
        return None, None


def upload_claim_attachment(token, claim_id, file_bytes, filename, mime_type="application/octet-stream"):
    """Sube archivo a MELI claim via POST /v1/claims/{claim_id}/attachments."""
    boundary = "----sonixmxclmbnd" + str(int(time.time()))
    data = b""
    data += f"--{boundary}\r\n".encode()
    data += f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
    data += f'Content-Type: {mime_type}\r\n\r\n'.encode()
    data += file_bytes + b"\r\n"
    data += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"https://api.mercadolibre.com/v1/claims/{claim_id}/attachments",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def send_claim_message(token, claim_id, text, attachment_ids=None):
    """Envía mensaje formal al mediador del claim con adjuntos."""
    body = {
        "receiver_role": "respondent",
        "message": text,
    }
    if attachment_ids:
        body["attachments"] = attachment_ids
    code, resp = meli("POST", f"/v1/claims/{claim_id}/messages", token, body=body)
    return code, resp


def start_return_playbook(token, cid, claim, state):
    """Al detectar claim de devolución: registrar y mandar alerta al BOT DE DEVOLUCIONES."""
    rs = state.setdefault("return_states", {})
    if cid in rs and rs[cid].get("step") not in ("cancelled",):
        return  # ya iniciado
    buyer_id = (claim.get("players") or [{}])[0].get("user_id")
    resource_id = claim.get("resource_id") or claim.get("resource", {}).get("id")
    rs[cid] = {
        "claim_id": cid,
        "step": "awaiting_arrival",
        "buyer_id": buyer_id,
        "resource_id": resource_id,
        "attachments": [],
        "ret_chat_id": TG_CHAT,   # por default el mismo chat privado
        "active": False,
        "created_at": int(time.time()),
        "deadline_at": int(time.time()) + 48*3600,
    }
    # Alerta directa al bot de devoluciones (todo el flujo vive ahi)
    msg = (
        f"🚨 *DEVOLUCION ABIERTA*\n\n"
        f"Claim: `{cid}`\n"
        f"Comprador: `{buyer_id}`\n"
        f"Motivo: `{claim.get('reason_id','')}`\n"
        f"Deadline MELI: 48 h\n\n"
        f"Cuando llegue el paquete de vuelta, toca el boton:"
    )
    tg_ret_send(TG_CHAT, msg, buttons=[
        [{"text":"📦 Ya llego el paquete", "callback_data": f"ret_arrived|{cid}"}],
        [{"text":"⏳ Aun no llega", "callback_data": f"ret_snooze|{cid}"}],
    ])
    _log(f"Return playbook started for {cid}")


def process_returns_bot(token, state):
    """Loop del bot de devoluciones: lee getUpdates, procesa /start, media, callbacks."""
    if not TG_RET_TOKEN:
        return
    rs = state.setdefault("return_states", {})
    if not rs:
        return  # nada que hacer
    offset = state.get("returns_offset", 0)
    try:
        upd = tg_ret("getUpdates", {"offset": offset+1, "timeout": 0, "limit": 50})
    except Exception as e:
        _log(f"  returns getUpdates err: {e}"); return
    if not upd or not upd.get("ok"):
        return
    updates = upd.get("result", [])
    if not updates:
        return
    last_id = offset
    for u in updates:
        last_id = max(last_id, u.get("update_id", offset))
        try:
            _handle_return_update(token, u, state)
        except Exception as e:
            _log(f"  return update err: {e}")
    state["returns_offset"] = last_id


def _active_return_for_chat(state, chat_id):
    """Devuelve (cid, rs_entry) del claim activo en ese chat, o (None, None)."""
    for cid, rs in (state.get("return_states") or {}).items():
        if rs.get("active") and rs.get("ret_chat_id") == chat_id and rs.get("step") == "collecting":
            return cid, rs
    return None, None


def _handle_return_update(token, u, state):
    # Caso 1: mensaje (texto, foto, video, documento)
    msg = u.get("message") or u.get("edited_message")
    if msg:
        chat_id = msg.get("chat", {}).get("id")
        txt = msg.get("text", "") or ""
        # /start con deep-link
        if txt.startswith("/start"):
            parts = txt.split(maxsplit=1)
            payload = parts[1] if len(parts) > 1 else ""
            return _return_start(chat_id, payload, state)
        if txt.strip().lower() in ("/cancel","cancelar","salir"):
            return _return_cancel(chat_id, state)
        # /status
        if txt.startswith("/status"):
            cid, rs = _active_return_for_chat(state, chat_id)
            if rs:
                tg_ret_send(chat_id, f"Claim `{cid}` — paso `{rs.get('step')}` — evidencias recibidas: {len(rs.get('attachments',[]))}")
            else:
                tg_ret_send(chat_id, "No hay protocolo activo. Toca el boton de \"Iniciar protocolo\" desde el bot principal.")
            return
        # Multimedia: asociar al claim activo del chat
        media_file_id = None; mime = "application/octet-stream"; kind = "unknown"
        if msg.get("photo"):
            media_file_id = msg["photo"][-1]["file_id"]
            mime = "image/jpeg"; kind = "photo"
        elif msg.get("video"):
            media_file_id = msg["video"]["file_id"]
            mime = msg["video"].get("mime_type","video/mp4"); kind = "video"
        elif msg.get("document"):
            media_file_id = msg["document"]["file_id"]
            mime = msg["document"].get("mime_type","application/octet-stream")
            kind = "document"
        elif msg.get("video_note"):
            media_file_id = msg["video_note"]["file_id"]
            mime = "video/mp4"; kind = "video_note"
        if media_file_id:
            cid, rs = _active_return_for_chat(state, chat_id)
            if not rs:
                tg_ret_send(chat_id, "No hay protocolo activo. Vuelve al bot principal y toca \"Iniciar protocolo anti-fraude\".")
                return
            rs["attachments"].append({"telegram_file_id": media_file_id, "kind": kind, "mime": mime,
                                      "msg_id": msg.get("message_id"), "ts": int(time.time())})
            n = len(rs["attachments"])
            # Responder con feedback + botones finales
            tg_ret_send(chat_id,
                f"✅ Evidencia #{n} recibida ({kind}).\n\n"
                "Manda todas las fotos/videos que tengas. Cuando termines, toca una opcion:",
                buttons=[
                    [{"text":"🚨 Es FRAUDE — abrir reclamo", "callback_data": f"ret_fraud|{cid}"}],
                    [{"text":"✔️ Esta correcto — aceptar devolucion", "callback_data": f"ret_ok|{cid}"}],
                    [{"text":"❌ Cancelar protocolo", "callback_data": f"ret_cancel|{cid}"}],
                ])
            return
        # mensaje de texto sin saber qué hacer
        if txt:
            cid, rs = _active_return_for_chat(state, chat_id)
            if rs:
                tg_ret_send(chat_id, "Te escucho. Mandame fotos/videos del paquete y contenido. Cuando termines, usa los botones.")
            else:
                tg_ret_send(chat_id, "Hola. Inicia el protocolo desde el boton \"Iniciar protocolo anti-fraude\" del bot principal.")
        return

    # Caso 2: callback de botones
    cb = u.get("callback_query")
    if cb:
        data = cb.get("data","") or ""
        chat_id = cb.get("message",{}).get("chat",{}).get("id")
        cb_id = cb.get("id")
        if "|" not in data:
            tg_ret_answer_cb(cb_id, "accion invalida"); return
        action, cid = data.split("|", 1)
        rs = state.get("return_states",{}).get(cid)
        if not rs:
            tg_ret_answer_cb(cb_id, "Claim no encontrado"); return

        if action == "ret_arrived":
            tg_ret_answer_cb(cb_id, "Protocolo activado")
            rs["active"] = True
            rs["ret_chat_id"] = chat_id
            rs["step"] = "collecting"
            tg_ret_send(chat_id,
                f"🛡️ *Protocolo anti-fraude ACTIVO*\n\n"
                f"Claim: `{cid}`\n\n"
                f"Mandame AQUI todo lo que tengas:\n"
                f"• Foto del paquete cerrado (folio/cinta intactos)\n"
                f"• Foto del peso en bascula\n"
                f"• Video continuo de apertura (sin cortes)\n"
                f"• Fotos del contenido\n\n"
                f"Cuando termines, usa los botones que te apareceran."
            )
        elif action == "ret_snooze":
            tg_ret_answer_cb(cb_id, "Ok, te recuerdo en 12h")
            rs["snooze_until"] = int(time.time()) + 12*3600
            tg_ret_send(chat_id, f"⏰ Snooze activado para `{cid}`. Te vuelvo a preguntar en 12 h.")
        elif action == "ret_fraud":
            tg_ret_answer_cb(cb_id, "Subiendo evidencia a MELI...")
            _return_submit_fraud(token, cid, rs, state)
        elif action == "ret_ok":
            tg_ret_answer_cb(cb_id, "Marcando como correcto...")
            _return_accept(token, cid, rs, state)
        elif action == "ret_cancel":
            tg_ret_answer_cb(cb_id, "Protocolo cancelado")
            rs["active"] = False; rs["step"] = "cancelled"
            tg_ret_send(chat_id, f"Protocolo cancelado para `{cid}`. Puedes reiniciar cuando quieras.")
        return


def _return_start(chat_id, payload, state):
    """/start CLM_XXX desde Telegram → activar modo captura."""
    cid = payload.strip()
    if not cid:
        tg_ret_send(chat_id, "👋 Bot de devoluciones anti-fraude.\n\nCuando abras el protocolo desde el bot principal, serás dirigido aquí con un deep-link. Luego mándame las fotos/videos del paquete.")
        return
    rs = state.get("return_states",{}).get(cid)
    if not rs:
        tg_ret_send(chat_id, f"No tengo registro del claim `{cid}`. Verifica que el claim siga abierto.")
        return
    # activar captura
    rs["active"] = True
    rs["ret_chat_id"] = chat_id
    rs["step"] = "collecting"
    tg_ret_send(chat_id,
        f"🛡️ *Protocolo anti-fraude activo*\n\n"
        f"Claim: `{cid}`\n"
        f"Motivo: devolución entrante\n\n"
        f"Ahora mandame AQUI todo lo que tengas:\n"
        f"• Foto del paquete cerrado (folio/cinta intactos)\n"
        f"• Foto del peso en bascula\n"
        f"• Video continuo de apertura (sin cortes)\n"
        f"• Fotos del contenido\n\n"
        f"Cuando termines, usa los botones que te iran apareciendo para enviar a MELI."
    )


def _return_cancel(chat_id, state):
    for cid, rs in (state.get("return_states") or {}).items():
        if rs.get("ret_chat_id") == chat_id and rs.get("active"):
            rs["active"] = False; rs["step"] = "cancelled"
            tg_ret_send(chat_id, f"Cancelado `{cid}`.")
            return
    tg_ret_send(chat_id, "No habia protocolo activo.")


def _return_submit_fraud(token, cid, rs, state):
    """Descargar media de Telegram, subir a MELI claim, mandar mensaje formal."""
    chat_id = rs.get("ret_chat_id")
    atts = rs.get("attachments", [])
    if not atts:
        tg_ret_send(chat_id, "No hay evidencia registrada. Manda al menos una foto o video.")
        return
    tg_ret_send(chat_id, f"⏳ Subiendo {len(atts)} archivos a MELI... esto puede tardar 1-2 min.")
    uploaded_ids = []
    failed = 0
    for i, a in enumerate(atts):
        content, _ = tg_ret_download_file(a["telegram_file_id"])
        if not content:
            failed += 1; continue
        ext = ".jpg" if a["kind"]=="photo" else (".mp4" if a["kind"] in ("video","video_note") else ".bin")
        fname = f"evidencia_{cid}_{i+1}{ext}"
        code, resp = upload_claim_attachment(token, cid, content, fname, a.get("mime","application/octet-stream"))
        if code >= 400:
            _log(f"  upload_attachment err {code}: {resp}")
            failed += 1; continue
        att_id = resp.get("id") or resp.get("attachment_id")
        if att_id:
            a["meli_attachment_id"] = att_id
            uploaded_ids.append(att_id)
        else:
            _log(f"  attachment sin id: {resp}")
            failed += 1
    if not uploaded_ids:
        tg_ret_send(chat_id, f"❌ No pude subir evidencia a MELI ({failed} fallaron). Revisa el log; quizas el endpoint cambió. Te reporto para que lo escales manualmente.")
        tg_send(f"⚠️ *Fallo upload evidencia* claim `{cid}` — {failed} archivos fallaron. Escalamiento manual requerido.")
        return
    # Mensaje formal al mediador
    formal = (
        "Buenas tardes. Al recibir el paquete de devolución del presente reclamo, "
        "documenté íntegramente el estado del mismo conforme al protocolo de custodia y recepción. "
        "Anexo a este mensaje evidencia audiovisual — fotografías y video continuo de la apertura — "
        "que acreditan que el contenido recibido NO corresponde al producto originalmente despachado al comprador. "
        "Con base en lo anterior, solicito respetuosamente a Mercado Libre que se pronuncie a mi favor "
        "en este reclamo y que, en su caso, se retenga el reembolso al comprador hasta concluir la mediación. "
        "Permanezco atento a sus observaciones y quedo a disposición para aportar cualquier evidencia adicional."
    )
    code_m, resp_m = send_claim_message(token, cid, formal, uploaded_ids)
    _log(f"  claim message status={code_m}")
    rs["step"] = "submitted"
    rs["active"] = False
    rs["submitted_at"] = int(time.time())
    tg_ret_send(chat_id,
        f"✅ *Reclamo enviado a MELI*\n\n"
        f"Archivos subidos: {len(uploaded_ids)}\n"
        f"Fallos: {failed}\n"
        f"Mensaje al mediador: `{code_m}`\n\n"
        f"Ahora esperamos respuesta de MELI. Te avisare cualquier cambio en el claim."
    )
    tg_send(f"🛡️ *Evidencia enviada* para claim `{cid}` — {len(uploaded_ids)} archivos + mensaje formal.")
    # Agregar a blocklist al buyer
    _blocklist_add(state, rs.get("buyer_id"), cid, reason="empty_box_or_swap")


def _return_accept(token, cid, rs, state):
    chat_id = rs.get("ret_chat_id")
    rs["step"] = "accepted"
    rs["active"] = False
    tg_ret_send(chat_id, f"✔️ Devolución de `{cid}` aceptada. Sin accion adicional.")
    tg_send(f"✔️ Devolución aceptada para `{cid}` (contenido correcto).")


def _blocklist_add(state, buyer_id, cid, reason):
    if not buyer_id: return
    bl = state.setdefault("buyer_blocklist", {})
    e = bl.setdefault(str(buyer_id), {"events": [], "risk": "NONE"})
    e["events"].append({"ts": int(time.time()), "claim": cid, "reason": reason})
    if len([x for x in e["events"] if x["reason"] in ("empty_box_or_swap",)]) >= 1:
        e["risk"] = "CRITICAL"
    _log(f"  blocklist buyer {buyer_id} risk={e['risk']}")


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

        # Extraer datos de la orden
        amount = 0; product_title = ""; product_item = ""
        try:
            if order_id and str(order_id).isdigit():
                c_ord, ord_data = meli("GET", f"/orders/{order_id}", token)
                amount = float(ord_data.get("total_amount") or 0)
                items = ord_data.get("order_items") or []
                if items:
                    product_title = (items[0].get("item") or {}).get("title", "")
                    product_item = (items[0].get("item") or {}).get("id", "")
        except Exception:
            pass

        # Guardar estado inicial + timestamp creación
        state["claim_states"][cid] = {
            "type": tipo, "stage": stage, "reason": reason, "amount": amount,
            "product_title": product_title, "product_item": product_item,
            "created_at": int(time.time()),
            "last_status": stage,
            "step": "pending_user_action",
        }

        # ARREPENTIMIENTO: SIEMPRE auto-aceptar sin notificar a Telegram
        if tipo == "arrepentimiento":
            _log(f"  auto-arrepentimiento #{cid}")
            try:
                start_playbook(token, cid, tipo, state)
            except Exception as e:
                _log(f"    err: {e}")
            continue

        # DEFECTO o NO_ORIGINAL: registrar en Google Sheets
        if tipo in ("defecto", "no_original"):
            push_to_sheets({
                "claim_id": cid,
                "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
                "month": datetime.utcnow().strftime("%Y-%m"),
                "type": tipo,
                "reason": reason,
                "stage": stage,
                "product_title": product_title,
                "product_item": product_item,
                "amount": amount,
                "order_id": str(order_id),
            })

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
# Auto-replenish stock (stock_config.json)
# ============================================================

STOCK_CONFIG_FILE = "stock_config.json"

def _load_stock_config():
    try:
        with open(STOCK_CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def _save_stock_config(cfg):
    # commit en el repo via git (lo hace el step posterior del workflow);
    # aqui solo escribimos el archivo
    try:
        with open(STOCK_CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        _log(f"  _save_stock_config err: {e}")
        return False

def check_and_replenish_stock(token, state):
    """Detecta items cerrados por venta y los relista desde inventario fisico."""
    cfg = _load_stock_config()
    if not cfg: return
    items = [(k, v) for k, v in cfg.items()
             if not k.startswith("_") and isinstance(v, dict)
             and v.get("auto_replenish") and not v.get("deleted")]
    if not items: return
    _log(f"Auto-replenish: revisando {len(items)} items")
    changed = False
    for item_id, meta in items:
        try:
            code, it = meli("GET", f"/items/{item_id}", token)
            if code != 200:
                _log(f"  {item_id}: GET err {code}"); continue
            stock_meli = it.get("available_quantity", 0)
            status = it.get("status", "")
            sold = it.get("sold_quantity", 0)
            # Si esta activo con stock, dejarlo en paz
            if stock_meli > 0 and status == "active":
                continue
            real = int(meta.get("real_stock", 0))
            if real <= 0:
                _log(f"  {item_id}: sin inventario real, dejo closed")
                continue
            qty = int(meta.get("replenish_quantity", 1))
            qty = min(qty, real)

            if status == "closed" and sold > 0:
                # Item cerrado con venta -> relistar (crea ID nuevo)
                ltype = it.get("listing_type_id") or "gold_pro"
                iprice = it.get("price")
                rbody = {"quantity": qty, "listing_type_id": ltype, "price": iprice,
                         "currency_id": it.get("currency_id","MXN"),
                         "condition": it.get("condition","used")}
                # Si hay seo_title en el stock_config, usarlo en el nuevo listing
                if meta.get("seo_title"):
                    rbody["title"] = meta["seo_title"]
                rcode, rresp = meli("POST", f"/items/{item_id}/relist", token, body=rbody)
                if rcode >= 400:
                    err_msg = (rresp.get("message") or "").lower()
                    if "deleted" in err_msg or rresp.get("error") == "item.status.invalid":
                        # Marcar como deleted y dejar de intentar
                        meta["deleted"] = True
                        meta["_deleted_at"] = int(time.time())
                        meta["_deleted_reason"] = rresp.get("message","")
                        cfg[item_id] = meta
                        changed = True
                        _log(f"  {item_id}: marcado como deleted permanente, no se reintentara")
                        tg_send(
                            f"⚠️ *Item deleted en MELI*\n\n"
                            f"`{item_id}` ({meta.get('label','')}) quedo eliminado permanentemente.\n"
                            f"Stock real restante: {meta.get('real_stock',0)} (sin relist automatico).\n"
                            f"Si queda inventario, publicar manualmente un nuevo item."
                        )
                        continue
                    _log(f"  {item_id}: relist err {rcode} {rresp}")
                    tg_send(f"⚠️ *Auto-replenish falló*\n\n"
                            f"Item `{item_id}` cerrado por venta pero no se pudo relistar.\n"
                            f"Error: `{rresp.get('message','')}`")
                    continue
                new_id = rresp.get("id")
                new_link = rresp.get("permalink")
                if not new_id:
                    _log(f"  {item_id}: relist sin new_id: {rresp}")
                    continue
                # Reescribir descripcion con template seguro (evita triggers anti-spam de MELI)
                try:
                    label = (meta.get("label") or "")
                    title = it.get("title","")
                    if "JBL" in label or "JBL" in title:
                        safe_desc = _safe_jbl_description(title)
                        meli("PUT", f"/items/{new_id}/description", token,
                             body={"plain_text": safe_desc})
                        _log(f"  {new_id}: descripcion safe-template aplicada")
                except Exception as e:
                    _log(f"  {new_id}: safe-desc err: {e}")
                # Migrar entrada en stock_config: borrar viejo, crear nuevo con real-qty
                new_meta = dict(meta)
                new_meta["real_stock"] = real - qty
                new_meta["previous_ids"] = (meta.get("previous_ids") or []) + [item_id]
                cfg[new_id] = new_meta
                cfg.pop(item_id, None)
                changed = True
                sold_before = sold
                _log(f"  {item_id} → {new_id}: relist OK qty={qty}, real restante={new_meta['real_stock']}")
                stats = state.setdefault("daily_stats", {})
                stats["relists"] = stats.get("relists", 0) + 1
                # Solo alertar cuando stock real cae <= 5 (inventario bajo)
                if new_meta['real_stock'] <= 5:
                    tg_send(
                        f"⚠️ *Inventario bajo*\n\n"
                        f"📦 {meta.get('label', item_id)}\n"
                        f"Quedan *{new_meta['real_stock']}* unidades reales.\n"
                        f"Considera reponer inventario fisico pronto."
                    )
            else:
                # Item closed sin ventas, o paused: intentar reactivar con PUT
                body = {"available_quantity": qty, "status": "active"}
                pcode, presp = meli("PUT", f"/items/{item_id}", token, body=body)
                if pcode >= 400:
                    _log(f"  {item_id}: reactivate err {pcode} {presp}")
                    tg_send(f"⚠️ Auto-replenish: no pude reactivar `{item_id}`: {presp.get('message','')}")
                    continue
                meta["real_stock"] = real - qty
                changed = True
                _log(f"  {item_id}: reactivado qty={qty}, real restante={meta['real_stock']}")
                tg_send(
                    f"🔁 *Reposicion automatica (reactivar)*\n\n"
                    f"📦 {meta.get('label', item_id)}\n"
                    f"🆔 `{item_id}`\n"
                    f"Stock MELI: {qty}\n"
                    f"Inventario real restante: {meta['real_stock']}"
                )
        except Exception as e:
            _log(f"  {item_id} auto-replenish err: {e}")
    if changed:
        _save_stock_config(cfg)
        state["_stock_config_dirty"] = True

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




def check_returns(token, state):
    """Escanea claims recientes con reason de devolucion y dispara el playbook."""
    seller_id = state.get("seller_id")
    if not seller_id:
        code, me = meli("GET", "/users/me", token)
        if code == 200:
            seller_id = me.get("id")
            state["seller_id"] = seller_id
    if not seller_id:
        return
    code, resp = meli("GET", f"/post-purchase/v1/claims/search?stage=dispute&limit=20&offset=0", token)
    if code != 200:
        return
    seen = state.setdefault("seen_returns", {})
    for claim in (resp.get("data") or []):
        cid = str(claim.get("id"))
        reason = claim.get("reason_id","")
        if reason not in RETURN_REASONS:
            continue
        if cid in seen:
            continue
        seen[cid] = int(time.time())
        start_return_playbook(token, cid, claim, state)




# ============================================================
# AUTO-Q&A + DAILY REVIEW
# ============================================================

QA_CONFIG_FILE = "qa_templates.json"

def _normalize(s):
    import unicodedata
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s

def _load_qa_templates():
    try:
        with open(QA_CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {"templates": [], "signature": ""}

def _match_template(question_text, templates_cfg):
    qn = _normalize(question_text)
    for t in templates_cfg.get("templates", []):
        for kw in t.get("match", []):
            if _normalize(kw) in qn:
                return t
    return None

def handle_questions(token, state):
    """Escanea preguntas UNANSWERED y responde con templates o notifica a Telegram."""
    cfg = _load_qa_templates()
    if not cfg.get("templates"):
        return
    code, me = meli("GET", "/users/me", token)
    if code != 200: return
    sid = me.get("id")
    code, qr = meli("GET", f"/questions/search?seller_id={sid}&status=UNANSWERED&limit=20", token)
    if code != 200:
        _log(f"  questions search err {code}"); return
    questions = qr.get("questions", []) or []
    if not questions:
        return
    seen_q = state.setdefault("seen_questions", {})
    _log(f"Q&A: {len(questions)} preguntas sin responder")
    sig = cfg.get("signature", "")
    blocklist = state.get("buyer_blocklist", {}) or {}
    for qu in questions:
        qid = str(qu.get("id"))
        item_id = qu.get("item_id")
        qtext = qu.get("text","") or ""
        buyer_id = str((qu.get("from") or {}).get("id",""))
        if qid in seen_q:
            continue
        # Blocklist: si el comprador está en blocklist, NO responder automatico
        bl_entry = blocklist.get(buyer_id)
        if bl_entry and bl_entry.get("risk") not in (None, "NONE"):
            seen_q[qid] = {"answered": False, "template": None, "ts": int(time.time()),
                           "skipped_reason": "buyer_blocklisted"}
            tg_send(
                f"🚨 *PREGUNTA DE COMPRADOR EN BLOCKLIST*\n\n"
                f"Item: `{item_id}`\n"
                f"Comprador: `{buyer_id}` — risk `{bl_entry.get('risk')}`\n"
                f"Motivo: `{(bl_entry.get('events') or [{}])[-1].get('reason','')}`\n\n"
                f"Q: _{qtext[:250]}_\n\n"
                f"⚠️ NO respondi automatico. Ignora o responde manual en MELI. "
                f"Recuerda bloquearlo tambien desde el panel de MELI."
            )
            continue
        matched = _match_template(qtext, cfg)
        if matched:
            answer_text = matched["response"] + sig
            code_a, resp = meli("POST", "/answers", token,
                                body={"question_id": int(qid), "text": answer_text})
            if code_a == 200:
                seen_q[qid] = {"answered": True, "template": matched["id"], "ts": int(time.time())}
                _log(f"  Q&A auto-respondida [{qid}] template={matched['id']}")
                # Contador para daily digest
                stats = state.setdefault("daily_stats", {})
                stats["auto_answered"] = stats.get("auto_answered", 0) + 1
            else:
                _log(f"  Q&A answer err {code_a}: {resp}")
        else:
            seen_q[qid] = {"answered": False, "template": None, "ts": int(time.time())}
            # Notificar a Telegram con botones para responder manual
            tg_send(
                f"❓ *Pregunta sin template*\n\n"
                f"Item: `{item_id}`\n"
                f"Comprador: `{qu.get('from',{}).get('id')}`\n"
                f"Q: _{qtext[:250]}_\n\n"
                f"No hay template que aplique. Responde manualmente en MELI."
            )


def send_review_summary_if_due(token, state):
    """Cada 10 min manda resumen a Telegram con metricas clave."""
    now = int(time.time())
    last = state.get("last_review_at", 0)
    if now - last < 600:  # 10 min
        return
    try:
        code, me = meli("GET", "/users/me", token)
        if code != 200: return
        sid = me.get("id")

        # Items activos del seller
        code2, r = meli("GET", f"/users/{sid}/items/search?status=active&limit=50", token)
        active = r.get("results", []) if code2 == 200 else []

        # Ventas ultimas 24h
        from datetime import datetime, timedelta, timezone
        since = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        code3, o = meli("GET", f"/orders/search?seller={sid}&order.date_created.from={since}&sort=date_desc&limit=50", token)
        orders_24h = o.get("results", []) if code3 == 200 else []
        sales_count = len(orders_24h)
        revenue = sum(float(x.get("total_amount",0)) for x in orders_24h)

        # Preguntas UNANSWERED
        code4, q = meli("GET", f"/questions/search?seller_id={sid}&status=UNANSWERED&limit=50", token)
        pending_q = len(q.get("questions", []) or []) if code4 == 200 else 0

        # Visitas items activos
        total_visits_7d = 0
        for iid in active[:10]:  # limite para no saturar
            code5, v = meli("GET", f"/items/visits/time_window?ids={iid}&last=7&unit=day", token)
            if code5 == 200 and isinstance(v, list) and v:
                total_visits_7d += v[0].get("total_visits", 0)

        # Stock real total
        cfg = _load_stock_config()
        real_stock_total = sum(
            int(v.get("real_stock",0))
            for k,v in cfg.items()
            if not k.startswith("_") and isinstance(v, dict)
        )

        msg = (
            f"📊 *Review 10 min*\n\n"
            f"🟢 Items activos: *{len(active)}*\n"
            f"💰 Ventas 24h: *{sales_count}* (${revenue:,.0f} MXN)\n"
            f"👁️ Visitas 7d: *{total_visits_7d}*\n"
            f"❓ Preguntas pendientes: *{pending_q}*\n"
            f"📦 Stock real bodega: *{real_stock_total}*"
        )
        tg_send(msg)
        state["last_review_at"] = now
        _log(f"Review enviado: ventas24h={sales_count} visitas7d={total_visits_7d} pending_q={pending_q}")
    except Exception as e:
        _log(f"  send_review err: {e}")




def auto_discover_items(token, state):
    """Escanea items del seller; si detecta uno con ventas que NO esta en stock_config, lo agrega."""
    cfg = _load_stock_config()
    if not cfg: return
    # user id del seller
    seller_id = state.get("seller_id")
    if not seller_id:
        code, me = meli("GET", "/users/me", token)
        if code == 200: seller_id = me.get("id"); state["seller_id"] = seller_id
    if not seller_id: return

    # Set de IDs ya conocidos (actuales + previous_ids)
    known = set()
    for k, v in cfg.items():
        if k.startswith("_"): continue
        known.add(k)
        for p in (v.get("previous_ids") or []):
            known.add(p)

    # Items activos + closed del seller
    discovered = []
    for st in ("active","closed"):
        code, r = meli("GET", f"/users/{seller_id}/items/search?status={st}&limit=50", token)
        if code != 200: continue
        for iid in r.get("results", []):
            if iid in known: continue
            code2, it = meli("GET", f"/items/{iid}", token)
            if code2 != 200: continue
            # Solo items con venta O items activos recien creados que tengan seo_title
            if it.get("sold_quantity",0) > 0 or it.get("status") == "active":
                discovered.append(iid)

    if not discovered: return

    _log(f"Auto-discover: {len(discovered)} items sin tracking → agregando a stock_config")
    changed = False
    for iid in discovered:
        code, it = meli("GET", f"/items/{iid}", token)
        if code != 200: continue
        # Adivinar label + SKU
        title = it.get("title","")
        price = it.get("price")
        cfg[iid] = {
            "real_stock": 30,  # conservador
            "sku": f"AUTO-{iid[-6:]}",
            "label": f"{title[:60]} - ${price}",
            "auto_replenish": True,
            "replenish_quantity": 1,
            "seo_title": title,
            "previous_ids": [],
            "_auto_discovered": True,
        }
        changed = True
        _log(f"  + {iid}: {title[:60]}")
        tg_send(
            f"🆕 *Auto-discover*\n\n"
            f"Item `{iid}` agregado a stock_config (no estaba trackeado).\n"
            f"Stock real default: 30 (ajusta manualmente si no es correcto).\n"
            f"Label: {title[:80]}"
        )
    if changed:
        _save_stock_config(cfg)
        state["_stock_config_dirty"] = True




def send_daily_claims_digest(token, state):
    """Envia a Telegram cada dia a las 9am CDMX (15:00 UTC) un resumen de reclamos."""
    import datetime as dt
    now_utc = dt.datetime.now(dt.timezone.utc)
    target_hour_utc = 15  # 9 am CDMX (UTC-6)

    # Clave del dia actual en UTC (YYYY-MM-DD)
    today_key = now_utc.strftime("%Y-%m-%d")
    last_key = state.get("last_daily_digest_key")
    if last_key == today_key:
        return  # ya enviado hoy
    # Solo si ya paso la hora objetivo hoy
    if now_utc.hour < target_hour_utc:
        return

    try:
        code, me = meli("GET", "/users/me", token)
        if code != 200: return
        sid = me.get("id")

        # Claims del seller (todos los estados)
        code, cr = meli("GET", f"/post-purchase/v1/claims/search?limit=50&offset=0", token)
        claims = cr.get("data", []) if code == 200 else []

        # Clasificar
        by_stage = {}
        by_reason = {}
        critical = []  # deadline < 24h
        now_ts = int(now_utc.timestamp())
        for c in claims:
            stage = c.get("stage","?")
            by_stage[stage] = by_stage.get(stage, 0) + 1
            rid = c.get("reason_id","?")
            by_reason[rid] = by_reason.get(rid, 0) + 1
            # deadline
            last_upd = c.get("last_updated") or c.get("date_created","")
            # claim tiene "stage.deadline" en unix ms si esta disponible
            qrem = c.get("quantity_remaining_to_close")
            if isinstance(qrem, int) and qrem > 0 and qrem < 24*3600:
                critical.append(c)

        # Devoluciones en state (return_states)
        ret_states = state.get("return_states", {}) or {}
        ret_active = [k for k,v in ret_states.items() if v.get("step") not in ("submitted","accepted","cancelled")]

        # Ventas últimas 24h
        since = (now_utc - dt.timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        code, o = meli("GET", f"/orders/search?seller={sid}&order.date_created.from={since}&sort=date_desc&limit=50", token)
        sales24 = o.get("results", []) if code == 200 else []
        rev24 = sum(float(x.get("total_amount",0)) for x in sales24)

        # Preguntas pendientes
        code, q = meli("GET", f"/questions/search?seller_id={sid}&status=UNANSWERED&limit=50", token)
        pending_q = len(q.get("questions", []) or []) if code == 200 else 0

        # Armar mensaje
        # Resetear contadores diarios (y capturar los de AYER)
        prev_stats = state.get("daily_stats", {}) or {}
        relists_yday = prev_stats.get("relists", 0)
        auto_ans_yday = prev_stats.get("auto_answered", 0)

        lines = [f"🌅 *Resumen diario {today_key}*", ""]
        lines.append(f"📦 *Ventas 24h*: {len(sales24)} ordenes · ${rev24:,.0f} MXN")
        lines.append(f"🔁 *Relists automaticos 24h*: {relists_yday}")
        lines.append(f"🤖 *Preguntas auto-respondidas 24h*: {auto_ans_yday}")
        lines.append(f"❓ *Preguntas pendientes ahora*: {pending_q}")
        lines.append("")
        lines.append(f"🧾 *Reclamos*: {len(claims)} total")
        if by_stage:
            lines.append("  Por stage:")
            for st, n in sorted(by_stage.items(), key=lambda x:-x[1]):
                lines.append(f"   · {st}: {n}")
        if by_reason:
            top = sorted(by_reason.items(), key=lambda x:-x[1])[:5]
            lines.append("  Top razones:")
            for rid, n in top:
                lines.append(f"   · `{rid}`: {n}")
        if critical:
            lines.append("")
            lines.append(f"🚨 *CRITICOS (<24h deadline)*: {len(critical)}")
            for c in critical[:5]:
                lines.append(f"   · claim `{c.get('id')}` reason={c.get('reason_id','')}")

        lines.append("")
        lines.append(f"📦 *Devoluciones activas*: {len(ret_active)}")
        for cid in ret_active[:5]:
            lines.append(f"   · `{cid}`")

        tg_send("\n".join(lines))
        state["last_daily_digest_key"] = today_key
        state["daily_stats"] = {"relists": 0, "auto_answered": 0}  # reset
        _log(f"Daily digest enviado para {today_key}")
    except Exception as e:
        _log(f"  daily digest err: {e}")


# ============================================================
# Main
# ============================================================


# ============================================================
# CATALOG PRICE WAR - monitor buy_box_winner and undercut
# ============================================================

CATALOG_CONFIG_FILE = "catalog_listings.json"

def _load_catalog_config():
    try:
        with open(CATALOG_CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def _save_catalog_config(cfg):
    try:
        with open(CATALOG_CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        _log(f"  _save_catalog_config err: {e}")
        return False

def catalog_price_war(token, state):
    """Monitorea catalog products y ajusta precio del item vinculado.
    - Si hay buy_box_winner más barato o igual → bajamos $step (no debajo de $floor).
    - Si estamos en floor y seguimos perdiendo → alerta Telegram una sola vez.
    - Si BBW no existe o es más caro que nosotros → no tocamos precio (estamos bien).
    """
    cfg = _load_catalog_config()
    if not cfg:
        return
    changed = False
    for cat_id, meta in list(cfg.items()):
        if not isinstance(meta, dict) or not meta.get("active"):
            continue
        item_id = meta.get("item_id")
        floor = int(meta.get("floor", 120))
        step = int(meta.get("step", 10))
        if not item_id:
            continue
        # Get catalog buy_box_winner
        code, prod = meli("GET", f"/products/{cat_id}", token)
        if code != 200:
            _log(f"  catalog {cat_id}: GET err {code}")
            continue
        bbw = prod.get("buy_box_winner") or {}
        bbw_price = bbw.get("price")
        bbw_item = bbw.get("item_id")
        # Get our item
        code, it = meli("GET", f"/items/{item_id}", token)
        if code != 200:
            _log(f"  item {item_id}: GET err {code}")
            continue
        our_price = int(it.get("price") or 0)
        our_status = it.get("status")
        label = meta.get("label", item_id)
        _log(f"  catalog {cat_id} [{label}]: ours=${our_price} ({our_status}) | BBW=${bbw_price} by item {bbw_item}")
        # We're the winner → nothing to do
        if bbw_item == item_id:
            continue
        # No BBW at all → no competitors, hold price
        if bbw_price is None:
            continue
        # BBW cheaper or equal → we're losing visibility
        if bbw_price <= our_price:
            new_price = our_price - step
            if new_price < floor:
                # At the floor → alert once, don't lower further
                if not meta.get("floor_alerted"):
                    tg_send(
                        f"⚠️ *Catalog floor alcanzado*\n\n"
                        f"`{item_id}` ({label})\n"
                        f"Competidor: ${bbw_price} | Nosotros: ${our_price}\n"
                        f"Floor: ${floor} — no podemos bajar más.\n"
                        f"Ya no somos competitivos en el catálogo."
                    )
                    meta["floor_alerted"] = True
                    cfg[cat_id] = meta
                    changed = True
                continue
            # Apply new price
            code, _r = meli("PUT", f"/items/{item_id}", token, body={"price": new_price})
            if code >= 400:
                _log(f"  {item_id}: PUT price err {code} {_r}")
                continue
            meta["last_price"] = new_price
            meta["last_lowered_at"] = int(time.time())
            meta["floor_alerted"] = False
            cfg[cat_id] = meta
            changed = True
            _log(f"  {item_id}: precio bajado ${our_price} → ${new_price} (competidor ${bbw_price})")
            # Tier notification only at floor or crossing key thresholds
            if new_price == floor:
                tg_send(
                    f"🎯 *Catalog: llegamos al floor*\n\n"
                    f"`{item_id}` ({label}): ahora en ${new_price}\n"
                    f"Competidor: ${bbw_price}"
                )
        # BBW exists and is more expensive → we're winning already, hold
    if changed:
        _save_catalog_config(cfg)



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
        # Orden importante: Q&A PRIMERO para no bloquear por reintentos de relist
        handle_questions(token, state)
        handle_claims(token, state)
        process_telegram_callbacks(token, state)
        advance_pending_playbooks(token, state)
        check_returns(token, state)
        process_returns_bot(token, state)
        check_and_replenish_stock(token, state)
        catalog_price_war(token, state)
        auto_discover_items(token, state)
        track_status_changes(token, state)
        check_overdue_claims(state)
        send_daily_claims_digest(token, state)
    except Exception as e:
        tg_send(f"❌ *Auto-Responder error*\n\n`{e}`")
        _log(f"main err: {e}"); save_json(STATE_FILE, state); sys.exit(1)

    save_json(STATE_FILE, state)
    _log("done")


if __name__ == "__main__":
    main()
