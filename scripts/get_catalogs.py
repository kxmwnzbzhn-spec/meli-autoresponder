import os, requests, time, json
import meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
Q=[
("Lattafa set 5 pzs","Lattafa set 5 piezas perfume"),("Lattafa Fakhar set 3","Lattafa Fakhar set"),
("Lattafa Fakhar","Lattafa Fakhar"),("Lattafa Mayar Intense","Lattafa Mayar Intense"),
("Lattafa Mayar Cherry","Lattafa Mayar Cherry Intense"),("Lattafa Sehr","Lattafa Sehar"),
("Lattafa Haya","Lattafa Haya"),("Lattafa Khamrah Dukhan","Lattafa Khamrah Dukhan"),
("Orientica dorado","Orientica Royal Amber"),("Orientica rojo","Orientica Amber Rouge"),
("Al Haramain dorado","Al Haramain Amber Oud Gold Edition"),("Al Haramain negro","Al Haramain Amber Oud Carbon"),
("Al Haramain morado","Al Haramain Amber Oud Ruby"),("Al Haramain café","Al Haramain Amber Oud Exclusif"),
("Al Haramain rojo","Al Haramain Amber Oud Ruby Edition"),("Bharara Beirut","Bharara Beirut"),
("Oud Al Layla","Oud Al Layla Maison Alhambra"),("MFK kurky","Maison Francis Kurkdjian 724"),
("MFK Baccarat 540","Baccarat Rouge 540"),("Shaik Sapphire","Shaik Opulent Sapphire 33"),
("VS Pure Seduction","Victoria Secret Pure Seduction"),("VS Bare Vanilla","Victoria Secret Bare Vanilla"),
("JPG dorado","Jean Paul Gaultier Le Male Elixir"),("JPG negro","Jean Paul Gaultier Ultra Male"),
("JPG flores","Jean Paul Gaultier La Belle"),("Dubai chocolate","Dubai Chocolate perfume"),
("Gucci floral","Gucci Flora Gorgeous"),("Jo Malone","Jo Malone London"),
("Lattafa Confession","Lattafa Confession Her"),("D&G Light Blue","Dolce Gabbana Light Blue"),
("D&G Devotion Men","Dolce Gabbana Devotion hombre"),("D&G Pour Homme","Dolce Gabbana Pour Homme"),
("D&G Velvet Tender Oud","Dolce Gabbana Velvet Tender Oud"),("Dior Bonne Etoile","Dior Bonne Etoile"),
("Dior Sauvage Elixir","Dior Sauvage Elixir"),("Dior Jadore","Dior Jadore"),
("Dior Sauvage sin alcohol","Dior Sauvage Parfum sans alcool"),("Dior Sakura","Dior Sakura"),
("Dior Sauvage","Dior Sauvage EDT"),("Dior Dune","Dior Dune"),
("Miss Dior Blooming","Miss Dior Blooming Bouquet"),("Dior EDP","Miss Dior Eau de Parfum"),
("Azzaro Most Wanted","Azzaro The Most Wanted"),("Armaf Odyssey Wild","Armaf Odyssey wild one"),
("Armaf Odyssey Candee","Armaf Odyssey Candee"),("Armaf Spectra","Armaf Spectra"),
("Armaf Lion's Club Rugir","Armaf Lions Club Rugir"),("Armaf Lion's Club Feroce","Armaf Lions Club Feroce"),
("Game of Spade Wildcard","Jo Milano Game of Spade Wildcard"),("Le Labo Santal 33","Le Labo Santal 33"),
("Tom Ford Black Orchid","Tom Ford Black Orchid"),("Tom Ford Bois Pacifique","Tom Ford Bois Pacifique"),
("Creed Aventus","Creed Aventus"),("Creed Silver Mountain","Creed Silver Mountain Water"),
("Creed Himalaya","Creed Himalaya"),("Byredo Mojave Ghost","Byredo Mojave Ghost"),
("Byredo Rose No Mans Land","Byredo Rose of no mans land"),("Cartier Panthere","Cartier La Panthere"),
("Initio negro","Initio Oud for Greatness"),("EA Stronger Tobacco","Emporio Armani Stronger With You Tobacco"),
("EA Stronger","Emporio Armani Stronger With You"),("EA Stronger Sandalwood","Emporio Armani Stronger With You Sandalwood"),
("GA Si Passione","Giorgio Armani Si Passione"),("GA Oud Royal Prive","Armani Prive Oud Royal"),
("GA My Way","Giorgio Armani My Way"),("GA Code","Giorgio Armani Code"),
("Club de Nuit Iconic","Armaf Club de Nuit Iconic"),("Club de Nuit Milestone","Armaf Club de Nuit Milestone"),
("Club de Nuit Maleka","Armaf Club de Nuit Maleka"),("Spicebomb dark","Spicebomb Viktor Rolf"),
("Spicebomb Extreme","Spicebomb Extreme Viktor Rolf"),("Dumont Nitro Red","Dumont Nitro Red"),
("Dumont Nitro Green","Dumont Nitro Green"),("YSL Mon Paris","Yves Saint Laurent Mon Paris"),
("YSL Libre","Yves Saint Laurent Libre"),("Penhaligons Lady Blanche","Penhaligon Lady Blanche"),
("Amouage Outlands","Amouage Interlude"),("Marshmallow Blush","Marshmallow Blush perfume"),
("Marc Jacobs Daisy","Marc Jacobs Daisy"),("Marc Jacobs Perfect","Marc Jacobs Perfect"),
("Marc Jacobs Perfect Elixir","Marc Jacobs Perfect Elixir"),("PR 1M Parfum","Paco Rabanne One Million Parfum"),
("PR 1M Gold","Paco Rabanne 1 Million"),("PR 1M Royal","Paco Rabanne One Million Royal"),
("PR Lady Million","Paco Rabanne Lady Million"),("Kilian Dont Be Shy","By Kilian Love Dont Be Shy"),
("Allegoria Rose Amira","Maison Alhambra Allegoria Rose"),("Allegoria Patchouli Ardent","Allegoria Patchouli Ardent"),
("Allegoria Cuir Intense","Allegoria Cuir Intense"),("Valentino set 4","Valentino set 4 piezas"),
("Billie Eilish","Billie Eilish Eilish perfume"),("Parfums de Marly Oriana","Parfums de Marly Oriana"),
("Mugler Angel Nova","Mugler Angel Nova"),
]
print("LABEL\tCPID\tNOMBRE\tBUYBOX\tOFERTAS\tVENDIDOS_BB\tLINK")
for label,q in Q:
    try:
        s=requests.get(f"{API}/products/search",params={"site_id":"MLM","status":"active","q":q},headers=H,timeout=20).json()
        res=s.get("results") or []
        if not res:
            print(f"{label}\t-\t(sin catalogo)\t-\t0\t-\t-"); time.sleep(0.2); continue
        top=res[0]; cp=top.get("id"); name=top.get("name")
        it=requests.get(f"{API}/products/{cp}/items",headers=H,timeout=20).json()
        offers=it.get("results") or []
        prices=[o.get("price") for o in offers if o.get("price")]
        bb=min(prices) if prices else "?"
        sold="?"
        if offers:
            best=min(offers,key=lambda o:o.get("price") or 9e9)
            iid=best.get("item_id")
            if iid:
                d=requests.get(f"{API}/items/{iid}?attributes=sold_quantity",headers=H,timeout=15).json()
                sold=d.get("sold_quantity")
        print(f"{label}\t{cp}\t{(name or '')[:45]}\t{bb}\t{len(offers)}\t{sold}\thttps://www.mercadolibre.com.mx/p/{cp}")
    except Exception as e:
        print(f"{label}\tERR\t{type(e).__name__}\t-\t-\t-\t-")
    time.sleep(0.2)
print("DONE")
