import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
ITEMS=["MLM5291774150","MLM5291785036","MLM2940047221","MLM5363034834","MLM5363034838","MLM2940047227","MLM5363034842","MLM5363023018","MLM2940047233","MLM5363147396","MLM5363023022","MLM5363147400","MLM5363034850","MLM5363023026","MLM5363034852","MLM5363147404","MLM2940047245","MLM5363147408","MLM5363023032","MLM5363147410","MLM5363034856","MLM5363147416","MLM2940047249","MLM5363147422","MLM5363034860"]
counts={"active":0,"paused":0,"under_review":0,"closed":0,"other":0}
for iid in ITEMS:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=status,sub_status,price,available_quantity",headers=H).json()
    st=g.get("status","?")
    counts[st]=counts.get(st,0)+1
    if st!="active":
        print(f"  ⚠ {iid} st={st} sub={g.get('sub_status')} qty={g.get('available_quantity')}")
print(f"\nTotals: {counts}")
