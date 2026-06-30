#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  start.sh — Script de lancement de l'API Gestion de Stock
#
#  Usage :
#    ./start.sh              → lance en mode développement (rechargement auto)
#    ./start.sh prod         → lance en mode production
#    ./start.sh migrate      → applique les migrations puis lance
#    ./start.sh migrate prod → migrations + production
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# ─── Couleurs pour les messages ──────────────────────────────
VERT="\033[0;32m"
ROUGE="\033[0;31m"
JAUNE="\033[0;33m"
BLEU="\033[0;34m"
RESET="\033[0m"

ok()   { echo -e "${VERT}✔ $*${RESET}"; }
err()  { echo -e "${ROUGE}✘ $*${RESET}" >&2; exit 1; }
info() { echo -e "${BLEU}➜ $*${RESET}"; }
warn() { echo -e "${JAUNE}⚠ $*${RESET}"; }

# ─── Bannière ────────────────────────────────────────────────
echo -e "${BLEU}"
echo "  ╔══════════════════════════════════════╗"
echo "  ║   API Gestion de Stock — MSTECH      ║"
echo "  ║   FastAPI + PostgreSQL + Alembic     ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "${RESET}"

# ─── Lecture des arguments ───────────────────────────────────
MODE_PROD=false
APPLIQUER_MIGRATIONS=false

for arg in "$@"; do
  case "$arg" in
    prod)    MODE_PROD=true ;;
    migrate) APPLIQUER_MIGRATIONS=true ;;
    --help|-h)
      echo "Usage : ./start.sh [migrate] [prod]"
      echo ""
      echo "  (aucun argument)   Lance en mode développement (rechargement auto)"
      echo "  migrate            Applique les migrations Alembic avant le lancement"
      echo "  prod               Lance en mode production (sans rechargement auto)"
      echo "  migrate prod       Migrations + mode production"
      exit 0
      ;;
    *)
      warn "Argument inconnu : '$arg' (ignoré). Utilisez --help pour voir les options."
      ;;
  esac
done

# ─── Vérification : Python disponible ────────────────────────
info "Vérification de l'environnement Python..."
if ! command -v python3 &>/dev/null; then
  err "Python 3 introuvable. Installez Python 3.10+ avant de continuer."
fi
PYTHON_VERSION=$(python3 --version 2>&1)
ok "Python trouvé : $PYTHON_VERSION"

# ─── Vérification : uvicorn disponible ───────────────────────
if ! command -v uvicorn &>/dev/null; then
  warn "uvicorn non trouvé dans le PATH. Tentative avec 'python3 -m uvicorn'..."
  UVICORN_CMD="python3 -m uvicorn"
else
  UVICORN_CMD="uvicorn"
  ok "uvicorn trouvé : $(uvicorn --version 2>&1 | head -1)"
fi

# ─── Chargement du fichier .env ──────────────────────────────
ENV_FILE=".env"
if [ -f "$ENV_FILE" ]; then
  info "Chargement des variables depuis $ENV_FILE..."
  set -a
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +a
  ok "Variables d'environnement chargées."
else
  warn "Fichier .env introuvable. Utilisation des variables système."
  warn "Copiez .env.example vers .env et remplissez les valeurs."
fi

# ─── Vérification : DATABASE_URL ─────────────────────────────
if [ -z "${DATABASE_URL:-}" ]; then
  err "La variable DATABASE_URL n'est pas définie.\n  → Créez un fichier .env (voir .env.example) ou exportez DATABASE_URL."
fi
ok "DATABASE_URL défini."

# ─── Vérification : SECRET_KEY ───────────────────────────────
if [ -z "${SECRET_KEY:-}" ]; then
  warn "SECRET_KEY non définie — la valeur par défaut sera utilisée (DÉCONSEILLÉ en production)."
  warn "Générez une clé : python3 -c \"import secrets; print(secrets.token_hex(32))\""
else
  ok "SECRET_KEY définie."
fi

# ─── Migrations Alembic (si demandé) ─────────────────────────
if [ "$APPLIQUER_MIGRATIONS" = true ]; then
  echo ""
  info "Application des migrations Alembic..."
  if ! command -v alembic &>/dev/null; then
    err "alembic introuvable. Installez les dépendances : pip install -r requirements.txt"
  fi

  alembic upgrade head
  ok "Migrations appliquées avec succès."
fi

# ─── Lancement du serveur ────────────────────────────────────
echo ""
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
APP_MODULE="src.app:app"

if [ "$MODE_PROD" = true ]; then
  WORKERS="${WORKERS:-4}"
  info "Lancement en mode PRODUCTION sur http://$HOST:$PORT (workers: $WORKERS)..."
  echo ""
  $UVICORN_CMD "$APP_MODULE" \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --log-level warning \
    --no-access-log
else
  info "Lancement en mode DÉVELOPPEMENT sur http://$HOST:$PORT"
  info "Documentation interactive : http://$HOST:$PORT/docs"
  info "Premier démarrage : POST http://$HOST:$PORT/auth/creer-premier-compte"
  echo ""
  $UVICORN_CMD "$APP_MODULE" \
    --host "$HOST" \
    --port "$PORT" \
    --reload \
    --log-level info
fi
