from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from app import main

client = TestClient(main.app)
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

@pytest.fixture(autouse=True)
def local_signing_key(monkeypatch):
    monkeypatch.setattr(main.jwks, 'get_signing_key_from_jwt', lambda token: SimpleNamespace(key=private_key.public_key()))


def access_token(**overrides):
    now = datetime.now(timezone.utc)
    claims = dict(iss=main.ISSUER, aud=main.AUDIENCE, sub='user-123', iat=now, exp=now + timedelta(minutes=10), scope='openid email profile sample_user', email='ada@example.test', given_name='Ada', family_name='Lovelace', created_at='2026-10-01T10:00:00Z')
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm='RS256', headers={'kid': 'test'})


def request(token):
    return client.get('/api/user', headers={'Authorization': 'Bearer ' + token})


def test_authenticated_user():
    response = request(access_token())
    assert response.status_code == 200
    assert response.json() == dict(sub='user-123', email='ada@example.test', first_name='Ada', last_name='Lovelace', created_at='2026-10-01T10:00:00Z')


def test_anonymous_rejected():
    assert client.get('/api/user').status_code == 401


@pytest.mark.parametrize('overrides', [dict(aud='other-app'), dict(iss='https://attacker.test'), dict(exp=datetime.now(timezone.utc)-timedelta(seconds=1))])
def test_invalid_claims_rejected(overrides):
    assert request(access_token(**overrides)).status_code == 401


def test_wrong_signature_rejected():
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    claims = jwt.decode(access_token(), options={'verify_signature': False})
    assert request(jwt.encode(claims, other_key, algorithm='RS256')).status_code == 401


def test_missing_scope_rejected():
    assert request(access_token(scope='openid email')).status_code == 403


def test_unsigned_rejected():
    claims = jwt.decode(access_token(), options={'verify_signature': False})
    assert request(jwt.encode(claims, key='', algorithm='none')).status_code == 401


def test_missing_expiry_rejected():
    claims = jwt.decode(access_token(), options={'verify_signature': False})
    del claims['exp']
    assert request(jwt.encode(claims, private_key, algorithm='RS256')).status_code == 401


def test_unavailable_jwks(monkeypatch):
    def unavailable(token):
        raise jwt.PyJWKClientConnectionError('unavailable')
    monkeypatch.setattr(main.jwks, 'get_signing_key_from_jwt', unavailable)
    assert request(access_token()).status_code == 503
