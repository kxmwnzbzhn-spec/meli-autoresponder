import os, requests
import meli_token
IDS="5291774150,5291785036,5363034838,2940662359,5390372034,2940047221,2909183147,5390371996,2950790163,2950801625,5364336572,2950790181,2950801553,2950839697,2940664057,2950827405,2950839631,5374101788,5363034842,2916942827,2950827407,2950790159,5364336602".split(",")
ids=["MLM"+i for i in IDS]
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_YC_NEW"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
res={}
for i in range(0,len(ids),20):
    chunk=ids[i:i+20]
    r=requests.get("https://api.mercadolibre.com/items?ids="+",".join(chunk)+"&attributes=id,title,status,price",headers=H,timeout=30).json()
    for it in r:
        b=it.get("body",{})
        if b.get("id"): res[b["id"]]={"t":b.get("title"),"s":b.get("status"),"p":b.get("price")}
        else: res[it.get("id","?")]={"t":None,"s":"ERR"+str(it.get('code')),"p":None}
print("ID\tSTATUS\tPRECIO\tTITULO")
for i in ids:
    d=res.get(i,{"t":"(no encontrado)","s":"?","p":None})
    print(f"{i}\t{d['s']}\t{d['p']}\t{d['t']}")
print("DONE")
