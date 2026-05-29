import os, requests
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_ASVA={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}

# Already-published (skipped in last run) + newly published = full Alchemia universe in ASVA
IDS=[
 # Newly published 2026-05-29
 "MLM2967772739","MLM2967805695","MLM2967785553","MLM2967805717","MLM2967772751",
 "MLM2967785571","MLM2967772767","MLM2967805739","MLM2967772777","MLM2967805753",
 "MLM2967805759","MLM2967772787","MLM2967759903","MLM2967759907","MLM2967805775",
 "MLM2967759915","MLM2967772809","MLM2967772817","MLM2967772829","MLM2967805809",
 "MLM2967759935","MLM2967785655","MLM2967785667",
 # Already published (skipped)
 "MLM2378074941","MLM3849137034","MLM2378087893","MLM2954229423","MLM2945250605",
 "MLM5374718702","MLM2945214721","MLM2598943053","MLM2594259115","MLM2594259089",
 "MLM2592601259","MLM2592360377","MLM2592715459","MLM2592715389","MLM2592360231",
 "MLM2592664137","MLM4436268412","MLM2592715211","MLM5374722276","MLM2592360045",
 "MLM4436177528","MLM2592740671","MLM2594564705",
]
rows=[]
for i in range(0,len(IDS),20):
    batch=",".join(IDS[i:i+20])
    r=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,title,status,sub_status,price,available_quantity,sold_quantity,permalink"},timeout=20).json()
    for x in r:
        if x.get("code")==200:
            b=x["body"]
            rows.append((b["id"],b.get("title",""),b.get("status"),b.get("sub_status"),b.get("price"),b.get("available_quantity"),b.get("sold_quantity"),b.get("permalink")))

# Sort by title for easy reading
rows.sort(key=lambda r: r[1].lower())
print(f"\nTotal Alchemia listings in ASVA: {len(rows)}")
print(f"\n{'='*120}")
for mlm,title,st,ss,pr,qty,sold,url in rows:
    flag="✅" if st=="active" else ("⏸" if st=="paused" else "❓")
    print(f"\n{flag} {mlm} | {st} | ${pr} | qty={qty} sold={sold}")
    print(f"  {title[:90]}")
    print(f"  {url}")
