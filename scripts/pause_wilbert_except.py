import os, requests, json
import meli_token
CID="5512970703"; API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
d=requests.get(f"{API}/post-purchase/v1/claims/{CID}",headers=H,timeout=20).json()
order_id=d.get("resource_id"); print(f"order_id={order_id}")
# GET probes para descubrir sub-recursos
print("\n--- GET probes ---")
for path in [f"/post-purchase/v1/claims/{CID}/expected_resolutions",
             f"/post-purchase/v1/claims/{CID}/resolutions",
             f"/post-purchase/v1/claims/{CID}/returns",
             f"/post-purchase/v1/claims/{CID}/refunds",
             f"/post-purchase/v1/claims/{CID}/orders",
             f"/orders/{order_id}/refunds",
             f"/post-purchase/v1/orders/{order_id}/refunds",
             f"/post-purchase/v1/orders/{order_id}/refund_status"]:
    r=requests.get(f"{API}{path}",headers=H,timeout=15)
    print(f"  GET {path[:62]:62} -> {r.status_code} {r.text[:120]}")
# POST probes con bodies ricos
print("\n--- POST probes ---")
bodies=[
 ("/post-purchase/v1/claims/{c}/expected_resolutions", {"type":"refund","player_role":"respondent"}),
 ("/post-purchase/v1/claims/{c}/expected_resolutions", {"type":"refund","player_role":"respondent","reason_id":d.get("reason_id")}),
 ("/post-purchase/v1/claims/{c}/expected_resolutions", {"expected_resolution":{"type":"refund"}}),
 ("/post-purchase/v1/orders/{o}/refunds", {"reason":"claim","amount":None}),
 ("/orders/{o}/refunds", {}),
 ("/v1/refunds", {"order_id":int(order_id) if order_id else 0}),
 ("/post-purchase/v1/claims/{c}/responses", {"action":"refund"}),
 ("/post-purchase/v1/claims/{c}/respondent_resolutions", {"type":"refund"}),
]
for path,body in bodies:
    url=f"{API}{path.format(c=CID,o=order_id)}"
    r=requests.post(url,headers=HJ,json=body,timeout=25)
    print(f"  POST {path[:55]:55} body={json.dumps(body)[:50]:50} -> {r.status_code} {r.text[:120]}")
    if r.status_code<300: print("  *** SUCCESS ***"); break
print("DONE")
