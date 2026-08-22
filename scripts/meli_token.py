"""
Autoridad central de tokens MELI.

Las 7 cuentas gestionadas por el Worker (WILBERT, YC_NEW, JUAN, RAYMUNDO,
CLARIBEL, ASVA, BREN) obtienen su access_token EXCLUSIVAMENTE del endpoint del
Worker. NINGUN script de GitHub vuelve a refrescar refresh_token de esas cuentas
(la rotacion la hace solo el Worker).

Cuentas NO gestionadas por el Worker (p.ej. ANGEL, ASGARI, RMAYCHI, AH, MC,
DILCIE, MILDRED) hacen refresh local — el Worker no las rota, asi que no hay
conflicto de rotacion para ellas.

Uso recomendado:
    import meli_token
    at = meli_token.get_access_token("YC_NEW")          # por cuenta
    # o, reemplazo directo de requests.post(.../oauth/token, data={...}):
    resp = meli_token.refresh(<refresh_token_value>)    # devuelve obj tipo dict + .json()
    at = resp["access_token"]
"""
import os
import requests

TOKEN_ENDPOINT = "https://meli-webhook.elite-market-1779161651.workers.dev/token"
TOKEN_SHARED = os.environ.get("TOKEN_SHARED", "")

# Cuentas cuya autoridad de token es el Worker
WORKER_ACCOUNTS = {"WILBERT", "YC_NEW", "JUAN", "RAYMUNDO", "CLARIBEL", "ASVA", "BREN"}

# env var de refresh_token -> cuenta canonica (MAYUS)
ENV_TO_ACCOUNT = {
    "MELI_REFRESH_TOKEN_WILBERT": "WILBERT",
    "MELI_REFRESH_TOKEN_YC_NEW": "YC_NEW",
    "MELI_REFRESH_TOKEN_JUAN": "JUAN",
    "MELI_REFRESH_TOKEN": "JUAN",          # fallback historico = Juan
    "MELI_REFRESH_TOKEN_RAYMUNDO": "RAYMUNDO",
    "MELI_REFRESH_TOKEN_CLARIBEL": "CLARIBEL",
    "MELI_REFRESH_TOKEN_ASVA": "ASVA",
    "MELI_REFRESH_TOKEN_USER1668": "ASVA",   # alias historico de ASVA (user 1668713481)
    "MELI_REFRESH_TOKEN_BREN": "BREN",
}


class TokenResp(dict):
    """Compatibilidad: se comporta como el dict de /oauth/token y ademas
    expone .json()/.status_code/.text para no romper a quienes guardaban
    el objeto Response."""
    status_code = 200
    text = ""

    def json(self):
        return self


def _endpoint_token(account):
    r = requests.get(
        f"{TOKEN_ENDPOINT}/{account}",
        headers={"Authorization": f"Bearer {TOKEN_SHARED}"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def _local_refresh(refresh_token_value):
    r = requests.post(
        "https://api.mercadolibre.com/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": os.environ["MELI_APP_ID"],
            "client_secret": os.environ["MELI_APP_SECRET"],
            "refresh_token": refresh_token_value,
        },
        timeout=20,
    )
    return r.json()


def get_access_token(account):
    """access_token por nombre de cuenta (MAYUS). Worker para las 7; local para el resto."""
    account = (account or "").upper()
    if account in WORKER_ACCOUNTS:
        try:
            return _endpoint_token(account)
        except requests.RequestException:
            # El Worker ya no expone /token/ASVA (404). ASVA E rota su refresh
            # token desde los workflows, por lo que el fallback local es seguro.
            if account == "ASVA":
                j = _local_refresh(os.environ.get("MELI_REFRESH_TOKEN_ASVA", ""))
                return j["access_token"]
            raise
    # cuenta fuera del Worker: refresh local por su env var
    env = next((e for e, a in ENV_TO_ACCOUNT.items() if a == account), f"MELI_REFRESH_TOKEN_{account}")
    j = _local_refresh(os.environ.get(env, ""))
    return j["access_token"]


def _account_for_value(refresh_token_value):
    """Determina la cuenta a partir del VALOR del refresh_token comparando con env."""
    for env, acct in ENV_TO_ACCOUNT.items():
        v = os.environ.get(env)
        if v and v == refresh_token_value:
            return acct
    return None


def refresh(refresh_token_value):
    """Reemplazo directo de requests.post(.../oauth/token, data={...}).
    Devuelve TokenResp (dict + .json()). Usa el Worker si el refresh_token
    pertenece a una de las 7 cuentas; si no, refresh local."""
    acct = _account_for_value(refresh_token_value)
    if acct in WORKER_ACCOUNTS:
        try:
            return TokenResp(access_token=_endpoint_token(acct), refresh_token=refresh_token_value)
        except requests.RequestException:
            if acct == "ASVA":
                return TokenResp(_local_refresh(refresh_token_value))
            raise
    return TokenResp(_local_refresh(refresh_token_value))
