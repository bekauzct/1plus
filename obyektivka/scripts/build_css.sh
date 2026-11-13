#!/usr/bin/env bash
# Tailwind CSS'ni standalone CLI bilan yig'adi (Node shart emas).
#   ./scripts/build_css.sh          — bir marta, minify bilan
#   ./scripts/build_css.sh --watch  — o'zgarishlarni kuzatib
set -euo pipefail
cd "$(dirname "$0")/.."
VERSION="${TAILWIND_VERSION:-v3.4.17}"
BIN="bin/tailwindcss"
if [ ! -x "$BIN" ]; then
  case "$(uname -s)-$(uname -m)" in
    Linux-x86_64) ASSET=tailwindcss-linux-x64 ;;
    Linux-aarch64) ASSET=tailwindcss-linux-arm64 ;;
    Darwin-arm64) ASSET=tailwindcss-macos-arm64 ;;
    Darwin-x86_64) ASSET=tailwindcss-macos-x64 ;;
    *) echo "Noma'lum platforma: $(uname -s)-$(uname -m)"; exit 1 ;;
  esac
  mkdir -p bin
  curl -sSfL -o "$BIN" "https://github.com/tailwindlabs/tailwindcss/releases/download/${VERSION}/${ASSET}"
  chmod +x "$BIN"
fi
if [ "${1:-}" = "--watch" ]; then
  exec "$BIN" -c tailwind.config.js -i static/css/src/app.css -o static/css/app.css --watch
fi
"$BIN" -c tailwind.config.js -i static/css/src/app.css -o static/css/app.css --minify
