"""Apply current config on every start, so edits do not wait for the worker's scan."""
import subprocess
result = subprocess.run(
    ['docker', 'compose', 'exec', '-T', 'authentik-server', 'ak', 'apply_blueprint', '/blueprints/custom/sample.yaml'],
    capture_output=True, text=True,
)
if result.returncode:
    print((result.stdout + result.stderr)[-6000:])
    raise SystemExit(result.returncode)
print('Applied authentik blueprint.')
