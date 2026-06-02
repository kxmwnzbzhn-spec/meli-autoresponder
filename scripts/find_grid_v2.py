"""Aggressive search for SIZE_GRID_ID from existing MLM194115 items."""
import os, requests, json, time
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

# Strategy: use /sites/MLM/search with category filter; try without category, also try domain.
# Also try Adrián's own paused items, and trending category items
queries=[
    {"category":"MLM194115","limit":50,"sort":"sold_quantity_desc"},
    {"q":"boxer hombre calvin klein","limit":50},
    {"q":"calzoncillo paquete","limit":30},
    {"q":"underwear hanes","category":"MLM194115","limit":30},
]
found_charts=set()
for params in queries:
    try:
        sr=requests.get(f"{API}/sites/MLM/search",headers=H,timeout=20,params=params).json()
    except Exception as e:
        print(f"SEARCH err {e}"); continue
    results=sr.get("results") or []
    print(f"\n[Q {params}] got {len(results)} results")
    for it in results[:30]:
        iid=it.get("id")
        try:
            g=requests.get(f"{API}/items/{iid}?attributes=id,category_id,attributes",headers=H,timeout=8).json()
        except: continue
        if g.get("category_id")!="MLM194115": continue
        attrs={a.get("id"):a.get("value_id") for a in (g.get("attributes") or [])}
        sgi=attrs.get("SIZE_GRID_ID")
        if sgi and sgi not in found_charts:
            found_charts.add(sgi)
            print(f"  ✅ {iid} → SIZE_GRID_ID={sgi}")
            # Get chart details
            c=requests.get(f"{API}/catalog_charts/{sgi}",headers=H,timeout=8)
            if c.status_code==200:
                cd=c.json()
                print(f"     names={cd.get('names')} domain={cd.get('domain_id')} type={cd.get('type')}")
                rows=cd.get("rows") or []
                print(f"     rows={len(rows)}")
                for rr in rows[:8]:
                    rats={a.get('id'):(a.get('values') or [{}])[0].get('name') for a in (rr.get('attributes') or [])}
                    print(f"       row_id={rr.get('id')} {rats}")
            else:
                print(f"     chart GET HTTP {c.status_code}: {c.text[:200]}")
    if len(found_charts)>=5: break

print(f"\n=== Found {len(found_charts)} unique chart_ids ===")
for c in found_charts: print(f"  {c}")

# Also: try Adrián's own listings — maybe he has clothing items already with a chart
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me["id"]
print(f"\n=== Adrián own items in MLM194115 ===")
si=requests.get(f"{API}/users/{uid}/items/search?category=MLM194115&limit=20",headers=H,timeout=15).json()
own_ids=si.get("results") or []
print(f"  total in MLM194115: {len(own_ids)}")
for iid in own_ids[:5]:
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=8).json()
    sgi=next((a.get("value_id") for a in (g.get("attributes") or []) if a.get("id")=="SIZE_GRID_ID"),None)
    print(f"  {iid} | SIZE_GRID_ID={sgi}")
