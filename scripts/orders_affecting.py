import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]

ACCOUNTS = [
    ("JUAN", "MELI_REFRESH_TOKEN"),
    ("CLARIBEL", "MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA", "MELI_REFRESH_TOKEN_ASVA"),
]

# Claims que afectan reputación (de mi último análisis)
CLAIMS_AFFECTING = {
    "JUAN": ["5503148321", "5503227787", "5503287582", "5503293842",
             "5502933251", "5502636400"],  # también incluye los abiertos previos que afectan
}

REASON_LABELS = {"PDD9943":"no es original","PDD9944":"defectuoso","PDD9945":"distinto al publicado","PDD9946":"otro","PDD9950":"otro","PNR9501":"no llegó","PDD9939":"diferente al publicado"}

print(f"📋 ÓRDENES con reclamo que AFECTA reputación:\n")

for label, env in ACCOUNTS:
    RT = os.environ.get(env,"")
    if not RT: continue
    if label not in CLAIMS_AFFECTING: continue
    
    r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
    H = {"Authorization":f"Bearer {r['access_token']}"}
    
    print(f"━━━ {label} ━━━")
    for cid in CLAIMS_AFFECTING[label]:
        try:
            c = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{cid}",headers=H,timeout=10).json()
            order_id = c.get("resource_id","?")
            ctype = c.get("type","")
            rid = c.get("reason_id","")
            reason = REASON_LABELS.get(rid, rid)
            status = c.get("status","")
            stage = c.get("stage","")
            rels = c.get("related_entities",[]) or []
            cd = c.get("date_created","")[:10]
            
            # Get buyer + product from order
            ord_data = requests.get(f"https://api.mercadolibre.com/orders/{order_id}",headers=H,timeout=10).json()
            buyer = ord_data.get("buyer",{}).get("nickname","?")
            amt = ord_data.get("total_amount","?")
            items_o = ord_data.get("order_items",[])
            product = items_o[0].get("item",{}).get("title","?")[:50] if items_o else "?"
            
            # Re-confirm afecta
            affects = ctype != "cancel_purchase" and not (ctype == "mediations" and "return" in rels)
            flag = "🚨" if affects else "⊘"
            
            print(f"\n  {flag} ORDEN: {order_id}")
            print(f"     Claim: {cid} | type={ctype} | stage={stage} | status={status}")
            print(f"     Producto: {product}")
            print(f"     Comprador: {buyer} | ${amt}")
            print(f"     Motivo: {reason} ({rid})")
            print(f"     Fecha: {cd}")
        except Exception as e:
            print(f"  err {cid}: {e}")
    print()

# Send to Telegram
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN","")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID","")
if TG_TOKEN and TG_CHAT:
    lines = ["🚨 *Órdenes con reclamo que afectan reputación*\n"]
    
    # Re-build ordered  
    for label, env in ACCOUNTS:
        if label not in CLAIMS_AFFECTING: continue
        RT = os.environ.get(env,"")
        if not RT: continue
        r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
        H = {"Authorization":f"Bearer {r['access_token']}"}
        
        affecting_for_acct = []
        for cid in CLAIMS_AFFECTING[label]:
            c = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{cid}",headers=H,timeout=10).json()
            ctype = c.get("type",""); rels = c.get("related_entities",[]) or []
            affects = ctype != "cancel_purchase" and not (ctype == "mediations" and "return" in rels)
            if not affects: continue
            order_id = c.get("resource_id","?")
            rid = c.get("reason_id","")
            reason = REASON_LABELS.get(rid, rid)
            status = c.get("status","")
            cd = c.get("date_created","")[:10]
            affecting_for_acct.append((order_id, cid, reason, status, cd))
        
        if affecting_for_acct:
            lines.append(f"\n*━━━ {label} ({len(affecting_for_acct)}) ━━━*")
            for oid, cid, rsn, sta, fch in affecting_for_acct:
                lines.append(f"🚨 Orden `{oid}`")
                lines.append(f"  Claim `{cid}` — {rsn} — {sta} — {fch}")
    
    msg = "\n".join(lines)
    r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      json={"chat_id":TG_CHAT,"text":msg[:4000],"parse_mode":"Markdown"})
    print(f"Telegram: {r.status_code}")
