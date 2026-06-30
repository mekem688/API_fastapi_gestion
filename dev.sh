#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  dev.sh — Lancement complet du projet (Backend + Frontend)
#
#  Usage :
#    ./dev.sh              → lance API + interface (mode dev)
#    ./dev.sh --migrate    → applique les migrations avant le lancement
#    ./dev.sh --help       → affiche l'aide
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# ─── Couleurs ────────────────────────────────────────────────
VERT="\033[0;32m"  ROUGE="\033[0;31m"
JAUNE="\033[0;33m" BLEU="\033[0;34m"
CYAN="\033[0;36m"  GRIS="\033[0;90m"
RESET="\033[0m"    BOLD="\033[1m"

ok()   { echo -e "${VERT}✔ $*${RESET}"; }
err()  { echo -e "${ROUGE}✘ $*${RESET}" >&2; exit 1; }
info() { echo -e "${BLEU}➜ $*${RESET}"; }
warn() { echo -e "${JAUNE}⚠ $*${RESET}"; }
sep()  { echo -e "${GRIS}────────────────────────────────────────${RESET}"; }

# ─── Arguments ───────────────────────────────────────────────
MIGRATE=false
for arg in "$@"; do
  case "$arg" in
    --migrate) MIGRATE=true ;;
    --help|-h)
      echo ""
      echo -e "${BOLD}dev.sh${RESET} — Lance le backend FastAPI et le frontend React en parallèle"
      echo ""
      echo "  ${BOLD}Usage :${RESET}  ./dev.sh [options]"
      echo ""
      echo "  Options :"
      echo "    --migrate    Applique les migrations Alembic avant le lancement"
      echo "    --help       Affiche cette aide"
      echo ""
      echo "  Accès :"
      echo "    API            →  http://localhost:8000"
      echo "    Documentation  →  http://localhost:8000/docs"
      echo "    Interface       →  http://localhost:5173"
      echo ""
      echo "  Prérequis : Python 3, pip, Node.js / npm (ou pnpm)"
      echo ""
      exit 0
      ;;
    *) warn "Argument inconnu : '$arg'" ;;
  esac
done

# ─── Bannière ────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${BLEU}"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║   MSTECH Gestion — Lancement développement  ║"
echo "  ║   Backend : FastAPI    Frontend : React      ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${RESET}"

# ─── Chargement du .env ──────────────────────────────────────
if [ -f ".env" ]; then
  info "Chargement de .env…"
  set -a; source .env; set +a
  ok "Variables d'environnement chargées."
else
  warn "Pas de fichier .env trouvé. Copiez .env.example vers .env"
  warn "  cp .env.example .env  puis remplissez DATABASE_URL et SECRET_KEY"
fi

# ─── Vérification DATABASE_URL ───────────────────────────────
if [ -z "${DATABASE_URL:-}" ]; then
  err "DATABASE_URL non définie. Remplissez votre fichier .env."
fi

# ─── Migrations (optionnel) ──────────────────────────────────
if [ "$MIGRATE" = true ]; then
  sep
  info "Application des migrations Alembic…"
  command -v alembic &>/dev/null || err "alembic introuvable. Installez : pip install -r requirements.txt"
  alembic upgrade head
  ok "Migrations appliquées."
fi

sep
echo ""

# ─── Fonction : préfixe couleur dans les logs ────────────────
prefix_log() {
  local label="$1" color="$2"
  while IFS= read -r line; do
    echo -e "${color}[${label}]${RESET} $line"
  done
}

# ─── Détection du gestionnaire de paquets Node.js ────────────
detect_node_pm() {
  if command -v pnpm &>/dev/null; then echo "pnpm"
  elif command -v npm &>/dev/null; then echo "npm"
  elif command -v yarn &>/dev/null; then echo "yarn"
  else echo ""
  fi
}

# ─── Vérification Python ─────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  err "Python 3 introuvable."
fi

# ─── Vérification Node.js ────────────────────────────────────
NODE_PM=$(detect_node_pm)
if [ -z "$NODE_PM" ]; then
  err "npm / pnpm / yarn introuvable. Installez Node.js."
fi

# ─── Installation des dépendances Python (si besoin) ─────────
if ! python3 -c "import fastapi" &>/dev/null 2>&1; then
  info "Installation des dépendances Python…"
  pip install -r requirements.txt -q
  ok "Dépendances Python installées."
fi

# ─── Installation des dépendances Node (si besoin) ───────────
if [ ! -d "frontend/node_modules" ]; then
  info "Installation des dépendances Node.js (frontend/)…"
  (cd frontend && $NODE_PM install --silent)
  ok "Dépendances Node installées."
fi

# ─── Choix de l'exécuteur uvicorn ────────────────────────────
if command -v uvicorn &>/dev/null; then
  UVICORN="uvicorn"
else
  UVICORN="python3 -m uvicorn"
fi

# ─── Affichage des URLs ───────────────────────────────────────
echo -e "  ${CYAN}${BOLD}API FastAPI${RESET}    →  http://localhost:${API_PORT:-8000}"
echo -e "  ${CYAN}${BOLD}Docs Swagger${RESET}   →  http://localhost:${API_PORT:-8000}/docs"
echo -e "  ${CYAN}${BOLD}Interface React${RESET} →  http://localhost:5173"
echo ""
sep
echo -e "  ${GRIS}Ctrl+C pour tout arrêter${RESET}"
sep
echo ""

# ─── Lancement du backend ─────────────────────────────────────
$UVICORN src.app:app \
  --host "${HOST:-0.0.0.0}" \
  --port "${API_PORT:-8000}" \
  --reload \
  --log-level info 2>&1 | prefix_log "API" "${VERT}" &
API_PID=$!

sleep 1  # Laisse l'API démarrer avant le frontend

# ─── Lancement du frontend ───────────────────────────────────
(cd frontend && $NODE_PM run dev 2>&1) | prefix_log "WEB" "${CYAN}" &
WEB_PID=$!

# ─── Gestion de l'arrêt propre (Ctrl+C) ──────────────────────
cleanup() {
  echo ""
  info "Arrêt en cours…"
  kill "$API_PID" 2>/dev/null || true
  kill "$WEB_PID" 2>/dev/null || true
  wait "$API_PID" 2>/dev/null || true
  wait "$WEB_PID" 2>/dev/null || true
  ok "Tout est arrêté. À bientôt !"
  exit 0
}
trap cleanup SIGINT SIGTERM

# ─── Attente (boucle principale) ─────────────────────────────
wait
