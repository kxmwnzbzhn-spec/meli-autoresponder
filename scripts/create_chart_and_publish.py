"""Create custom size chart for boxers (S/M/L), then publish item with chart_id."""
import os, requests, json, sys
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me.get("id")
print(f"seller={uid}")

# ========== STEP 1: Discover an existing item with chart to learn the schema ==========
print("\n=== Search published items in MLM194115 with SIZE_GRID_ID ===")
seed_chart_id=None
sr=requests.get(f"{API}/sites/MLM/search",headers=H,timeout=15,
                params={"q":"calvin klein boxer microfibra","category":"MLM194115","limit":15}).json()
for it in (sr.get("results") or [])[:15]:
    iid=it.get("id")
    g=requests.get(f"{API}/items/{iid}?attributes=id,title,attributes",headers=H,timeout=10).json()
    sgi=next((a.get("value_id") for a in (g.get("attributes") or []) if a.get("id")=="SIZE_GRID_ID"),None)
    if sgi:
        print(f"  found {iid} | {g.get('title')[:55]} | SIZE_GRID_ID={sgi}")
        seed_chart_id=sgi
        # Inspect chart
        c=requests.get(f"{API}/catalog_charts/{sgi}",headers=H,timeout=10)
        print(f"  GET /catalog_charts/{sgi}: HTTP {c.status_code}: {c.text[:1500]}")
        if c.status_code==200:
            cd=c.json()
            rows=cd.get("rows") or []
            print(f"  rows={len(rows)}")
            for rr2 in rows[:6]:
                attrs={a.get('id'):(a.get('values') or [{}])[0].get('name') for a in (rr2.get('attributes') or [])}
                print(f"    row_id={rr2.get('id')} attrs={attrs}")
        break

# ========== STEP 2: Try creating custom chart ==========
print("\n=== POST /catalog_charts (create custom) ===")
chart_payload={
    "names": {"main_title": "Calvin Klein Boxers Hombre - Tallas"},
    "domain_id": "MLM-UNDERPANTS",
    "site_id": "MLM",
    "type": "specific",
    "attributes": [
        {"id": "BRAND", "values": [{"name": "Calvin Klein"}]},
        {"id": "MODEL", "values": [{"name": "Brief"}]},
        {"id": "GENDER", "values": [{"name": "Hombre"}]}
    ],
    "rows": [
        {"attributes": [
            {"id":"SIZE","values":[{"name":"S"}]},
            {"id":"WAIST_CIRCUMFERENCE","values":[{"name":"71 a 76 cm"}]},
            {"id":"HIP_CIRCUMFERENCE","values":[{"name":"86 a 91 cm"}]}
        ]},
        {"attributes": [
            {"id":"SIZE","values":[{"name":"M"}]},
            {"id":"WAIST_CIRCUMFERENCE","values":[{"name":"81 a 86 cm"}]},
            {"id":"HIP_CIRCUMFERENCE","values":[{"name":"94 a 99 cm"}]}
        ]},
        {"attributes": [
            {"id":"SIZE","values":[{"name":"L"}]},
            {"id":"WAIST_CIRCUMFERENCE","values":[{"name":"91 a 97 cm"}]},
            {"id":"HIP_CIRCUMFERENCE","values":[{"name":"102 a 107 cm"}]}
        ]}
    ]
}
cr=requests.post(f"{API}/catalog_charts",headers=HJ,json=chart_payload,timeout=20)
print(f"HTTP {cr.status_code}: {cr.text[:2500]}")

chart_id=None
if cr.status_code in (200,201):
    chart_id=cr.json().get("id")
    print(f"\n✅ CHART CREATED chart_id={chart_id}")
    # Fetch rows
    ch=requests.get(f"{API}/catalog_charts/{chart_id}",headers=H,timeout=10).json()
    print(f"\nChart rows:")
    for rr in (ch.get("rows") or []):
        ats={a.get('id'):(a.get('values') or [{}])[0].get('name') for a in (rr.get('attributes') or [])}
        print(f"  row_id={rr.get('id')} {ats}")
elif seed_chart_id:
    print(f"\n[FALLBACK] use seed_chart_id={seed_chart_id} (de un competidor)")
    chart_id=seed_chart_id

if not chart_id:
    print("\n[STOP] no chart_id disponible — no se puede publicar con variantes")
    sys.exit(1)
