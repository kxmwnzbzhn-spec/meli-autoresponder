import os, requests, json
from datetime import datetime, timezone, timedelta

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
ACCOUNTS=[
    ("JUAN","MELI_REFRESH_TOKEN"),
    ("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA","MELI_REFRESH_TOKEN_ASVA"),
    ("DILCIE","MELI_REFRESH_TOKEN_DILCIE"),
    ("MILDRED","MELI_REFRESH_TOKEN_MILDRED"),
    ("BREN","MELI_REFRESH_TOKEN_BREN"),
    ("WILBERT","MELI_REFRESH_TOKEN_WILBERT"),
    ("YC_NEW","MELI_REFRESH_TOKEN_YC_NEW"),
    ("OFICIAL","MELI_REFRESH_TOKEN_OFICIAL"),
]

cdmx=datetime.now(timezone.utc)-timedelta(hours=6)
since=cdmx-timedelta(days=60)
date_from=since.strftime("%Y-%m-%dT%H:%M:%S.000Z")
print(f"=== NETO ACUMULADO ÚLTIMOS 60 DÍAS — desde {date_from} ===")
print(f"Generado: {cdmx.strftime('%Y-%m-%d %H:%M')} CDMX\n")

results={}
for label,env in ACCOUNTS:
    RT=os.environ.get(env,"")
    if not RT:
        results[label]={"err":"no token"}; continue
    try:
        r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=15).json()
        if "access_token" not in r:
            results[label]={"err":f"refresh fail: {r.get('message','?')}"}; continue
        H={"Authorization":f"Bearer {r['access_token']}"}
        me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
        uid=me["id"]; nick=me.get("nickname","")
    except Exception as e:
        results[label]={"err":f"auth: {e}"}; continue
    
    paid=cancelled=0
    gross=fees=qty=0
    by_day={}
    offset=0
    while True:
        url=f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={date_from}&limit=50&offset={offset}&sort=date_desc"
        rr=requests.get(url,headers=H,timeout=30).json()
        res=rr.get("results",[])
        if not res: break
        for o in res:
            st=o.get("status","")
            if st=="cancelled": cancelled+=1; continue
            if st in ("paid","shipped","delivered"):
                paid+=1
                day=o.get("date_created","")[:10]
                g_o=f_o=q_o=0
                for it in o.get("order_items",[]):
                    q=it.get("quantity",0) or 0
                    up=it.get("unit_price",0) or 0
                    sf=it.get("sale_fee",0) or 0
                    g_o+=up*q; f_o+=sf*q; q_o+=q
                gross+=g_o; fees+=f_o; qty+=q_o
                d=by_day.setdefault(day,{"o":0,"u":0,"g":0,"n":0})
                d["o"]+=1; d["u"]+=q_o; d["g"]+=g_o; d["n"]+=g_o-f_o
        if len(res)<50: break
        offset+=50
        if offset>10000: break  # safety for huge accounts
    
    net=gross-fees
    results[label]={"nick":nick,"uid":uid,"paid":paid,"cancelled":cancelled,"qty":qty,"gross":gross,"fees":fees,"net":net,"by_day":by_day}

# Print summary table
print(f"{'CUENTA':<10} {'NICK':<24} {'ÓRD':>4} {'CANC':>5} {'UN':>4} {'BRUTO':>14} {'COMIS':>12} {'NETO':>14}")
print("-"*100)
tot=dict(o=0,c=0,q=0,g=0,f=0,n=0)
for label,_ in ACCOUNTS:
    r=results.get(label,{})
    if "err" in r:
        print(f"{label:<10} {'(' + r['err'] + ')':<70}")
        continue
    print(f"{label:<10} {r['nick'][:24]:<24} {r['paid']:>4} {r['cancelled']:>5} {r['qty']:>4} ${r['gross']:>13,.2f} ${r['fees']:>11,.2f} ${r['net']:>13,.2f}")
    tot["o"]+=r["paid"]; tot["c"]+=r["cancelled"]; tot["q"]+=r["qty"]
    tot["g"]+=r["gross"]; tot["f"]+=r["fees"]; tot["n"]+=r["net"]
print("-"*100)
print(f"{'TOTAL':<10} {'':<24} {tot['o']:>4} {tot['c']:>5} {tot['q']:>4} ${tot['g']:>13,.2f} ${tot['f']:>11,.2f} ${tot['n']:>13,.2f}")

# JSON dump for parsing
print("\n=== JSON ===")
out={k: ({**v, "by_day": dict(sorted(v.get("by_day",{}).items()))} if "err" not in v else v) for k,v in results.items()}
print(json.dumps(out, ensure_ascii=False))
