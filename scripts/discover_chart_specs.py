"""Discover chart spec for MLM-UNDERPANTS and try creating a custom chart."""
import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

# 1) Try chart template endpoint variants
for ep in [
    "/domains/MLM-UNDERPANTS/specs?spec=charts_template",
    "/catalog_charts/domains/MLM-UNDERPANTS/template",
    "/catalog_charts/discover?domain_id=MLM-UNDERPANTS&site_id=MLM",
    "/sites/MLM/domains/MLM-UNDERPANTS/charts/template",
    "/catalog_charts/template?domain_id=MLM-UNDERPANTS",
    "/charts/domains/MLM-UNDERPANTS",
]:
    print(f"\n=== GET {ep} ===")
    rr=requests.get(f"{API}{ep}",headers=H,timeout=15)
    print(f"HTTP {rr.status_code}: {rr.text[:600]}")

# 2) Try /catalog_charts discover (most common public endpoint)
print(f"\n=== GET /catalog_charts ===")
rr=requests.get(f"{API}/catalog_charts",headers=H,timeout=15,
  params={"site_id":"MLM","domain_id":"MLM-UNDERPANTS","attributes":"BRAND:23136,GENDER:339665,MODEL:4767895"})
print(f"HTTP {rr.status_code}: {rr.text[:1500]}")

# 3) Discovery via items search — find an existing item with chart and read its SIZE_GRID_ID
print(f"\n=== Search existing CK Brief items with grid ===")
sr=requests.get(f"{API}/sites/MLM/search?q=calvin klein brief microfibra&category=MLM194115&limit=10",headers=H,timeout=15).json()
for r in (sr.get("results") or [])[:10]:
    iid=r.get("id"); ttl=(r.get("title") or "")[:60]
    g=requests.get(f"{API}/items/{iid}?attributes=id,title,attributes,variations",headers=H,timeout=10).json()
    sgi=next((a.get("value_id") for a in (g.get("attributes") or []) if a.get("id")=="SIZE_GRID_ID"),None)
    print(f"  {iid} | {ttl} | SIZE_GRID_ID={sgi}")
    if sgi:
        # Inspect the chart
        ch=requests.get(f"{API}/charts/{sgi}",headers=H,timeout=10)
        print(f"    [CHART {sgi}] HTTP {ch.status_code}")
        if ch.status_code==200:
            cd=ch.json()
            print(json.dumps({k:cd.get(k) for k in ("id","domain_id","site_id","names","type","attributes")}, indent=2)[:1500])
            rows=cd.get("rows") or []
            print(f"    rows={len(rows)}")
            for rr2 in rows[:6]:
                attrs={a.get('id'):(a.get('values') or [{}])[0].get('name') for a in (rr2.get('attributes') or [])}
                print(f"      row_id={rr2.get('id')} | {attrs}")
            break
