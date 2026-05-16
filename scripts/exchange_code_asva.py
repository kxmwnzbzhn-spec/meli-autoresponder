import os,requests,json
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
CODE="TG-6a087e152e62f700016abb6b-1668713481"
r=requests.post("https://api.mercadolibre.com/oauth/token",data={
    "grant_type":"authorization_code","client_id":CID,"client_secret":CS,
    "code":CODE,"redirect_uri":"https://oauth.pstmn.io/v1/callback"
})
print("http=",r.status_code)
print(json.dumps(r.json(),indent=2))
