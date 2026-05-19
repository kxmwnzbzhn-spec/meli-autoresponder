#!/usr/bin/env python3
"""Localiza MLM5233454100 (paused → no público) probando cada cuenta."""
import os, requests, re
API="https://api.mercadolibre.com"

ACCOUNTS={
  "YIRIAM": os.environ.get("MELI_REFRESH_TOKEN_YC_NEW"),
  "WILBERT": os.environ.get("MELI_REFRESH_TOKEN_WILBERT"),
  "RAYMUNDO": os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
  "JUAN": os.environ.get("MELI_REFRESH_TOKEN_JUAN"),
  "CLARIBEL": os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
  "ASVA": os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
  "DILCIE": os.environ.get("MELI_REFRESH_TOKEN_DILCIE"),
  "BREN": os.environ.get("MELI_REFRESH_TOKEN_BREN"),
  "MILDRED": os.environ.get("MELI_REFRESH_TOKEN_MILDRED"),
  "MG20260424": os.environ.get("MELI_REFRESH_TOKEN_MG20260424"),
}
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]

def tok(rt):
    if not rt: return None
    try:
        return requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt},timeout=15).json().get("access_token")
    except: return None

target_id="MLM5233454100"
owner=None
title=None
for name,rt in ACCOUNTS.items():
    T=tok(rt)
    if not T: continue
    H={"Authorization":f"Bearer {T}"}
    g=requests.get(f"{API}/items/{target_id}",headers=H,timeout=10).json()
    if g.get("id")==target_id:
        owner=name
        title=g.get("title")
        print(f"OWNER: {name} | status={g.get('status')} sub={g.get('sub_status')} qty={g.get('available_quantity')} price={g.get('price')}")
        print(f"  title='{title}'")
        print(f"  seller_id={g.get('seller_id')}")
        print(f"  variations={len(g.get('variations') or [])}")
        # Listar attributes para entender color
        for a in g.get("attributes") or []:
            if "color" in (a.get("id") or "").lower() or "color" in (a.get("name") or "").lower():
                print(f"  attr {a.get('id')}={a.get('value_name')}")
        break

if not owner:
    print("NO OWNER ENCONTRADO. ¿Quizás es de otra cuenta?")
    raise SystemExit(0)

# Buscar hermanas en la misma cuenta
T=tok(ACCOUNTS[owner])
H={"Authorization":f"Bearer {T}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me.get("id")

print(f"\n--- BUSCANDO HERMANAS en {owner} (uid={uid}) ---")
matches=[]
for st in ("active","paused"):
    offset=0
    while True:
        r=requests.get(f"{API}/users/{uid}/items/search?status={st}&limit=50&offset={offset}",headers=H,timeout=15).json()
        ids=r.get("results") or []
        if not ids: break
        # Multi-get
        chunks=[ids[i:i+20] for i in range(0,len(ids),20)]
        for ch in chunks:
            mg=requests.get(f"{API}/items?ids={','.join(ch)}",headers=H,timeout=15).json()
            for ent in mg:
                b=ent.get("body") or {}
                t=(b.get("title") or "").lower()
                # Match flexible: bocina + ip67 (o impermeable) + 35w
                if "bocina" in t and ("ip67" in t or "impermeable" in t) and "35w" in t:
                    color="?"
                    for c in ("Azul","Roja","Rojo","Negro","Negra","Morado","Morada"):
                        if c.lower() in t:
                            color=c; break
                    matches.append({
                        "id": b.get("id"),
                        "title": b.get("title"),
                        "price": b.get("price"),
                        "sold": b.get("sold_quantity",0),
                        "status": b.get("status"),
                        "qty": b.get("available_quantity"),
                        "color": color,
                        "cpid": b.get("catalog_product_id"),
                    })
        if len(ids)<50: break
        offset+=50
        if offset>500: break

print(f"\n=== {len(matches)} hermanas encontradas ===")
for m in sorted(matches, key=lambda x: -x.get("sold",0)):
    print(f"  {m['id']:<14} {m['status']:<8} color={m['color']:<6} sold={m['sold']:<3} qty={m['qty']:<3} ${m['price']}  cpid={m['cpid']}  '{m['title'][:55]}'")
