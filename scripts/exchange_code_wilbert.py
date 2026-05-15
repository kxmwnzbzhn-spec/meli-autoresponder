import os,requests,json
CID=os.environ["MELI_APP_ID"]
CS=os.environ["MELI_APP_SECRET"]
CODE="TG-6a0682491470520001433e88-3367276814"
REDIRECT="https://oauth.pstmn.io/v1/callback"
r=requests.post("https://api.mercadolibre.com/oauth/token",data={
    "grant_type":"authorization_code",
    "client_id":CID,
    "client_secret":CS,
    "code":CODE,
    "redirect_uri":REDIRECT
})
print("http=",r.status_code)
print(json.dumps(r.json(),indent=2))
