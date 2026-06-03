"""Send message to all paid+not_shipped buyers of MLM2967318097 (Claribel)."""
import os, requests, json, time
API="https://api.mercadolibre.com"
SBU=os.environ.get("SUPABASE_URL","").rstrip("/")
SBK=os.environ.get("SUPABASE_SERVICE_KEY","")
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=minimal"} if SBK else None

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_CLARIBEL={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
SELLER=me["id"]; print(f"seller={SELLER}")

ITEM="MLM2967318097"

# Get all orders again with fresh data
import datetime as dt
since=(dt.datetime.utcnow()-dt.timedelta(days=60)).strftime("%Y-%m-%dT00:00:00.000Z")
orders=[]; offset=0
while offset<5000:
    params={"seller":SELLER,"item":ITEM,"order.date_created.from":since,
            "limit":50,"offset":offset,"sort":"date_desc"}
    rr=requests.get(f"{API}/orders/search",headers=H,params=params,timeout=20).json()
    res=rr.get("results") or []
    orders.extend(res)
    if len(res)<50: break
    offset+=50
print(f"Total orders: {len(orders)}")

MSG = ("Hola, te escribimos de la tienda. "
       "Lamentablemente tuvimos una sobreventa del modelo Bose SoundLink Home en color Negro "
       "y no contamos con stock para despacharte la pieza en ese color. "
       "Como solución inmediata, tenemos disponibilidad del mismo modelo en color Gris Plata, "
       "totalmente nuevo, sellado y al mismo precio. "
       "¿Te interesaría que te enviemos la pieza en Gris Plata en lugar de Negro? "
       "Si prefieres, también podemos procesar el reembolso completo de tu compra en este momento, sin trámites. "
       "Quedamos atentos a tu respuesta. Mil disculpas por la molestia.")

# Filter: status=paid AND shipping not in shipped/delivered/handling
SKIP_SHIP={"shipped","delivered","not_delivered","returned","not_specified"}
targets=[]
skipped=[]
for o in orders:
    if o.get("status")!="paid": continue
    items=o.get("order_items") or []
    if not any((i.get("item") or {}).get("id")==ITEM for i in items): continue
    sh=o.get("shipping") or {}
    sh_status=(sh.get("status") or "").lower()
    sh_substatus=(sh.get("substatus") or "").lower()
    if sh_status in SKIP_SHIP and sh_status not in ("","pending","handling","ready_to_ship","to_be_agreed"):
        skipped.append((o.get("id"),sh_status,sh_substatus))
        continue
    buyer=o.get("buyer") or {}
    pack=o.get("pack_id") or o.get("id")
    targets.append({
        "order_id":o.get("id"),
        "pack_id":pack,
        "buyer_id":buyer.get("id"),
        "buyer_nick":buyer.get("nickname"),
        "sh_status":sh_status,
        "sh_substatus":sh_substatus,
    })

print(f"\nTargets to message: {len(targets)}")
print(f"Skipped (already shipped/delivered): {len(skipped)}")
for s in skipped: print(f"  skip {s}")

# Send
ok=0; fail=0; errs=[]
for t in targets:
    pack=t["pack_id"]; buyer=t["buyer_id"]; order=t["order_id"]
    if not buyer or not pack:
        fail+=1; errs.append((order,"missing buyer/pack")); continue
    url=f"{API}/messages/packs/{pack}/sellers/{SELLER}?tag=post_sale"
    body={
        "from":{"user_id":SELLER},
        "to":{"user_id":buyer},
        "text":MSG,
    }
    try:
        rm=requests.post(url,headers=HJ,json=body,timeout=15)
    except Exception as e:
        fail+=1; errs.append((order,f"EXC {e}")); continue
    if rm.status_code in (200,201):
        ok+=1
        print(f"  ✅ order={order} buyer={t['buyer_nick']} pack={pack}")
        if SBH:
            requests.post(f"{SBU}/rest/v1/meli_actions_log",
                headers={**SBH,"Content-Type":"application/json","Prefer":"return=minimal"},
                json={"account":"CLARIBEL","item_id":ITEM,"action_type":"buyer_message_sent",
                      "from_value":f"order={order}","to_value":f"buyer={buyer}",
                      "actor":"claude_cowork",
                      "details":"oferta de cambio a gris plata por sobreventa"},timeout=8)
    else:
        fail+=1
        errs.append((order,rm.status_code,rm.text[:300]))
        print(f"  ❌ order={order} buyer={buyer} HTTP {rm.status_code}: {rm.text[:300]}")
    time.sleep(0.4)

print(f"\n=== SUMMARY ===")
print(f"  Total candidates (paid + with item): {len(orders)} → after filter targets={len(targets)}")
print(f"  ✅ sent: {ok}")
print(f"  ❌ failed: {fail}")
if errs:
    print(f"  First errors:")
    for e in errs[:10]: print(f"    {e}")

# Telegram
TG=os.environ.get("TELEGRAM_BOT_TOKEN",""); CID=os.environ.get("TELEGRAM_CHAT_ID","")
if TG and CID:
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",
        json={"chat_id":CID,"text":f"Claribel oferta gris-plata: {ok} mensajes enviados, {fail} fallaron de {len(targets)} pendientes"},timeout=10)
