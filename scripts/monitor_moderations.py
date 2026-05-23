#!/usr/bin/env python3
"""Detecta items moderados/suspendidos por MELI y avisa por Telegram.

Estrategia:
- Por cada cuenta (refresh_token en env), obtener user_id
- Listar items con status in ('paused','under_review','closed')
- Filtrar los que tengan sub_status indicando MODERACIÓN MELI
  (no las pausas que YO mismo hice ni las baja por stock=0)
- Comparar contra state file data/moderations_seen.json
- Por cada NUEVO item moderado → mandar TG con cuenta, item_id, título,
  motivo y link

Cron cada 15 minutos.
"""
import os, sys, json, time
from pathlib import Path
import requests
import meli_token

APP_ID     = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
TG_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
TG_CHAT    = os.environ["TELEGRAM_CHAT_ID"]

ACCOUNTS = {
    "JUAN":     os.environ.get("MELI_REFRESH_TOKEN"),
    "CLARIBEL": os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "ASVA":     os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "RAYMUNDO": os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
    "DILCIE":   os.environ.get("MELI_REFRESH_TOKEN_DILCIE"),
    "MILDRED":  os.environ.get("MELI_REFRESH_TOKEN_MILDRED"),
    "BREN":     os.environ.get("MELI_REFRESH_TOKEN_BREN"),
    "WILBERT":  os.environ.get("MELI_REFRESH_TOKEN_WILBERT"),
    "YC_NEW":   os.environ.get("MELI_REFRESH_TOKEN_YC_NEW"),
}

# Sub-status que indican MODERACIÓN por MELI (NO pausas mías ni stock=0)
# Ref: https://developers.mercadolibre.com.mx/es_ar/condiciones-y-codigos-de-error
MODERATION_SUBSTATUS = {
    "moderated",                   # Pausada por moderador MELI
    "freeze",                      # Congelada
    "freezed_by_anti_fraud",       # Anti-fraude
    "warning_sub_status",          # Aviso MELI
    "intervention_pause",          # Intervención
    "warning",                     # Genérico
    "moderation_pause",            # Otra forma
    "blocked_by_buyer",            # Reclamo
    "deleted_by_listing_provider", # MELI lo borró
    "infringement",                # Infracción IP
    "out_of_stock_pending",        # Edge case
}

STATE_FILE = Path("data/moderations_seen.json")
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}

def save_state(s):
    STATE_FILE.write_text(json.dumps(s, indent=2, ensure_ascii=False))

def refresh(rt):
    r = meli_token.refresh(rt)
    r.raise_for_status()
    return r.json()["access_token"]

def me(tok):
    return requests.get("https://api.mercadolibre.com/users/me",
                        headers={"Authorization": f"Bearer {tok}"}, timeout=20).json()

def list_items(tok, user_id, status):
    """Lista TODOS los item_ids con un status dado (paginado)."""
    items = []
    offset = 0
    while True:
        r = requests.get(
            f"https://api.mercadolibre.com/users/{user_id}/items/search",
            headers={"Authorization": f"Bearer {tok}"},
            params={"status": status, "limit": 100, "offset": offset},
            timeout=30,
        )
        if r.status_code >= 400:
            print(f"   ! search status={status} err {r.status_code}: {r.text[:120]}")
            break
        d = r.json()
        results = d.get("results", [])
        items.extend(results)
        total = d.get("paging", {}).get("total", 0)
        offset += len(results)
        if not results or offset >= total or offset >= 1000:
            break
    return items

def get_item(tok, iid):
    r = requests.get(f"https://api.mercadolibre.com/items/{iid}",
                     headers={"Authorization": f"Bearer {tok}"},
                     params={"attributes": "id,title,status,sub_status,permalink,seller_custom_field"},
                     timeout=20)
    if r.status_code >= 400:
        return None
    return r.json()

def tg_send(text):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": TG_CHAT, "parse_mode": "HTML", "text": text,
                  "disable_web_page_preview": "true"},
            timeout=20,
        )
        return r.status_code == 200
    except Exception as e:
        print(f"  TG err: {e}")
        return False

def main():
    state = load_state()
    new_alerts = []

    for nick, rt in ACCOUNTS.items():
        if not rt:
            continue
        try:
            tok = refresh(rt)
            user = me(tok)
            uid = user.get("id")
            print(f"\n=== {nick} (uid={uid}) ===")
        except Exception as e:
            print(f"  {nick}: refresh fallo → {e}")
            continue

        # Recolectar items con status sospechoso
        suspicious_ids = set()
        for status in ("paused", "under_review", "closed"):
            ids = list_items(tok, uid, status)
            print(f"  {status}: {len(ids)} items")
            suspicious_ids.update(ids)

        # Inspeccionar cada uno
        seen_account = state.setdefault(nick, {})
        for iid in suspicious_ids:
            it = get_item(tok, iid)
            if not it:
                continue
            sub = set(it.get("sub_status") or [])
            status = it.get("status")

            # Heurística: alerta SOLO si sub_status indica moderación
            # O si está under_review (siempre es MELI)
            is_moderated = bool(sub & MODERATION_SUBSTATUS) or status == "under_review"
            if not is_moderated:
                continue

            reason = ", ".join(sorted(sub & MODERATION_SUBSTATUS)) or status

            # Dedupe: ya alertamos este (item_id, reason)?
            key = f"{iid}::{reason}"
            if key in seen_account:
                continue

            title = it.get("title", "(sin título)")
            link = it.get("permalink", f"https://articulo.mercadolibre.com.mx/{iid}")

            new_alerts.append({
                "cuenta": nick,
                "item_id": iid,
                "title": title,
                "status": status,
                "reason": reason,
                "link": link,
            })
            seen_account[key] = int(time.time())
            print(f"  🚨 NEW MOD: {iid} {status}/{reason} — {title[:60]}")

    save_state(state)

    if not new_alerts:
        print("\n✅ Sin moderaciones nuevas")
        return

    # Mandar 1 mensaje por alerta (más legible)
    for a in new_alerts:
        msg = (
            f"🚨 <b>PUBLICACIÓN SUSPENDIDA POR MELI</b>\n\n"
            f"<b>Cuenta:</b> {a['cuenta']}\n"
            f"<b>Item:</b> <code>{a['item_id']}</code>\n"
            f"<b>Título:</b> {a['title'][:120]}\n"
            f"<b>Estado:</b> {a['status']}\n"
            f"<b>Motivo:</b> {a['reason']}\n\n"
            f"<a href=\"{a['link']}\">Ver en MELI</a>"
        )
        tg_send(msg)
        time.sleep(0.5)

    print(f"\n📨 Telegram: {len(new_alerts)} alerta(s) enviadas")

if __name__ == "__main__":
    main()
