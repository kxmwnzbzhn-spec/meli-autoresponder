import os, requests, json
from datetime import datetime, timezone, timedelta

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]; RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json(); uid=me["id"]

cdmx=datetime.now(timezone.utc)-timedelta(hours=6)
since=cdmx-timedelta(days=60)
date_from=since.strftime("%Y-%m-%dT%H:%M:%S.000Z")

# Pull cancelled
orders=[]; offset=0
while True:
    rr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.status=cancelled&order.date_created.from={date_from}&limit=50&offset={offset}&sort=date_desc",headers=H,timeout=30).json()
    res=rr.get("results",[])
    if not res: break
    orders.extend(res)
    if len(res)<50: break
    offset+=50

print(f"Juan cancelled total: {len(orders)}\n")

# Análisis: cuántos tuvieron payment.status='refunded' con transaction_amount_refunded>0
# y cuántos tuvieron payment con status 'cancelled' o 'rejected' (no es refund real)
stats={"refunded":0,"cancelled_payment":0,"rejected":0,"pending":0,"approved_no_refund":0,"other":0,"no_payments":0}
refund_total=0
sample_refunded=[]
sample_other=[]
for o in orders:
    pays=o.get("payments") or []
    if not pays:
        stats["no_payments"]+=1; continue
    has_refund=False
    for p in pays:
        st=p.get("status","")
        ra=p.get("transaction_amount_refunded",0) or 0
        if st=="refunded" and ra>0:
            has_refund=True
            refund_total+=ra
            stats["refunded"]+=1
            if len(sample_refunded)<3:
                sample_refunded.append({"oid":o.get("id"),"status":o.get("status"),"sd":o.get("status_detail"),"pst":st,"ta":p.get("transaction_amount"),"refunded":ra,"reason":(o.get("cancel_detail") or {}).get("description")})
        elif st in ("cancelled","cancellation"):
            stats["cancelled_payment"]+=1
            if len(sample_other)<3 and st not in [s.get("pst") for s in sample_other]:
                sample_other.append({"oid":o.get("id"),"pst":st,"ta":p.get("transaction_amount"),"refunded":ra,"reason":(o.get("cancel_detail") or {}).get("description")})
        elif st=="rejected":
            stats["rejected"]+=1
            if len(sample_other)<3 and "rejected" not in [s.get("pst") for s in sample_other]:
                sample_other.append({"oid":o.get("id"),"pst":st,"ta":p.get("transaction_amount"),"refunded":ra})
        elif st=="pending":
            stats["pending"]+=1
        elif st=="approved" and ra==0:
            stats["approved_no_refund"]+=1
            if len(sample_other)<3 and "approved" not in [s.get("pst") for s in sample_other]:
                sample_other.append({"oid":o.get("id"),"pst":st,"ta":p.get("transaction_amount"),"refunded":ra,"reason":(o.get("cancel_detail") or {}).get("description")})
        else:
            stats["other"]+=1

print("Status de pagos en órdenes canceladas de Juan:")
for k,v in stats.items():
    print(f"  {k}: {v}")

print(f"\nTotal refund (payment.status=refunded & refunded>0): ${refund_total:,.2f}")

print("\nSample refunded (real refunds):")
for s in sample_refunded:
    print(f"  {s}")

print("\nSample otros estados (NO son refund real):")
for s in sample_other:
    print(f"  {s}")

# Cancel detail / reasons
reasons={}
for o in orders:
    cd=o.get("cancel_detail") or {}
    rsn=cd.get("description") or cd.get("code") or "?"
    reasons[rsn]=reasons.get(rsn,0)+1
print(f"\n=== Motivos de cancelación (top 10) ===")
for r,c in sorted(reasons.items(),key=lambda x:-x[1])[:10]:
    print(f"  {c}x  {r}")
