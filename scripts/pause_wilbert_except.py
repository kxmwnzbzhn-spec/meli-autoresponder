import os, requests, json
import meli_token
API="https://api.mercadolibre.com"
# probar Yiriam (15 abiertos), Raymundo (3) y Wilbert
for ACC,UID in [("YC_NEW",3364413125),("WILBERT",3367276814),("RAYMUNDO",3338633403)]:
    AT=meli_token.refresh(os.environ[f"MELI_REFRESH_TOKEN_{ACC}"]).json()["access_token"]
    H={"Authorization":f"Bearer {AT}"}
    s=requests.get(f"{API}/post-purchase/v1/claims/search",params={"stage":"claim","status":"opened","players.role":"respondent","players.user_id":UID,"limit":1},headers=H,timeout=20).json()
    res=s.get("data") or s.get("results") or []
    if not res: print(f"\n=== {ACC} (uid {UID}): 0 claims abiertos"); continue
    cid=res[0].get("id")
    d=requests.get(f"{API}/post-purchase/v2/claims/{cid}",headers=H,timeout=20).json()
    print(f"\n=== {ACC} claim_id={cid} ===")
    print("status:",d.get("status"),"| stage:",d.get("stage"),"| reason_id:",d.get("reason_id"),"| type:",d.get("type"))
    print("players:", [(p.get('role'),p.get('user_id'),p.get('available_actions')) for p in (d.get('players') or [])])
    print("resource:",d.get("resource"),d.get("resource_id"))
    print("available_actions (top):", json.dumps(d.get("available_actions"),ensure_ascii=False)[:500] if d.get("available_actions") else None)
    print("resolution:", d.get("resolution"))
print("DONE")
