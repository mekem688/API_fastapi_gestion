#!/bin/bash
# Démarre l'application de bureau SIGE.DESKTOP
echo "=== SIGE.DESKTOP — Démarrage ==="

if [ ! -d ".venv" ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installation des dépendances..."
pip install -r requirements.txt -q

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Fichier .env créé à partir de .env.example — modifiez API_URL si besoin."
fi

echo "Lancement de l'application..."
python -m app.main
