import os, requests, json
from datetime import datetime, timezone, timedelta
from collections import defaultdict

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
    "PDD9943": "no es original",
    "PDD9944": "producto defectuoso/dañado",
    "PNR9501": "no llegó el producto",
    "PDD9945": "producto distinto al publicado",
    "PDD8974": "diferente al pedido",
    "PDD9939": "diferente al publicado",
}

# Yesterday CDMX (2026-04-25)
date_str = os.environ.get("ACCOUNTING_DATE","2026-04-25")
target = datetime.strptime(date_str,"%Y-%m-%d").replace(tzinfo=timezone(timedelta(hours=-6)))
day_start = target.replace(hour=0,minute=0)
day_end = day_start + timedelta(days=1)

print(f"Reclamos creados {date_str} CDMX\n")

total_all = 0
total_affecting = 0
all_claims = []

for label, env_var in ACCOUNTS:
    RT = os.environ.get(env_var,"")
    if not RT: continue
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token",data={
            "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
        }).json()
        H = {"Authorization":f"Bearer {r['access_token']}"}
        me = requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
    except: continue
    
    # Search ALL claims (including closed) for this period
    cs = requests.get(
        f"https://api.mercadolibre.com/post-purchase/v1/claims/search?limit=50",
        headers=H, timeout=15
    ).json()
    claims = cs.get("data") or []
    
    acct_total = 0
    acct_affecting = 0
    for c in claims:
        cd = c.get("date_created","")
        try:
            cdt = datetime.fromisoformat(cd.replace("Z","+00:00"))
            if not (day_start <= cdt < day_end): continue
        except: continue
        
        cid = c.get("id")
        ctype = c.get("type","")
        rels = c.get("related_entities",[]) or []
        rid = c.get("reason_id","")
        # Get full detail
        try:
            full = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{cid}",headers=H,timeout=10).json()
            ctype = full.get("type",ctype)
            rels = full.get("related_entities",rels)
        except: pass
        
        affects = not (ctype == "mediations" and "return" in rels)
        acct_total += 1
        if affects: acct_affecting += 1
        
        all_claims.append({
            "label":label,"cid":cid,"type":ctype,"reason":REASON_LABELS.get(rid,rid),
            "rels":rels,"affects":affects,"order":c.get("resource_id",""),
            "status":c.get("status","")
        })
    
    if acct_total > 0:
        print(f"  {label}: {acct_total} reclamos ({acct_affecting} afectan reputación)")
    total_all += acct_total
    total_affecting += acct_affecting

print(f"\n{'='*50}")
print(f"📊 TOTAL {date_str}: {total_all} reclamos")
print(f"   ⚠️  Afectan reputación: {total_affecting}")
print(f"   ✅ NO afectan: {total_all - total_affecting}")
print(f"{'='*50}\n")

# Detail
print("DETALLE:")
for c in all_claims:
    flag = "🚨" if c["affects"] else "⊘"
    print(f"  {flag} [{c['label']}] {c['cid']} | type={c['type']} | reason={c['reason']} | orden={c['order']} | status={c['status']}")
    
# Send to Telegram
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN","")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID","")
if TG_TOKEN and TG_CHAT:
    lines = [f"📊 *Reclamos {date_str}*\n"]
    lines.append(f"Total: *{total_all}* reclamos")
    lines.append(f"⚠️ Afectan reputación: *{total_affecting}*")
    lines.append(f"✅ NO afectan: {total_all - total_affecting}\n")
    if all_claims:
        for c in all_claims[:10]:
            flag = "🚨" if c["affects"] else "⊘"
            lines.append(f"{flag} `{c['cid']}` [{c['label']}] {c['reason']}")
    msg = "\n".join(lines)
    r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      json={"chat_id":TG_CHAT,"text":msg[:4000],"parse_mode":"Markdown"})
    print(f"\nTelegram: {r.status_code}")
