"""Final chart endpoint attempts + reopen 3 items as fallback."""
import os, requests, json, time
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me.get("id")

# Endpoint hunt for chart create
chart_payload={
    "names":{"main_title":"Calvin Klein Boxers Hombre"},
    "domain_id":"MLM-UNDERPANTS",
    "site_id":"MLM",
    "type":"specific",
    "attributes":[{"id":"BRAND","values":[{"name":"Calvin Klein"}]},{"id":"GENDER","values":[{"name":"Hombre"}]}],
    "rows":[
        {"attributes":[{"id":"SIZE","values":[{"name":"S"}]},{"id":"WAIST_CIRCUMFERENCE","values":[{"name":"71-76 cm"}]}]},
        {"attributes":[{"id":"SIZE","values":[{"name":"M"}]},{"id":"WAIST_CIRCUMFERENCE","values":[{"name":"81-86 cm"}]}]},
        {"attributes":[{"id":"SIZE","values":[{"name":"L"}]},{"id":"WAIST_CIRCUMFERENCE","values":[{"name":"91-97 cm"}]}]}
    ]
}
chart_id=None
for ep in [
    "/catalog_charts/charts",
    "/catalog_charts/MLM/MLM-UNDERPANTS/charts",
    "/catalog_charts/MLM/charts",
    f"/users/{uid}/catalog_charts",
    "/measure_unit",  # unrelated, just to see
]:
    rr=requests.post(f"{API}{ep}",headers=HJ,json=chart_payload,timeout=15)
    print(f"  POST {ep} → HTTP {rr.status_code}: {rr.text[:300]}")
    if rr.status_code in (200,201):
        chart_id=(rr.json().get("id") or rr.json().get("chart_id"))
        print(f"  ✅ CHART CREATED {chart_id}")
        break

# Also GET endpoints to see what's there
for ep in [
    "/catalog_charts/charts",
    f"/users/{uid}/catalog_charts",
    "/sites/MLM/catalog_charts",
]:
    rr=requests.get(f"{API}{ep}",headers=H,timeout=10)
    print(f"  GET  {ep} → HTTP {rr.status_code}: {rr.text[:300]}")

print(f"\nchart_id={chart_id}")

# === If no chart, REOPEN the 3 items ===
if not chart_id:
    print("\n[FALLBACK] no chart available — REOPEN the 3 separate items")
    for iid in ["MLM5444637526","MLM5444848314","MLM5444797814"]:
        rp=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"active"},timeout=15)
        print(f"  {iid} reopen → HTTP {rp.status_code}: {rp.text[:200]}")
        time.sleep(0.5)
