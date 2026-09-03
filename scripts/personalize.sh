#!/usr/bin/env bash
# Reemplaza el placeholder USERNAME por tu usuario real de GitHub.
#
#   bash scripts/personalize.sh eddieelorza
#
# Opcional: pasa --raw como segundo argumento para convertir las rutas
# relativas de los assets a URLs raw.githubusercontent (util si tu README
# se va a embeber fuera de GitHub, p. ej. en tu portfolio).

set -euo pipefail

USER_NAME="${1:-}"
MODE="${2:-}"

if [[ -z "$USER_NAME" ]]; then
  echo "uso: bash scripts/personalize.sh <tu-usuario-github> [--raw]" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
README="$ROOT/README.md"

# macOS y GNU sed se comportan distinto con -i
sedi() { if sed --version >/dev/null 2>&1; then sed -i "$@"; else sed -i '' "$@"; fi; }

sedi "s|USERNAME|${USER_NAME}|g" "$README"
echo "✓ USERNAME → ${USER_NAME}"

if [[ "$MODE" == "--raw" ]]; then
  RAW="https://raw.githubusercontent.com/${USER_NAME}/${USER_NAME}/main/assets"
  sedi "s|\./assets|${RAW}|g" "$README"
  echo "✓ rutas relativas → ${RAW}"
fi

echo
echo "Siguiente paso:"
echo "  git add -A && git commit -m 'feat: animated profile README' && git push"
