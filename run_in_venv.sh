#!/usr/bin/env bash
# Wrapper to run VideoAgent inside the project's virtualenv
set -euo pipefail
cd "$(dirname "$0")"

# Load environment variables from common locations so scheduled runs
# can pick up secrets (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, etc.).
# Priority: project .env then OpenClaw env file.
if [ -f .env ]; then
  # shellcheck disable=SC1091
  set -a
  # shellcheck disable=SC1090
  source .env
  set +a
fi

OPENCLAW_ENV="$HOME/.openclaw/telegram.env"
if [ -f "$OPENCLAW_ENV" ]; then
  # shellcheck disable=SC1091
  set -a
  # shellcheck disable=SC1090
  source "$OPENCLAW_ENV"
  set +a
fi

# Activate venv if present
if [ -f venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

# Debug mode: either pass first arg 'debug' or '--debug', or set DEBUG=1 in env
DEBUG=0
if [ "${1:-}" = "debug" ] || [ "${1:-}" = "--debug" ] || [ "${DEBUG:-}" = "1" ]; then
  DEBUG=1
fi

export PYTHONUNBUFFERED=1
if [ "$DEBUG" -eq 1 ]; then
  echo "🔎 Running in debug mode — printing output to terminal"
  # Run the project entrypoint and print output to terminal
  python run.py
else
  # Run the project entrypoint and log output
  python run.py >> /tmp/videoagent_cron.log 2>&1
fi
