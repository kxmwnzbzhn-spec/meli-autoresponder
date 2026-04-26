import os, requests, json
from datetime import datetime, timezone, timedelta

APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]

ACCOUNTS = [
    ("JUAN", "MELI_REFRESH_TOKEN"),
    ("CLARIBEL", "MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA", "MELI_REFRESH_TOKEN_ASVA"),
    ("RAYMUNDO", "MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("DILCIE", "MELI_REFRESH_TOKEN_DILCIE"),
    ("MILDRED", "MELI_REFRESH_TOKEN_MILDRED"),
]

REASON_LABELS = {"PDD9943":"no es original","PDD9944":"defectuoso","PNR9501":"no llegó",
                 "PDD9945":"distinto al publicado","PDD8974":"diferente","PDD9939":"diferente al publicado"}

date_str = os.environ.get("ACCOUNTING_DATE","2026-04-25")
target = datetime.strptime(date_str,"%Y-%m-%d").replace(tzinfo=timezone(timedelta(hours=-6)))
day_start = target.replace(hour=0,minute=0)
day_end = day_start + timedelta(days=1)

print(f"Reclamos creados {date_str} CDMX\n")

all_c = []
for label, env in ACCOUNTS:
    RT = os.environ.get(env,""); 
    if not RT: continue
    r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
    H = {"Authorization":f"Bearer {r['access_token']}"}
    me = requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    
    # Search BOTH opened AND closed (API requires status filter)
    for st_filter in ("opened","closed"):
        offset = 0
        while True:
            url = f"https://api.mercadolibre.com/post-purchase/v1/claims/search?limit=50&offset={offset}&status={st_filter}"
            cs = requests.get(url, headers=H, timeout=20).json()
            data = cs.get("data") or []
            if not data: break
            for c in data:
                cd = c.get("date_created","")
                try: cdt = datetime.fromisoformat(cd.replace("Z","+00:00"))
                except: continue
                if cdt < day_start: continue  # past yesterday — but keep walking older ones in same page
                if cdt >= day_end: continue   # future
                all_c.append({"label":label,"data":c,"H":H,"date":cdt})
            # Stop if oldest in this page is before day_start
            try:
                oldest = data[-1].get("date_created","")
                if datetime.fromisoformat(oldest.replace("Z","+00:00")) < day_start: break
            except: break
            offset += 50
            if offset >= 500: break

print(f"Total reclamos ayer: {len(all_c)}\n")

# Detalle + classify
total_aff = 0; total_excl = 0
for ent in sorted(all_c, key=lambda x: (x["label"], x["date"])):
    c = ent["data"]; H = ent["H"]
    cid = c.get("id"); ctype = c.get("type",""); rid = c.get("reason_id","")
    rels = c.get("related_entities",[]) or []; status = c.get("status","")
    try:
        full = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{cid}",headers=H,timeout=10).json()
        ctype = full.get("type",ctype); rels = full.get("related_entities",rels)
    except: pass
    
    # Determinar si afecta:
    # - cancel_purchase (closed) → no afecta
    # - mediations + return → no afecta  
    # - returns → afecta
    # - mediations sin return → afecta
    affects = False
    if ctype == "cancel_purchase":
        affects = False  # solo cancel
    elif ctype == "mediations" and "return" in rels:
        affects = False  # excluido por return entity
    else:
        affects = True
    
    if affects: total_aff += 1
    else: total_excl += 1
    flag = "🚨" if affects else "⊘"
    reason = REASON_LABELS.get(rid, rid) if rid else "-"
    print(f"  {flag} [{ent['label']}] {cid} | {ctype:<15} | status={status:<8} | reason={reason} | {ent['date'].strftime('%H:%M')}")

print(f"\n{'='*55}")
print(f"📊 TOTAL {date_str}: {len(all_c)} reclamos creados")
print(f"   ⚠️  Afectan reputación: {total_aff}")
print(f"   ⊘ NO afectan (cancel/return excluido): {total_excl}")
print(f"{'='*55}")

# Telegram
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN","")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID","")
if TG_TOKEN and TG_CHAT:
    lines = [f"📊 *Reclamos {date_str}*\n"]
    lines.append(f"Total: *{len(all_c)}*")
    lines.append(f"⚠️ Afectan reputación: *{total_aff}*")
    lines.append(f"⊘ NO afectan: *{total_excl}*\n")
    
    affecting_list = [(e,c) for c,e in [(x["data"],x) for x in all_c]]
    by_acct = {}
    for ent in all_c:
        c = ent["data"]
        ctype = c.get("type","")
        rels = c.get("related_entities",[]) or []
        affects = ctype != "cancel_purchase" and not (ctype == "mediations" and "return" in rels)
        if affects:
            by_acct.setdefault(ent["label"],[]).append((c.get("id"), ctype, REASON_LABELS.get(c.get("reason_id",""), c.get("reason_id","")), ent["date"].strftime("%H:%M"), c.get("status","")))
    
    if by_acct:
        lines.append("*━━━ AFECTAN REPUTACIÓN ━━━*")
        for acct, claims in by_acct.items():
            lines.append(f"\n*{acct}* ({len(claims)})")
            for cid, ct, rsn, hr, sta in claims:
                lines.append(f"🚨 `{cid}` {ct} — {rsn} | {hr} | {sta}")
    
    msg = "\n".join(lines)
    r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      json={"chat_id":TG_CHAT,"text":msg[:4000],"parse_mode":"Markdown"})
    print(f"\nTelegram: {r.status_code}")
