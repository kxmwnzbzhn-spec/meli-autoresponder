import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]; RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]; print(f"=== {me.get('nickname')} ({uid}) ===\n")

# 1) Claims endpoint con varios filtros
print("--- /post-purchase/v1/claims/search ---")
for st in ["opened","in_process","closed","with_refund"]:
    try:
        c=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search?status={st}&limit=5",headers=H,timeout=15).json()
        if isinstance(c,dict):
            print(f"  status={st}: total={c.get('paging',{}).get('total','?')}, items={len(c.get('data') or [])}")
            for cl in (c.get('data') or [])[:2]:
                print(f"    {json.dumps(cl,ensure_ascii=False)[:400]}")
    except Exception as e:
        print(f"  status={st}: ERR {e}")

# 2) Sample order con mediations
print("\n--- Probing orders with mediations ---")
o=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.status=paid&limit=50",headers=H,timeout=20).json()
with_med=[]
for ord in o.get("results",[]):
    meds=ord.get("mediations") or []
    if meds:
        with_med.append(ord)
        if len(with_med)<=3:
            print(f"\nOrder {ord.get('id')} mediations:")
            print(f"  status={ord.get('status')} total=${ord.get('total_amount'):,.2f}")
            print(f"  mediations array (count={len(meds)}):")
            for m in meds:
                print(f"    {json.dumps(m,ensure_ascii=False)[:300]}")

print(f"\nTotal orders sample 50 with mediations: {len(with_med)}")

# 3) Claims con detalle de status y fechas
print("\n--- Listando claims con detalles ---")
all_claims=requests.get("https://api.mercadolibre.com/post-purchase/v1/claims/search?limit=20",headers=H,timeout=20).json()
if isinstance(all_claims,dict):
    print(f"Total claims (sin filtro): {all_claims.get('paging',{}).get('total','?')}")
    by_st={}
    for cl in (all_claims.get('data') or []):
        st=cl.get('status','?')
        by_st[st]=by_st.get(st,0)+1
    print(f"Status breakdown (sample 20): {by_st}")
