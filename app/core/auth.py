from functools import lru_cache
from typing import Optional
from jose import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
import os

security = HTTPBearer()

@lru_cache
def get_settings():
    return {
        "domain": os.getenv("AUTH0_DOMAIN"),
        "audience": os.getenv("AUTH0_API_AUDIENCE"),
        "algorithms": [os.getenv("AUTH0_ALGORITHMS", "RS256")]
    }

def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return credentials.credentials

def verify_token(token: str = Depends(get_token)):
    settings = get_settings()
    jwks_url = f"https://{settings['domain']}/.well-known/jwks.json"
    jwks = requests.get(jwks_url).json()
    unverified_header = jwt.get_unverified_header(token)
    rsa_key: Optional[dict] = None
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
            break
    if rsa_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_header")
    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=settings["algorithms"],
            audience=settings["audience"],
            issuer=f"https://{settings['domain']}/"
        )
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token")
    return payload
