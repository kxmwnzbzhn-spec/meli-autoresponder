import os,requests,json,time
from datetime import datetime

ACCOUNTS={
    "JUAN":os.environ.get("MELI_REFRESH_TOKEN"),
    "CLARIBEL":os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "ASVA":os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "RAYMUNDO":os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
    "DILCIE":os.environ.get("MELI_REFRESH_TOKEN_DILCIE"),
    "MILDRED":os.environ.get("MELI_REFRESH_TOKEN_MILDRED"),
}

REASON_LABELS={
    "PDD9943":"Producto no como descrito (incluye 'no es original')",
    "PDD9944":"Producto no coincide con publicacion",
    "PDD9955":"Defecto de fabrica",
    "PDD9977":"Falta accesorios/incompletos",
    "PNR9501":"Comprador no recibio (sin stock)",
    "PNR9503":"Comprador no recibio (envio retrasado)",
    "PNR9504":"Comprador no recibio (entrega fallida)",
    "PNR9508":"Comprador no recibio (sin stock declarado)",
}

TG_TOKEN=os.environ["TELEGRAM_BOT_TOKEN"]
TG_CHAT=os.environ["TELEGRAM_CHAT_ID"]

all_claims=[]
total_count=0

for label,rt in ACCOUNTS.items():
    if not rt: continue
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt}).json()
    if "access_token" not in r: continue
    H={"Authorization":f"Bearer {r['access_token']}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    nick=me.get("nickname","")
    
    # Open claims
    s=requests.get("https://api.mercadolibre.com/post-purchase/v1/claims/search?status=opened&limit=50",headers=H,timeout=15).json()
    claims=s.get("data") or []
    if not claims: continue
    
    for c in claims:
        cid=c.get("id")
        reason=c.get("reason_id","")
        stage=c.get("stage","")
        order_id=c.get("resource_id")
        product_title=""
        try:
            o=requests.get(f"https://api.mercadolibre.com/orders/{order_id}",headers=H,timeout=10).json()
            items=o.get("order_items") or []
            if items:
                product_title=(items[0].get("item") or {}).get("title","")[:50]
        except: pass
        
        all_claims.append({
            "account":label,"nickname":nick,
            "claim_id":cid,"order_id":order_id,
            "product":product_title,"reason":reason,
            "reason_label":REASON_LABELS.get(reason,reason),
            "stage":stage,
        })
        total_count+=1

# Construir mensaje Telegram
now=datetime.now().strftime("%d-%b %H:%M")
if total_count==0:
    msg=f"✅ *Barredora horaria* {now}\n\nSin reclamos abiertos en las 6 cuentas. Todo tranquilo."
else:
    msg=f"📊 *Barredora horaria* {now}\n*{total_count} reclamos abiertos*\n\n"
    # Agrupar por cuenta
    by_account={}
    for c in all_claims:
        by_account.setdefault(c["account"],[]).append(c)
    
    for acc,claims_list in by_account.items():
        msg+=f"━━━━━━━━━━━━━━━━━\n🏪 *{acc}* ({len(claims_list)})\n\n"
        for c in claims_list:
            msg+=f"📦 {c['product']}\n"
            msg+=f"  • Venta: `{c['order_id']}`\n"
            msg+=f"  • Reclamo: `{c['claim_id']}` ({c['stage']})\n"
            msg+=f"  • Motivo: {c['reason_label']}\n\n"

# Telegram message limit ~4096 chars
if len(msg)>4000:
    msg=msg[:3950]+"\n\n_(mensaje truncado)_"

rp=requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
    json={"chat_id":TG_CHAT,"text":msg,"parse_mode":"Markdown","disable_web_page_preview":True})
print(f"telegram: {rp.status_code}")
print(f"total claims: {total_count}")
