"""Create missing development secrets, preserving configured values and SMTP settings."""
from pathlib import Path
import re
import secrets
path = Path(__file__).resolve().parents[1] / '.env'
source = path.read_text() if path.exists() else path.with_name('.env.example').read_text()
original = source if path.exists() else None
for key in ('PG_PASS', 'AUTHENTIK_SECRET_KEY', 'AUTHENTIK_BOOTSTRAP_PASSWORD', 'OIDC_CLIENT_SECRET', 'NEXTAUTH_SECRET'):
    pattern = rf'^{key}=\s*$'
    if re.search(pattern, source, re.MULTILINE):
        source = re.sub(pattern, f'{key}={secrets.token_hex(32)}', source, count=1, flags=re.MULTILINE)
    elif not re.search(rf'^{key}=', source, re.MULTILINE):
        source += f'\n{key}={secrets.token_hex(32)}\n'
if source != original:
    path.write_text(source)
    path.chmod(0o600)
    print('Created missing development secrets in .env.')
