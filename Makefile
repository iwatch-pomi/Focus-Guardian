.PHONY: setup backend frontend dev docker-dev test

# ── セットアップ ──────────────────────────────────────────
setup:
	@echo "==> Backend setup"
	cd backend && python -m venv .venv && \
	  .venv/bin/pip install -q -e ".[dev]"
	@echo "==> Frontend setup"
	cd frontend && npm install
	@echo "==> .env 作成"
	@[ -f backend/.env ] || cp backend/.env.example backend/.env
	@[ -f frontend/.env.local ] || cp frontend/.env.local.example frontend/.env.local
	@mkdir -p data
	@echo ""
	@echo "✅ セットアップ完了。backend/.env に ANTHROPIC_API_KEY を設定してください。"

# ── 個別起動 ──────────────────────────────────────────────
backend:
	cd backend && .venv/bin/uvicorn api.main:app --reload --host 127.0.0.1 --port 8000

frontend:
	cd frontend && npm run dev

# ── 同時起動（tmux不要・バックグラウンド） ───────────────
dev:
	@mkdir -p data
	@echo "==> Backend を起動中 (port 8000)..."
	cd backend && .venv/bin/uvicorn api.main:app --reload --host 127.0.0.1 --port 8000 &
	@sleep 2
	@echo "==> Frontend を起動中 (port 3000)..."
	cd frontend && npm run dev

# ── Docker Compose ────────────────────────────────────────
docker-dev:
	docker compose up --build

# ── テスト ───────────────────────────────────────────────
test:
	cd backend && .venv/bin/pytest tests/ -v
