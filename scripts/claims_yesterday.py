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

REASON_LABELS = {
    "PDD9943":"no es original","PDD9944":"defectuoso/dañado","PNR9501":"no llegó",
    "PDD9945":"distinto al publicado","PDD8974":"diferente al pedido",
    "PDD9939":"diferente al publicado","PDD8975":"incompleto","PDD8973":"no le gustó",
    "PDR9526":"no recibió",
}

date_str = os.environ.get("ACCOUNTING_DATE","2026-04-25")
target = datetime.strptime(date_str,"%Y-%m-%d").replace(tzinfo=timezone(timedelta(hours=-6)))
day_start = target.replace(hour=0,minute=0)
day_end = day_start + timedelta(days=1)

# CDMX bounds
print(f"Buscando reclamos creados en {date_str} CDMX")
print(f"  CDMX bounds: {day_start.isoformat()} → {day_end.isoformat()}")

total_all = 0; total_aff = 0; all_c = []
for label, env in ACCOUNTS:
    RT = os.environ.get(env,"")
    if not RT: continue
    r = requests.post("https://api.mercadolibre.com/oauth/token",data={
        "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
    }).json()
    H = {"Authorization":f"Bearer {r['access_token']}"}
    me = requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    
    # Iterate all pages of claims (without status filter — get ALL)
    acct_claims = []
    offset = 0
    while True:
        # Use sort by date_created desc to walk all
        url = f"https://api.mercadolibre.com/post-purchase/v1/claims/search?limit=50&offset={offset}&sort=date_created,desc"
        cs = requests.get(url, headers=H, timeout=20).json()
        data = cs.get("data") or []
        if not data: break
        all_done = True
        for c in data:
            cd = c.get("date_created","")
            try:
                cdt = datetime.fromisoformat(cd.replace("Z","+00:00"))
            except: continue
            if cdt < day_start:
                # We're past yesterday — stop pagination
                continue
            if cdt >= day_end:
                # Future of yesterday — keep iterating
                all_done = False
                continue
            # Match yesterday
            all_done = False
            acct_claims.append(c)
        # If oldest in this batch is before day_start, stop
        try:
            oldest = data[-1].get("date_created","")
            oldest_dt = datetime.fromisoformat(oldest.replace("Z","+00:00"))
            if oldest_dt < day_start: break
        except: break
        offset += 50
        if offset >= 500: break  # safety
    
    print(f"\n=== {label} ({me.get('nickname')}): {len(acct_claims)} reclamos ayer ===")
    for c in acct_claims:
        cid = c.get("id")
        ctype = c.get("type",""); rid = c.get("reason_id","")
        rels = c.get("related_entities",[]) or []
        # Detail
        try:
            full = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{cid}",headers=H,timeout=10).json()
            ctype = full.get("type",ctype); rels = full.get("related_entities",rels)
        except: pass
        affects = not (ctype == "mediations" and "return" in rels)
        all_c.append({"label":label,"cid":cid,"type":ctype,"reason":REASON_LABELS.get(rid,rid),"rels":rels,"affects":affects,"order":c.get("resource_id",""),"status":c.get("status",""),"date":c.get("date_created","")})
        if affects: total_aff += 1
        flag = "🚨" if affects else "⊘"
        print(f"  {flag} {cid} | type={ctype} | reason={REASON_LABELS.get(rid,rid)} | status={c.get('status')} | {c.get('date_created','')}")
    total_all += len(acct_claims)

print(f"\n{'='*55}")
print(f"📊 TOTAL {date_str}: {total_all} reclamos creados")
print(f"   ⚠️ Afectan reputación: {total_aff}")
print(f"   ⊘ Excluidos: {total_all - total_aff}")
print(f"{'='*55}")

# Telegram
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN","")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID","")
if TG_TOKEN and TG_CHAT:
    lines = [f"📊 *Reclamos {date_str}*\n", f"Total: *{total_all}* | ⚠️ Afectan: *{total_aff}* | ⊘ Excluidos: {total_all-total_aff}\n"]
    for c in all_c[:15]:
        flag = "🚨" if c["affects"] else "⊘"
        lines.append(f"{flag} `{c['cid']}` [{c['label']}] {c['type']} {c['reason']} status={c['status']}")
    msg = "\n".join(lines)
    r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      json={"chat_id":TG_CHAT,"text":msg[:4000],"parse_mode":"Markdown"})
    print(f"\nTelegram: {r.status_code}")
