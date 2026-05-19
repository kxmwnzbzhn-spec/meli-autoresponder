#!/usr/bin/env python3
"""Localiza MLM5233454100 + sus 3 hermanas (mismo título, distintos colores)
en la cuenta donde estén. Probar todas las cuentas si hace falta."""
import os, requests
API="https://api.mercadolibre.com"

ACCOUNTS={
  "YIRIAM": os.environ.get("MELI_REFRESH_TOKEN_YC_NEW"),
  "WILBERT": os.environ.get("MELI_REFRESH_TOKEN_WILBERT"),
  "RAYMUNDO": os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
  "JUAN": os.environ.get("MELI_REFRESH_TOKEN_JUAN"),
}
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]

def tok(rt):
    if not rt: return None
    try:
        return requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt},timeout=15).json().get("access_token")
    except: return None

# 1) GET MLM5233454100 público para conocer seller_id + título base
g0=requests.get(f"{API}/items/MLM5233454100",timeout=15).json()
seller_id=g0.get("seller_id")
title=g0.get("title") or ""
print(f"MLM5233454100: seller_id={seller_id} status={g0.get('status')} qty={g0.get('available_quantity')} price={g0.get('price')}")
print(f"  title='{title}'")
# Quitar color del título para buscar hermanas
import re
base=re.sub(r"\s+(Azul|Rojo|Roja|Negro|Negra|Morado|Morada|Verde|Blanco|Blanca)\s*$","",title,flags=re.IGNORECASE)
base=re.sub(r"\s+(Color\s+)?(Azul|Rojo|Roja|Negro|Negra|Morado|Morada|Verde|Blanco|Blanca)\s*$","",base,flags=re.IGNORECASE)
print(f"  base='{base}'")

# 2) Para cada cuenta, listar TODOS items y filtrar por base similar
matches=[]
for name,rt in ACCOUNTS.items():
    T=tok(rt)
    if not T: 
        print(f"\n{name}: sin token")
        continue
    H={"Authorization":f"Bearer {T}"}
    me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
    uid=me.get("id")
    if uid!=seller_id:
        # No es esta cuenta. Pero igual revisamos por si hay clones
        pass
    print(f"\n--- {name} uid={uid} ---")
    for st in ("active","paused"):
        offset=0
        while True:
            r=requests.get(f"{API}/users/{uid}/items/search?status={st}&limit=50&offset={offset}",headers=H,timeout=15).json()
            ids=r.get("results") or []
            if not ids: break
            # Multi-get
            mg=requests.get(f"{API}/items?ids={','.join(ids[:20])}",headers=H,timeout=15).json()
            for ent in mg:
                b=ent.get("body") or {}
                t=b.get("title","")
                # Match: title contains base words
                if "bocina" in t.lower() and ("ip67" in t.lower() or "impermeable" in t.lower()) and "35w" in t.lower():
                    color="?"
                    for c in ("Azul","Roja","Rojo","Negro","Negra","Morado","Morada"):
                        if c.lower() in t.lower():
                            color=c; break
                    matches.append({
                        "id": b.get("id"),
                        "account": name,
                        "uid": uid,
                        "title": t,
                        "price": b.get("price"),
                        "sold": b.get("sold_quantity",0),
                        "status": b.get("status"),
                        "qty": b.get("available_quantity"),
                        "color": color,
                    })
            # Next page
            if len(ids)<50: break
            offset+=50
            if offset>500: break

print(f"\n\n=== MATCHES {len(matches)} ===")
for m in matches:
    print(f"  {m['id']:<14} [{m['account']:<8}] {m['status']:<8} color={m['color']:<6} sold={m['sold']:<3} qty={m['qty']:<3} ${m['price']}  '{m['title'][:50]}'")
