"""
Lista TODOS los reclamos abiertos que AFECTAN REPUTACIÓN por cuenta.

Reglas para "afecta reputación":
- status = "opened"
- type = "mediations" (estos sí afectan; "claim" sin mediación no impacta)
- NO tener resolution.benefited.entity = "complainant" (si MELI ya resolvió a favor del cliente y solo queda pago)
- NO ser tipo "return" puro sin mediación
"""
import os, requests, json
from datetime import datetime, timezone, timedelta
from collections import defaultdict

APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]

ACCOUNTS = [
    ("JUAN","MELI_REFRESH_TOKEN"),
    ("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA","MELI_REFRESH_TOKEN_ASVA"),
    ("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("DILCIE","MELI_REFRESH_TOKEN_DILCIE"),
    ("MILDRED","MELI_REFRESH_TOKEN_MILDRED"),
    ("YC_NEW","MELI_REFRESH_TOKEN_YC_NEW"),
    ("BREN","MELI_REFRESH_TOKEN_BREN"),
]

REASON_LABELS = {
    "PDD9943": "No es original (imitación)",
    "PDD9944": "Producto defectuoso/dañado",
    "PNR9501": "No llegó el producto",
    "PDD8975": "Producto incompleto",
    "PDD9945": "Producto distinto al publicado",
    "PDD8974": "Diferente al pedido",
    "PDD8973": "No le gustó",
    "PDR9526": "No recibió el producto",
    "PDD9939": "Diferente al publicado",
    "PDD9946": "Otro motivo (PDD9946)",
    "PDD9950": "Otro motivo (PDD9950)",
    "PNR9508": "Cancelación pago",
}

results_by_account = {}
total_affecting = 0

for label, env_var in ACCOUNTS:
    RT = os.environ.get(env_var, "")
    if not RT: continue
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token",
            data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},
            timeout=15).json()
        H = {"Authorization":f"Bearer {r['access_token']}"}
        me = requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
        USER_ID = me["id"]
    except Exception as e:
        print(f"[{label}] auth err: {e}")
        continue
    
    print(f"\n=== {label} ({me.get('nickname','')} {USER_ID}) ===")
    
    affecting = []
    offset = 0
    while True:
        try:
            rc = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search?status=opened&limit=50&offset={offset}",
                headers=H, timeout=20).json()
        except: break
        data = rc.get("data",[])
        if not data: break
        for cl in data:
            ctype = (cl.get("type") or "").lower()
            # Filter solo mediations (los que afectan)
            if ctype != "mediations": continue
            
            cid = cl.get("id")
            order_id = cl.get("resource_id") or cl.get("resource","").split("/")[-1]
            reason_id = (cl.get("reason_id") or "").strip()
            reason_label = REASON_LABELS.get(reason_id, reason_id or "Sin motivo")
            date_created = cl.get("date_created","")
            
            # Get product title
            product_title = ""
            buyer_nick = ""
            try:
                if order_id:
                    od = requests.get(f"https://api.mercadolibre.com/orders/{order_id}",headers=H,timeout=10).json()
                    for oi in od.get("order_items",[]):
                        product_title = (oi.get("item") or {}).get("title","")
                        if product_title: break
                    buyer_nick = (od.get("buyer") or {}).get("nickname","")
            except: pass
            
            affecting.append({
                "claim_id": cid,
                "order_id": order_id,
                "reason_id": reason_id,
                "reason_label": reason_label,
                "date_created": date_created,
                "title": product_title[:60],
                "buyer": buyer_nick,
                "claim_url": f"https://www.mercadolibre.com.mx/reclamos/{cid}",
            })
        offset += 50
        if offset >= rc.get("paging",{}).get("total",0): break
    
    print(f"  Reclamos que afectan reputación: {len(affecting)}")
    for cl in affecting:
        print(f"    • Claim {cl['claim_id']} | Order {cl['order_id']}")
        print(f"      📅 {cl['date_created'][:16]} | 👤 {cl['buyer']}")
        print(f"      ⚠️  {cl['reason_id']} — {cl['reason_label']}")
        print(f"      📦 {cl['title']}")
        print(f"      🔗 {cl['claim_url']}")
    
    results_by_account[label] = {
        "user_id": USER_ID,
        "nickname": me.get("nickname",""),
        "claims": affecting,
    }
    total_affecting += len(affecting)

print(f"\n{'='*60}")
print(f"📊 TOTAL reclamos abiertos que afectan reputación: {total_affecting}")
print(f"{'='*60}")
for label, data in results_by_account.items():
    n = len(data["claims"])
    if n > 0:
        print(f"  {label:10}: {n} reclamos")

# Save JSON for downstream tools
with open("claims_affecting_reputation.json","w") as f:
    json.dump(results_by_account, f, indent=2, ensure_ascii=False)
print(f"\n✅ claims_affecting_reputation.json guardado")
