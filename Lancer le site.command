#!/bin/zsh
# Lance le serveur local de lemagcroisieres.fr et ouvre le site dans Safari.
# Double-cliquez sur ce fichier depuis le Finder. Laissez la fenêtre ouverte.
# Pour arrêter le serveur : Ctrl+C, ou fermez simplement la fenêtre.

cd "$(dirname "$0")" || exit 1

PORT=4873

# Si le port est déjà occupé (ancien serveur resté en arrière-plan), on le libère.
if lsof -ti:$PORT >/dev/null 2>&1; then
  echo "Un serveur occupait déjà le port $PORT — on le remplace."
  lsof -ti:$PORT | xargs kill 2>/dev/null
  sleep 1
fi

echo "Dossier servi : $(pwd)"
echo "Adresse       : http://localhost:$PORT/"
echo ""
echo "Laissez cette fenêtre ouverte pendant que vous consultez le site."
echo "Ctrl+C pour arrêter."
echo ""

# Ouvre Safari une fois le serveur prêt.
( sleep 1.5; open -a Safari "http://localhost:$PORT/" ) &

python3 -m http.server $PORT
