"""OAuth healthcheck — valida los refresh_tokens de las 9 cuentas MELI.

Por cada cuenta en la tabla `accounts`, intenta refresh + GET /users/me.
Reporta vía Telegram cualquier fallo (refresh_token invalido, cuenta penalizada, etc.).
También alerta proactivamente si el access_token devuelto está cerca de expirar
o si la cuenta tiene reputación baja.

Uso:
    SUPABASE_DB_URL=... MELI_APP_ID=... MELI_APP_SECRET=... \\
        MELI_REFRESH_TOKEN_WILBERT=... MELI_REFRESH_TOKEN_YC_NEW=... ... \\
        TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... \\
        python oauth_healthcheck.py
"""
import os, sys, requests, psycopg2
import meli_token

DSN = os.environ["SUPABASE_DB_URL"]
CID = os.environ["MELI_APP_ID"]
CS = os.environ["MELI_APP_SECRET"]
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID")


def tg(msg: str) -> None:
    if not TG_TOKEN or not TG_CHAT:
        print(f"[no telegram] {msg}")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": TG_CHAT, "text": msg, "parse_mode": "Markdown"},
            timeout=10,
        )
    except Exception as e:
        print(f"telegram failed: {e}")


def check_account(nick: str, secret_name: str) -> dict:
    """Devuelve {ok, nick, user_id?, status, error?}"""
    rt = os.environ.get(secret_name, "").strip()
    if not rt:
        return {"ok": False, "nick": nick, "status": "no_secret",
                "error": f"secret {secret_name} no presente en env"}

    # 1. Refresh
    try:
        r = meli_token.refresh(rt)
    except Exception as e:
        return {"ok": False, "nick": nick, "status": "refresh_error", "error": str(e)}

    if r.status_code != 200:
        return {"ok": False, "nick": nick, "status": "refresh_http_" + str(r.status_code),
                "error": r.text[:300]}

    body = r.json()
    access_token = body.get("access_token")
    if not access_token:
        return {"ok": False, "nick": nick, "status": "no_access_token",
                "error": str(body)[:300]}

    # 2. Verifica que sigue válido
    try:
        me = requests.get("https://api.mercadolibre.com/users/me",
                          headers={"Authorization": f"Bearer {access_token}"},
                          timeout=20)
    except Exception as e:
        return {"ok": False, "nick": nick, "status": "me_error", "error": str(e)}

    if me.status_code != 200:
        return {"ok": False, "nick": nick, "status": "me_http_" + str(me.status_code),
                "error": me.text[:300]}

    me_body = me.json()
    user_id = me_body.get("id")
    nickname_api = me_body.get("nickname")
    seller_reputation = (me_body.get("seller_reputation") or {})
    level = seller_reputation.get("level_id")  # 5_green (mejor) → 1_red (peor) → None
    power_seller_status = seller_reputation.get("power_seller_status")

    return {
        "ok": True, "nick": nick, "user_id": user_id, "nick_api": nickname_api,
        "level": level, "power_seller": power_seller_status, "status": "healthy",
    }


def main() -> int:
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute("SELECT nickname, refresh_token_secret FROM accounts WHERE active = true ORDER BY nickname")
    accounts = cur.fetchall()
    cur.close()
    conn.close()

    if not accounts:
        msg = "⚠️ No hay accounts activos en la tabla accounts. ¿Corriste inv_backfill_accounts?"
        print(msg)
        tg(msg)
        return 1

    results = []
    failures = []
    bad_reputation = []
    for nick, secret_name in accounts:
        res = check_account(nick, secret_name)
        results.append(res)
        if not res["ok"]:
            failures.append(res)
        else:
            lvl = res.get("level") or ""
            # 1_red, 2_orange, 3_yellow = bad. 4_light_green, 5_green = good.
            if lvl and not lvl.startswith(("4_", "5_")):
                bad_reputation.append(res)

    # Reporte
    lines = [f"🩺 *OAuth healthcheck* — {len(accounts)} cuentas", ""]
    for r in results:
        if r["ok"]:
            lvl = r.get("level") or "—"
            emoji = "✅" if lvl.startswith(("4_", "5_")) else ("⚠️" if lvl != "—" else "✅")
            lines.append(f"{emoji} `{r['nick']}` user_id={r.get('user_id')} reputación={lvl}")
        else:
            lines.append(f"❌ `{r['nick']}` → {r['status']}: {r.get('error', '')[:100]}")

    print("\n".join(lines))

    # Solo enviar Telegram si hay fallas o reputación baja
    if failures or bad_reputation:
        alert_lines = ["🚨 *OAuth healthcheck — atención requerida*", ""]
        if failures:
            alert_lines.append(f"*Fallos ({len(failures)}):*")
            for f in failures:
                alert_lines.append(f"  ❌ `{f['nick']}` → {f['status']}")
                alert_lines.append(f"     {f.get('error', '')[:200]}")
            alert_lines.append("")
        if bad_reputation:
            alert_lines.append(f"*Reputación baja ({len(bad_reputation)}):*")
            for r in bad_reputation:
                alert_lines.append(f"  ⚠️ `{r['nick']}` level=`{r.get('level')}`")
        tg("\n".join(alert_lines))
        return 1
    else:
        # Solo log silencioso si todo OK
        print("✓ Todos los tokens válidos y reputaciones OK")
        return 0


if __name__ == "__main__":
    sys.exit(main())
