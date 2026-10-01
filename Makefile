.PHONY: start-dev stop-dev logs test
start-dev:
	@python3 scripts/init_env.py
	docker compose up -d --build --wait --wait-timeout 240
	@python3 scripts/apply_blueprint.py
	@python3 scripts/check_ready.py
	@echo "Frontend: http://localhost:3000 | Mailpit: http://localhost:8025 | API: http://localhost:8000/docs"
stop-dev:
	docker compose down
logs:
	docker compose logs -f --tail=80
test:
	docker compose run --rm backend uv run --frozen --group dev pytest -q
