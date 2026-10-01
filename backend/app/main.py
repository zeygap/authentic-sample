import os
from datetime import datetime
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

ISSUER = os.getenv("OIDC_ISSUER", "http://localhost:9000/application/o/sample/")
AUDIENCE = os.getenv("OIDC_AUDIENCE", "sample-frontend")
jwks = jwt.PyJWKClient(os.getenv("OIDC_JWKS_URL", "http://localhost:9000/application/o/sample/jwks/"), timeout=5)
app = FastAPI(title="authentik token demo")
app.add_middleware(CORSMiddleware, allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")], allow_methods=["GET"], allow_headers=["Authorization"])
bearer = HTTPBearer(auto_error=False)

class UserInfo(BaseModel):
    sub: str
    email: str
    first_name: str
    last_name: str
    created_at: datetime


def authenticated_claims(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> dict:
    if credentials is None:
        raise HTTPException(401, "Bearer token required", headers={"WWW-Authenticate": "Bearer"})
    try:
        key = jwks.get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(credentials.credentials, key.key, algorithms=["RS256"], issuer=ISSUER, audience=AUDIENCE, options={"require": ["exp", "iat", "iss", "aud", "sub"]})
        if "sample_user" not in claims.get("scope", "").split():
            raise HTTPException(403, "sample_user scope required")
        return claims
    except jwt.PyJWKClientConnectionError as exc:
        raise HTTPException(503, "Identity provider temporarily unavailable") from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(401, "Invalid or expired access token", headers={"WWW-Authenticate": "Bearer error=invalid_token"}) from exc


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/user", response_model=UserInfo)
def get_user(claims: Annotated[dict, Depends(authenticated_claims)]):
    # These attributes are signed by authentik's custom OIDC scope mapping.
    try:
        return UserInfo(sub=claims["sub"], email=claims["email"], first_name=claims["given_name"], last_name=claims["family_name"], created_at=claims["created_at"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(403, "Required user claims missing") from exc
