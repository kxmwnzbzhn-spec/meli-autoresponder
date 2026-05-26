import os, requests, json
import meli_token
CID="5512970703"; API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
# detalle previo
d0=requests.get(f"{API}/post-purchase/v1/claims/{CID}",headers=H,timeout=20).json()
print(f"CLAIM {CID} status={d0.get('status')} type={d0.get('type')} reason={d0.get('reason_id')}")
print("seller_actions:",[a.get("action") for p in (d0.get('players') or []) if p.get('role')=='respondent' for a in (p.get('available_actions') or [])])
# variantes endpoint (stop al primer 2xx)
attempts=[
 ("POST","/post-purchase/v1/claims/{c}/refund", None),
 ("POST","/post-purchase/v1/claims/{c}/transactions/refund", None),
 ("POST","/post-purchase/v1/claims/{c}/actions", {"action":"refund"}),
 ("POST","/post-purchase/v1/claims/{c}/players/respondent/actions", {"action":"refund"}),
 ("POST","/post-purchase/v1/claims/{c}/expected_resolutions", {"type":"refund"}),
 ("POST","/post-purchase/v1/claims/{c}/resolutions", {"type":"refund"}),
 ("POST","/post-purchase/v1/claims/{c}/returns", {"type":"refund"}),
 ("PUT","/post-purchase/v1/claims/{c}", {"resolution":{"type":"refund"}}),
 ("PUT","/post-purchase/v1/claims/{c}", {"action":"refund"}),
]
success=None
for method,path,body in attempts:
    url=f"{API}{path.format(c=CID)}"
    fn=requests.post if method=="POST" else requests.put
    r=fn(url,headers=HJ,json=body,timeout=25) if body is not None else fn(url,headers=H,timeout=25)
    print(f"  {method} {path.format(c=CID)[:60]:60} body={json.dumps(body) if body else '-':30} -> {r.status_code} {r.text[:140]}")
    if r.status_code<300:
        success=(method,path,body); break
print("\nSUCCESS:", success)
# verificar estado post
d1=requests.get(f"{API}/post-purchase/v1/claims/{CID}",headers=H,timeout=15).json()
print(f"POST status={d1.get('status')} stage={d1.get('stage')} resolution={d1.get('resolution')}")
print("DONE")
