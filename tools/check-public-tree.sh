#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
bad=0
git ls-files | while IFS= read -r path; do
  case "$path" in
    ports/triples/assets/fonts/Inter-Bold.ttf|ports/triples/assets/fonts/Jua-Regular.ttf) ;;
    *.apk|*.xapk|*.ppm|*.zip|*.7z|*.so|*.dat|*.sav|*.png|*.jpg|*.jpeg|*/userdata/*|*/prefs/*|*/assets/*|.local/*)
      echo "Private or binary file staged: $path" >&2; exit 1;;
  esac
  [ -f "$path" ] || continue
  size=$(wc -c < "$path")
  case "$path" in
    ports/triples/assets/fonts/Inter-Bold.ttf)
      [ "$(shasum -a 256 "$path" | cut -d ' ' -f 1)" = 288316099b1e0a47a4716d159098005eef7c0066921f34e3200393dbdb01947f ] || exit 1
      continue;;
    ports/triples/assets/fonts/Jua-Regular.ttf)
      [ "$(shasum -a 256 "$path" | cut -d ' ' -f 1)" = a1ad0976608d0dd6d298cb01de8431f20e9416b330dd8f58cb0e5f88cee39985 ] || exit 1
      continue;;
  esac
  if [ "$size" -gt 1048576 ]; then echo "File over 1 MiB: $path" >&2; exit 1; fi
done || bad=1
if git grep -nIE '(/Users/|/Volumes/|192\.168\.[0-9]+\.[0-9]+|(password|passwd|token|secret)[[:space:]]*[:=])' -- ':!tools/check-public-tree.sh' >/dev/null; then
  echo 'Potential local path, network address or secret in tracked text:' >&2
  git grep -nIE '(/Users/|/Volumes/|192\.168\.[0-9]+\.[0-9]+|(password|passwd|token|secret)[[:space:]]*[:=])' -- ':!tools/check-public-tree.sh' >&2
  bad=1
fi
[ "$bad" -eq 0 ]
