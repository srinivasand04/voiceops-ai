#!/usr/bin/env bash
# One-time setup for a fresh Ubuntu 22.04/24.04 server (run as root or with sudo):
#   curl -fsSL https://raw.githubusercontent.com/srinivasand04/voiceops-ai/main/deploy/server-setup.sh | sudo DOMAIN=calls.example.com bash
# Re-running it later updates the app to the latest main branch.
set -euo pipefail

: "${DOMAIN:?Set DOMAIN, e.g. DOMAIN=calls.example.com}"
REPO="${REPO:-https://github.com/srinivasand04/voiceops-ai.git}"
APP_DIR="${APP_DIR:-/opt/voiceops}"

# Docker
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sh
fi

# Swap: Whisper + pyannote need ~4 GB RAM, swap prevents out-of-memory kills.
if [ ! -f /swapfile ]; then
  fallocate -l 4G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# Code
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull --ff-only
else
  git clone "$REPO" "$APP_DIR"
fi
cd "$APP_DIR"

# Secrets are generated once and kept in .env (never committed).
if [ ! -f .env ]; then
  cat > .env <<EOF
POSTGRES_DB=voiceops
POSTGRES_USER=voiceops_user
POSTGRES_PASSWORD=$(openssl rand -hex 16)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
JWT_SECRET=$(openssl rand -hex 32)
DOMAIN=${DOMAIN}
# Paste your Hugging Face token here once (needed to download the pyannote model)
HF_TOKEN=
# Optional: enables Claude-written summaries
ANTHROPIC_API_KEY=
EOF
  chmod 600 .env
  echo ">> Created $APP_DIR/.env - add HF_TOKEN to it, then run this script again."
fi

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo ">> Deployed. Open https://${DOMAIN} (DNS A record must point to this server)."
